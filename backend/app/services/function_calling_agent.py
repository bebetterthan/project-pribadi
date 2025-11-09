"""
Function Calling Agent - New Architecture (Production Ready)
Uses Gemini Function Calling API for autonomous tool selection

Enhanced with:
- Retry logic with exponential backoff
- Circuit breaker for fault tolerance
- Structured logging with trace context
- Metrics collection
- Graceful degradation
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.tools.function_toolbox import SECURITY_TOOLS, ToolExecutor
from app.models.scan import Scan, ScanStatus
from app.utils.logger import logger
from app.utils.chat_logger import ChatLogger
from app.utils.json_sanitizer import sanitize_event, test_json_serialization
from app.services.cost_tracker import CostTracker
from app.utils.retry import retry_async, RetryConfig, RetryableError
from app.utils.circuit_breaker import GEMINI_CIRCUIT_BREAKER, CircuitBreakerOpenError
from app.utils.context import get_context, set_scan_id
from app.api.v1.endpoints.metrics import record_api_call, record_error
from app.core.exceptions import AIServiceError, AIQuotaExceededError, AIContentFilterError
from app.config import settings
from datetime import datetime
import json
import asyncio
import time


class FunctionCallingAgent:
    """
    Autonomous agent using Gemini Function Calling
    
    Architecture:
    1. AI receives user objective + available tools
    2. AI decides which tool to call (function call)
    3. Backend executes tool with real target (AI never sees it)
    4. Backend sends sanitized results back to AI
    5. AI analyzes and decides next step
    6. Loop continues until AI calls 'complete_assessment'
    """
    
    def __init__(self, gemini_api_key: str, use_pro_model: bool = False, hybrid_mode: bool = False):
        """
        Initialize agent with dual model support (Fase 2)
        
        Args:
            gemini_api_key: Google AI API key
            use_pro_model: If True and hybrid_mode=False, use Pro model only
            hybrid_mode: If True, initialize both Flash and Pro for dynamic routing
        """
        self.api_key = gemini_api_key
        self.hybrid_mode = hybrid_mode
        genai.configure(api_key=gemini_api_key)
        
        if hybrid_mode:
            # Initialize BOTH models for hybrid routing
            logger.info("🔀 Initializing Hybrid Mode with Flash + Pro models...")
            self.flash_model, self.flash_name = self._init_model('flash')
            self.pro_model, self.pro_name = self._init_model('pro')
            self.current_model = self.flash_model  # Start with Flash
            self.current_model_type = "FLASH"
            logger.info(f"✅ Hybrid Mode ready: Flash ({self.flash_name}) + Pro ({self.pro_name})")
        else:
            # Single model mode (legacy)
            model_type = 'pro' if use_pro_model else 'flash'
            self.model, model_name = self._init_model(model_type)
            self.model_type = "PRO" if use_pro_model else "FLASH"
            self.current_model = self.model
            self.current_model_type = self.model_type
            logger.info(f"🤖 Single Model Mode: {model_name} ({self.model_type})")
        
        # Conversation history (shared across models in hybrid mode)
        self.chat = None
        self.conversation_history = []
        
        # Task tracking for routing decisions
        self.current_task_type = None
        self.iteration_count = 0
        self.tool_call_count = 0
        self.last_action = None
        
    def _init_model(self, model_type: str):
        """
        Initialize a Gemini model with fallback
        
        Args:
            model_type: 'flash' or 'pro'
            
        Returns:
            (model_instance, model_name)
        """
        if model_type == 'flash':
            # Try Gemini 2.5 Flash first, fallback to 1.5
            model_names = ['gemini-2.5-flash', 'gemini-1.5-flash-latest', 'gemini-2.0-flash-exp']
        else:  # pro
            # Try Gemini 2.5 Pro first, fallback to 1.5
            model_names = ['gemini-2.5-pro', 'gemini-1.5-pro-latest']
        
        for model_name in model_names:
            try:
                logger.debug(f"🔧 Attempting to initialize: {model_name}")
                logger.debug(f"   API key length: {len(self.api_key)}")
                logger.debug(f"   Tools count: {len(SECURITY_TOOLS)}")
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    tools=SECURITY_TOOLS,
                    generation_config={
                        'temperature': 0.4 if model_type == 'pro' else 0.3,
                        'top_p': 0.95,
                        'top_k': 40,
                        'max_output_tokens': 8192 if model_type == 'pro' else 4096,
                    }
                )
                logger.info(f"✅ Successfully initialized: {model_name}")
                return model, model_name
            except Exception as e:
                error_msg = str(e) if str(e) else repr(e)
                error_type = type(e).__name__
                logger.warning(f"⚠️ Failed to initialize {model_name}")
                logger.warning(f"   Error type: {error_type}")
                logger.warning(f"   Error message: {error_msg}")
                logger.debug(f"   Full exception:", exc_info=True)
                continue
        
        # If all fail, raise error
        raise Exception(f"❌ Failed to initialize any {model_type} model. Check API key and model availability.")
        
        logger.info(f"🤖 FunctionCallingAgent initialized")
    
    def _determine_task_type(self) -> str:
        """
        Determine current task type based on agent state (Fase 2: Task-Based Routing)
        
        Returns:
            Task type string for routing decision
        """
        # Rule 1: Initial scan (first iteration)
        if self.iteration_count == 0:
            return "initial_scan"
        
        # Rule 2: After first tool execution - strategic analysis needed
        if self.last_action == "tool_execution" and self.tool_call_count == 1:
            return "strategic_decision"
        
        # Rule 3: Multiple tools executed - decide next steps
        if self.tool_call_count > 1 and self.last_action == "tool_execution":
            return "next_step_decision"
        
        # Rule 4: Many iterations or tools - time for final report
        if self.iteration_count > 5 or self.tool_call_count >= 3:
            return "final_report"
        
        # Rule 5: Error occurred - simple error handling
        if self.last_action == "error":
            return "error_handling"
        
        # Rule 6: AI is thinking/analyzing results
        if self.last_action == "thought":
            return "vulnerability_analysis"
        
        # Default: General reasoning (use Pro for safety)
        return "general_reasoning"
    
    def _select_model(self, task_type: str):
        """
        Select appropriate model based on task type (Fase 2: Task-Based Routing)
        
        Args:
            task_type: Type of task to perform
            
        Returns:
            (model_instance, model_type_str, reasoning)
        """
        if not self.hybrid_mode:
            # Hybrid mode disabled, use current model
            return self.current_model, self.current_model_type, "Hybrid mode disabled"
        
        # Task-based routing logic
        routing_rules = {
            "initial_scan": ("flash", "Initial tool selection is straightforward"),
            "data_extraction": ("flash", "Simple parsing task"),
            "error_handling": ("flash", "Error response doesn't need complex reasoning"),
            
            "strategic_decision": ("pro", "Strategic analysis requires complex reasoning"),
            "vulnerability_analysis": ("pro", "Security domain knowledge needed"),
            "next_step_decision": ("pro", "Multi-tool correlation required"),
            "final_report": ("pro", "Synthesis of all findings needed"),
            "general_reasoning": ("pro", "Complex task, use Pro for safety"),
        }
        
        model_choice, reasoning = routing_rules.get(task_type, ("pro", "Unknown task, default to Pro"))
        
        if model_choice == "flash":
            return self.flash_model, "FLASH", reasoning
        else:
            return self.pro_model, "PRO", reasoning
    
    def _switch_model(self, new_model, new_model_type: str):
        """
        Switch active model and prepare context handoff (Fase 2: Context Management)
        
        Args:
            new_model: Model instance to switch to
            new_model_type: "FLASH" or "PRO"
        """
        if self.current_model_type == new_model_type:
            # No switch needed
            return None
        
        old_model_type = self.current_model_type
        self.current_model = new_model
        self.current_model_type = new_model_type
        
        logger.info(f"🔄 Model switch: {old_model_type} → {new_model_type}")
        
        # Prepare context summary for handoff
        context_summary = self._build_context_summary()
        
        return {
            "from_model": old_model_type,
            "to_model": new_model_type,
            "context_summary": context_summary,
            "conversation_length": len(self.conversation_history)
        }
    
    def _build_context_summary(self) -> str:
        """
        Build context summary for model handoff (Fase 2: Context Management)
        
        Returns:
            Concise summary of conversation so far
        """
        if not self.conversation_history:
            return "No previous context"
        
        # Build summary from recent history (last 3-5 messages)
        recent_msgs = self.conversation_history[-5:]
        summary_parts = []
        
        for msg in recent_msgs:
            if msg.get('type') == 'tool_execution':
                tool = msg.get('tool', 'unknown')
                summary_parts.append(f"Executed {tool}")
            elif msg.get('type') == 'thought':
                content = msg.get('content', '')[:100]
                summary_parts.append(f"AI: {content}...")
        
        summary = "[Context: " + " → ".join(summary_parts) + "]"
        return summary if len(summary) < 300 else summary[:297] + "...]"
    
    def _record_api_call(self, response, model_type: str, task_type: str, cost_tracker, response_time: float):
        """
        Record API call cost (Fase 2: Cost Tracking)
        
        Args:
            response: Gemini API response
            model_type: "flash" or "pro"
            task_type: Task type for analytics
            cost_tracker: CostTracker instance
            response_time: Response time in seconds
        """
        try:
            # Extract token usage from response
            # Gemini API provides usage_metadata
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                
                # Record the call
                cost_tracker.record_call(
                    model_type=model_type.lower(),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    task_type=task_type,
                    response_time=response_time
                )
                
                logger.debug(f"💰 API call recorded: {input_tokens}+{output_tokens} tokens, {response_time:.2f}s")
            else:
                logger.warning("⚠️ No usage metadata in response, cannot track cost")
        except Exception as e:
            logger.warning(f"⚠️ Failed to record API call: {e}")
    
    async def run_autonomous_loop(
        self,
        scan: Scan,
        db: Session,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main autonomous loop with function calling
        
        Yields SSE events for streaming to frontend
        
        Args:
            scan: Scan object
            db: Database session
            max_iterations: Max tool calls to prevent infinite loop
        """
        logger.info(f"🚀 Starting autonomous function calling loop for scan {scan.id}")
        logger.info(f"🎯 Target: {scan.target} (hidden from AI)")
        logger.info(f"📝 Objective: {scan.user_prompt}")
        
        # Initialize chat logger
        chat_logger = ChatLogger(scan.id, db)
        
        # FASE 2: Initialize cost tracker
        cost_tracker = CostTracker(scan.id)
        
        # Initialize tool executor (has access to real target)
        tool_executor = ToolExecutor(
            real_target=scan.target,
            scan_id=scan.id,
            db_session=db
        )
        
        # FASE 2: Determine initial task type and select model
        self.iteration_count = 0
        self.tool_call_count = 0
        self.last_action = None
        
        initial_task_type = self._determine_task_type()
        selected_model, model_type, routing_reason = self._select_model(initial_task_type)
        
        # Start conversation with selected model
        self.chat = selected_model.start_chat(enable_automatic_function_calling=False)
        
        # Initial prompt (TARGET-AGNOSTIC!)
        initial_prompt = self._build_initial_prompt(scan.user_prompt)
        
        # Yield initial message
        yield {
            "type": "system",
            "content": f"🤖 AI Agent initialized - Starting autonomous assessment",
            "metadata": {"model": model_type}
        }
        chat_logger.log_system(f"🤖 AI Agent initialized", model=model_type)
        
        # FASE 2: Yield model selection info
        if self.hybrid_mode:
            yield {
                "type": "system_info",
                "subtype": "model_selection",
                "content": f"🤖 Using Gemini {model_type} for: {initial_task_type}",
                "metadata": {
                    "model": model_type,
                    "task_type": initial_task_type,
                    "reasoning": routing_reason
                }
            }
            chat_logger.log_system(f"Model selected: {model_type} for {initial_task_type}", task_type=initial_task_type, model=model_type)
        
        # Only show user objective if it's short (< 200 chars), otherwise skip
        # (AI will include it in its first response anyway)
        if len(scan.user_prompt) < 200:
            yield {
                "type": "thought",
                "content": f"📝 User Objective: {scan.user_prompt}",
                "metadata": {}
            }
            chat_logger.log_thought(f"📝 User Objective: {scan.user_prompt}")
        else:
            # Log for backend only, don't send to frontend
            logger.info(f"📝 User Objective ({len(scan.user_prompt)} chars): {scan.user_prompt[:100]}...")
            chat_logger.log_thought(f"📝 User Objective: {scan.user_prompt[:200]}...")
        
        # Send initial message to AI
        logger.info(f"💬 Sending initial prompt to AI using {model_type}...")
        
        # Yield "AI starting" event for better UX
        yield {
            "type": "thought",
            "content": f"🚀 **Initializing AI Security Assessment**\n\nPreparing attack strategy using **{model_type.upper()}** model...\n\nTarget: `{scan.target}`",
            "metadata": {"phase": "initialization", "model": model_type}
        }
        
        try:
            # FASE 2: Track API call timing and cost
            start_time = time.time()
            response = await asyncio.to_thread(self.chat.send_message, initial_prompt)
            response_time = time.time() - start_time
            
            # Record cost
            self._record_api_call(response, model_type, initial_task_type, cost_tracker, response_time)
            
            logger.info(f"✅ Initial AI response received ({response_time:.2f}s)")
            
            # Check if AI provided initial strategic thinking before tool call
            if response.candidates and response.candidates[0].content.parts:
                first_part = response.candidates[0].content.parts[0]
                if hasattr(first_part, 'text') and first_part.text and not hasattr(first_part, 'function_call'):
                    initial_strategy = first_part.text.strip()
                    if initial_strategy:
                        logger.info(f"📝 AI initial strategy: {initial_strategy[:100]}...")
                        yield {
                            "type": "thought",
                            "content": f"🧠 **AI Initial Strategy:**\n\n{initial_strategy}",
                            "metadata": {"phase": "planning", "model": model_type}
                        }
                        chat_logger.log_thought(f"Initial Strategy: {initial_strategy}")
        except Exception as e:
            error_msg = f"Failed to initialize conversation with AI: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "type": "system",
                "content": f"❌ {error_msg}",
                "metadata": {"error": True}
            }
            chat_logger.log_system(error_msg, error=True)
            scan.status = ScanStatus.FAILED
            scan.error = error_msg
            db.commit()
            return
        
        iteration = 0
        completed = False
        
        # MAIN LOOP
        while iteration < max_iterations and not completed:
            iteration += 1
            self.iteration_count = iteration
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Iteration {iteration}/{max_iterations}")
            logger.info(f"{'='*60}")
            
            # FASE 2: Dynamic model selection for this iteration
            if self.hybrid_mode and iteration > 1:  # Skip first (already selected)
                current_task_type = self._determine_task_type()
                new_model, new_model_type, routing_reason = self._select_model(current_task_type)
                
                # Check if model switch needed
                switch_info = self._switch_model(new_model, new_model_type)
                
                if switch_info:
                    # Model switched! Yield switch event
                    yield {
                        "type": "system_info",
                        "subtype": "model_switch",
                        "content": f"🔄 Switching to Gemini {new_model_type} for {current_task_type}",
                        "metadata": {
                            "from_model": switch_info["from_model"],
                            "to_model": new_model_type,
                            "task_type": current_task_type,
                            "reasoning": routing_reason,
                            "context_summary": switch_info["context_summary"]
                        }
                    }
                    chat_logger.log_system(f"Model switch: {switch_info['from_model']} → {new_model_type}", **switch_info)
                    
                    # Context handoff: start new chat with context
                    self.chat = new_model.start_chat(enable_automatic_function_calling=False)
                    context_msg = f"{switch_info['context_summary']} Continue the assessment."
                    
                    logger.info(f"📋 Context handoff: {context_msg[:100]}...")
                    
                    yield {
                        "type": "system_info",
                        "subtype": "context_handoff",
                        "content": f"📋 Transferring context to {new_model_type} model",
                        "metadata": {
                            "context_tokens": len(context_msg.split()),
                            "summary": switch_info["context_summary"]
                        }
                    }
                    
                    # Send context to new model with error handling
                    try:
                        start_time = time.time()
                        response = await asyncio.to_thread(self.chat.send_message, context_msg)
                        response_time = time.time() - start_time
                        
                        # Record cost for context handoff
                        self._record_api_call(response, new_model_type, "context_handoff", cost_tracker, response_time)
                        
                        logger.info(f"✅ Context handoff successful ({response_time:.2f}s)")
                    except Exception as handoff_error:
                        error_msg = f"Failed to transfer context to {new_model_type} model: {str(handoff_error)}"
                        logger.error(error_msg, exc_info=True)
                        yield {
                            "type": "system",
                            "content": f"❌ {error_msg}",
                            "metadata": {"error": True, "error_type": type(handoff_error).__name__}
                        }
                        # Continue with old model instead of crashing
                        self.chat = selected_model.start_chat(enable_automatic_function_calling=False)
                        self.current_model = selected_model
                        self.current_model_type = model_type
                        logger.warning(f"⚠️ Reverting to {model_type} model")
                        continue
            
            # Check if AI wants to call a function (with error handling)
            try:
                if not response.candidates or not response.candidates[0].content.parts:
                    logger.warning("⚠️ No response parts from AI")
                    break
                
                part = response.candidates[0].content.parts[0]
            except (IndexError, AttributeError) as e:
                logger.error(f"❌ Invalid response structure from AI: {e}")
                yield {
                    "type": "system",
                    "content": "⚠️ Received unexpected response from AI. Retrying...",
                    "metadata": {"error": True}
                }
                # Try to continue with a prompt
                try:
                    response = await asyncio.to_thread(
                        self.chat.send_message, 
                        "Please continue with the assessment or call complete_assessment if done."
                    )
                    continue
                except:
                    break
            
            # Check if it's a function call (with error handling for malformed protobuf)
            function_call = None
            function_name = None
            
            try:
                if not hasattr(part, 'function_call') or not part.function_call:
                    # Not a function call, check if it's text
                    continue
                    
                function_call = part.function_call
                function_name = function_call.name
            except (KeyError, AttributeError) as attr_error:
                # Gemini SDK might raise KeyError when accessing malformed protobuf attributes
                error_msg = f"Failed to access function_call attributes (possibly malformed protobuf): {attr_error}"
                logger.error(error_msg, exc_info=True)
                
                # Write to critical error file
                try:
                    from datetime import datetime
                    with open("logs/CRITICAL_ERROR.txt", "a", encoding="utf-8") as f:
                        f.write(f"\n\n{'='*80}\n")
                        f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                        f.write(f"ERROR: Malformed Protobuf Attribute Access\n")
                        f.write(f"Error Type: {type(attr_error).__name__}\n")
                        f.write(f"Error Message: {attr_error}\n")
                        f.write(f"{'='*80}\n")
                        f.flush()
                except:
                    pass
                
                yield {
                    "type": "system",
                    "content": f"⚠️ Received malformed response from AI. Retrying...",
                    "metadata": {"error": True, "error_type": type(attr_error).__name__}
                }
                
                # Try to continue
                try:
                    response = await asyncio.to_thread(
                        self.chat.send_message, 
                        "Please continue with the assessment or call complete_assessment if done."
                    )
                    continue
                except:
                    break
                    
            # Process function call
            if function_call and function_name:
                
                logger.info(f"="*60)
                logger.info(f"🔍 PROCESSING FUNCTION CALL: {function_name}")
                logger.info(f"="*60)
                
                # CRITICAL DEBUG: Log raw function_call structure BEFORE any processing
                try:
                    logger.info(f"🔬 RAW function_call object:")
                    logger.info(f"   Type: {type(function_call)}")
                    logger.info(f"   Name: {function_name}")
                    logger.info(f"   Has args: {hasattr(function_call, 'args')}")
                    if hasattr(function_call, 'args'):
                        logger.info(f"   Args type: {type(function_call.args)}")
                        logger.info(f"   Args repr (first 500 chars): {repr(function_call.args)[:500]}")
                        # Try to serialize to JSON for inspection
                        try:
                            import json
                            from google.protobuf.json_format import MessageToDict
                            raw_dict = MessageToDict(function_call.args._pb, preserving_proto_field_name=True)
                            logger.info(f"   Args as JSON: {json.dumps(raw_dict, indent=2)}")
                        except Exception as json_err:
                            logger.warning(f"   Could not serialize args to JSON: {json_err}")
                except Exception as debug_err:
                    logger.error(f"   Failed to log raw function_call: {debug_err}")
                
                # Convert protobuf Struct to dict properly (handles special characters)
                arguments = {}
                try:
                    import json
                    from google.protobuf.json_format import MessageToDict
                    
                    print(f"\n{'='*60}")
                    print(f"[FUNCTION CALL] PROCESSING: {function_name}")
                    print(f"{'='*60}")
                    
                    logger.info(f"🔍 Converting function args for: {function_name}")
                    logger.info(f"   Args type: {type(function_call.args)}")
                    
                    # Log raw args structure for debugging (with MAXIMUM safety)
                    try:
                        # Don't even try to access keys() if it might fail
                        # Just check if the object exists
                        logger.info(f"   Args object exists: {function_call.args is not None}")
                        logger.info(f"   Has _pb attribute: {hasattr(function_call.args, '_pb')}")
                        
                        # Try to get length/count without iterating
                        try:
                            if hasattr(function_call.args, '__len__'):
                                args_len = len(function_call.args)
                                logger.info(f"   Args count: {args_len}")
                                print(f"   Args count: {args_len}")
                        except:
                            logger.info(f"   Cannot determine args count")
                    except Exception as key_log_error:
                        logger.warning(f"   Could not inspect args structure: {type(key_log_error).__name__}: {key_log_error}")
                        print(f"   [WARN] Inspection error: {key_log_error}")
                    
                    # CRITICAL FIX: Skip MessageToDict entirely - it CANNOT handle keys with \n
                    # Go DIRECTLY to iteration method which has key sanitization
                    
                    # Direct iteration with aggressive key sanitization (ONLY METHOD)
                    logger.info("   Using direct iteration with key sanitization (ROBUST METHOD)...")
                    print("   [INFO] Using direct iteration with aggressive key sanitization...")
                    
                    try:
                        # function_call.args is a Struct, iterate directly
                        iteration_count = 0
                        for key in function_call.args:
                            iteration_count += 1
                            try:
                                # CRITICAL: Log RAW key BEFORE any processing
                                import sys
                                sys.stdout.write(f"\n[ITERATION {iteration_count}] Raw key: {repr(key)} (type: {type(key).__name__})\n")
                                sys.stdout.flush()
                                
                                # Clean key AGGRESSIVELY - remove ALL control characters
                                original_key = key
                                clean_key = str(key).strip()
                                # Remove newlines, tabs, carriage returns, and other control chars
                                clean_key = clean_key.replace('\n', '').replace('\r', '').replace('\t', '').replace('\x0b', '').replace('\x0c', '')
                                
                                if original_key != clean_key:
                                    sys.stdout.write(f"   [CLEAN] Cleaned key: {repr(original_key)} -> {repr(clean_key)}\n")
                                    sys.stdout.flush()
                                    logger.warning(f"   Key sanitized: {repr(original_key)} → {repr(clean_key)}")
                                
                                if not clean_key:
                                    sys.stdout.write(f"   [WARN] Key became empty after cleaning: {repr(original_key)}, skipping\n")
                                    sys.stdout.flush()
                                    logger.warning(f"   Key became empty after cleaning: {repr(original_key)}")
                                    continue
                                
                                # Get value (this should work for Struct)
                                value = function_call.args[key]  # Use ORIGINAL key to access, but store with CLEAN key
                                
                                # Check if value is JSON serializable
                                try:
                                    import json
                                    json.dumps(value)
                                    arguments[clean_key] = value
                                except (TypeError, ValueError):
                                    # Convert non-serializable to string
                                    sys.stdout.write(f"   [WARN] Value for {clean_key} not JSON serializable, converting to string\n")
                                    sys.stdout.flush()
                                    logger.warning(f"   Value for {clean_key} not JSON serializable, converting to string")
                                    arguments[clean_key] = str(value)
                                
                                sys.stdout.write(f"   [OK] Extracted: {clean_key} = {str(value)[:50]}\n")
                                sys.stdout.flush()
                                logger.debug(f"   Extracted: {clean_key}")
                            except Exception as key_error:
                                import traceback
                                error_details = f"""
   [ERROR] Failed to process key!
   Key: {repr(key)}
   Error Type: {type(key_error).__name__}
   Error Message: {key_error}
   Traceback:
{traceback.format_exc()}
"""
                                sys.stdout.write(error_details)
                                sys.stdout.flush()
                                logger.error(f"   Failed to process key {repr(key)}: {type(key_error).__name__}: {key_error}")
                                continue
                        
                        if arguments:
                            sys.stdout.write(f"   [SUCCESS] Direct iteration successful! Extracted {len(arguments)} args\n")
                            sys.stdout.write(f"   [SUCCESS] Keys: {list(arguments.keys())}\n")
                            sys.stdout.flush()
                            logger.info(f"   Direct iteration successful: {list(arguments.keys())}")
                        else:
                            sys.stdout.write(f"   [WARN] No arguments extracted from direct iteration\n")
                            sys.stdout.flush()
                            logger.warning(f"   No arguments extracted from direct iteration")
                    except Exception as direct_error:
                        import sys
                        import traceback
                        
                        # CRITICAL: Detailed error output with IMMEDIATE flush
                        error_report = f"""
{'='*80}
[ERROR] DIRECT ITERATION CATASTROPHIC FAILURE
{'='*80}
Function: {function_name}
Error Type: {type(direct_error).__name__}
Error Message: {direct_error}

Full Traceback:
{traceback.format_exc()}
{'='*80}
"""
                        sys.stdout.write(error_report)
                        sys.stdout.flush()
                        
                        logger.error(f"   Direct iteration failed: {type(direct_error).__name__}: {direct_error}")
                        # Don't raise - continue with empty arguments BUT log heavily
                        arguments = {}
                    
                    # OLD CODE BELOW - COMPLETELY DISABLED (kept for reference only)
                    if False:
                        logger.info("   Attempting MessageToDict conversion...")
                        try:
                            # CRITICAL: Wrap MessageToDict in comprehensive error handling
                            try:
                                # Check if _pb is the correct type
                                pb_obj = function_call.args._pb
                                logger.info(f"   _pb type: {type(pb_obj)}")
                                
                                # Only use MessageToDict if it's a proper protobuf message
                                if hasattr(pb_obj, 'DESCRIPTOR'):
                                    raw_arguments = MessageToDict(pb_obj, preserving_proto_field_name=True)
                                    logger.info(f"   ✅ MessageToDict successful")
                                    logger.info(f"   Type of result: {type(raw_arguments)}")
                                    logger.info(f"   Raw keys from MessageToDict: {list(raw_arguments.keys())}")
                                else:
                                    logger.warning(f"   ⚠️ _pb object has no DESCRIPTOR, cannot use MessageToDict")
                                    logger.warning(f"   _pb is type: {type(pb_obj).__name__}")
                                    # Skip to next method
                                    raise AttributeError("_pb has no DESCRIPTOR attribute")
                            except KeyError as msgtodict_key_error:
                                # THIS is where '\n description' error might occur!
                                print(f"\n{'!'*60}")
                                print(f"[ERROR] KeyError during MessageToDict!")
                                print(f"{'!'*60}")
                                print(f"Error: {repr(str(msgtodict_key_error))}")
                                print(f"Function: {function_name}")
                                print(f"This indicates protobuf has malformed field name (newline in key)")
                                print(f"Falling back to direct iteration...")
                                print(f"{'!'*60}\n")
                                
                                logger.error(f"   ❌ KeyError during MessageToDict: {repr(str(msgtodict_key_error))}")
                                logger.error(f"      This indicates protobuf has malformed field name")
                                # Try alternative: iterate over protobuf fields directly
                                raise
                            except AttributeError as attr_error:
                                logger.error(f"   ❌ AttributeError during MessageToDict: {attr_error}")
                                logger.error(f"      Cannot access DESCRIPTOR on _pb object")
                                raise
                            
                            # CRITICAL: Always sanitize keys even after MessageToDict
                            arguments = {}
                            try:
                                for key, value in raw_arguments.items():
                                    try:
                                        # Log BEFORE sanitization
                                        logger.debug(f"   Processing key: {repr(key)} (type: {type(key)})")
                                        
                                        clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                                        if clean_key != key:
                                            logger.warning(f"   🧹 Sanitized key: {repr(key)} → {repr(clean_key)}")
                                        if clean_key:  # Only add non-empty keys
                                            arguments[clean_key] = value
                                        else:
                                            logger.warning(f"   ⚠️ Key became empty after sanitization: {repr(key)}")
                                    except KeyError as key_clean_error:
                                        logger.error(f"   ❌ KeyError processing key: {repr(str(key_clean_error))}")
                                        logger.error(f"      Original key: {repr(key)}")
                                        # Try with a safe default key
                                        safe_key = f"arg_{len(arguments)}"
                                        logger.warning(f"   Using safe key: {safe_key}")
                                        arguments[safe_key] = value
                                    except Exception as key_clean_error:
                                        logger.error(f"   ❌ Error processing key {repr(key)}: {type(key_clean_error).__name__}: {key_clean_error}")
                                        # Try with a safe default key
                                        safe_key = f"arg_{len(arguments)}"
                                        logger.warning(f"   Using safe key: {safe_key}")
                                        arguments[safe_key] = value
                                
                                logger.info(f"   🧹 Keys after sanitization: {list(arguments.keys())}")
                            except KeyError as sanitize_key_error:
                                logger.error(f"   ❌ KeyError in sanitization loop: {repr(str(sanitize_key_error))}")
                                logger.error(f"   ❌ This is the '\n description' error!")
                                # Fall through to fallback method
                                raise
                            except Exception as sanitize_error:
                                logger.error(f"   ❌ Sanitization loop failed: {type(sanitize_error).__name__}: {sanitize_error}")
                                # Fall through to fallback method
                                raise
                        except (KeyError, Exception) as msgtodict_error:
                            logger.error(f"   ❌ MessageToDict conversion chain failed: {type(msgtodict_error).__name__}: {msgtodict_error}")
                            # Fall through to fallback method
                            raise
                    else:
                        # Method 2: Direct iteration if _pb not available (PRIMARY METHOD)
                        print("   Using direct iteration (ROBUST METHOD)...")
                        logger.info("   _pb not available, using direct iteration (PRIMARY METHOD)...")
                        try:
                            # function_call.args is a Struct, iterate directly
                            for key in function_call.args:
                                try:
                                    # Clean key AGGRESSIVELY - remove ALL control characters
                                    original_key = key
                                    clean_key = str(key).strip()
                                    # Remove newlines, tabs, carriage returns, and other control chars
                                    clean_key = clean_key.replace('\n', '').replace('\r', '').replace('\t', '').replace('\x0b', '').replace('\x0c', '')
                                    
                                    if original_key != clean_key:
                                        print(f"   [CLEAN] Cleaned key: {repr(original_key)} -> {repr(clean_key)}")
                                        logger.warning(f"   🧹 Key sanitized: {repr(original_key)} → {repr(clean_key)}")
                                    
                                    if not clean_key:
                                        print(f"   [WARN] Key became empty after cleaning: {repr(original_key)}, skipping")
                                        logger.warning(f"   ⚠️ Key became empty after cleaning: {repr(original_key)}")
                                        continue
                                    
                                    # Get value (this should work for Struct)
                                    value = function_call.args[key]  # Use ORIGINAL key to access, but store with CLEAN key
                                    
                                    # Check if value is JSON serializable
                                    try:
                                        import json
                                        json.dumps(value)
                                        arguments[clean_key] = value
                                    except (TypeError, ValueError):
                                        # Convert non-serializable to string
                                        print(f"   [WARN] Value for {clean_key} not JSON serializable, converting to string")
                                        logger.warning(f"   ⚠️ Value for {clean_key} not JSON serializable, converting to string")
                                        arguments[clean_key] = str(value)
                                    
                                    print(f"   [OK] Extracted: {clean_key} = {str(value)[:50]}")
                                    logger.debug(f"   ✓ Extracted: {clean_key}")
                                except Exception as key_error:
                                    print(f"   [ERROR] Failed to process key {repr(key)}: {key_error}")
                                    logger.error(f"   ❌ Failed to process key {repr(key)}: {type(key_error).__name__}: {key_error}")
                                    continue
                            
                            if arguments:
                                print(f"   [SUCCESS] Direct iteration successful! Extracted {len(arguments)} args")
                                print(f"   Keys: {list(arguments.keys())}")
                                logger.info(f"   ✅ Direct iteration successful: {list(arguments.keys())}")
                            else:
                                print(f"   [WARN] No arguments extracted from direct iteration")
                                logger.warning(f"   ⚠️ No arguments extracted from direct iteration")
                        except Exception as direct_error:
                            print(f"   [ERROR] Direct iteration failed: {direct_error}")
                            logger.error(f"   ❌ Direct iteration failed: {type(direct_error).__name__}: {direct_error}")
                            raise
                    
                except Exception as conv_error:
                    # Method 3: Fallback with sanitization
                    print(f"\n{'='*60}")
                    print(f"[CRITICAL] ALL PROTOBUF CONVERSION METHODS FAILED")
                    print(f"{'='*60}")
                    print(f"Error Type: {type(conv_error).__name__}")
                    print(f"Error Message: {conv_error}")
                    print(f"Function: {function_name}")
                    print(f"{'='*60}")
                    print(f"Attempting fallback with aggressive key sanitization...\n")
                    
                    logger.error(f"{'='*60}")
                    logger.error(f"⚠️ CRITICAL: Protobuf conversion failed")
                    logger.error(f"   Error type: {type(conv_error).__name__}")
                    logger.error(f"   Error message: {conv_error}")
                    logger.error(f"   Function: {function_name}")
                    logger.error(f"{'='*60}")
                    logger.warning(f"   Attempting fallback with aggressive key sanitization...")
                    
                    try:
                        # Last resort: MANUAL protobuf parsing without MessageToDict
                        logger.warning("   Attempting MANUAL protobuf field extraction...")
                        
                        # Method A: Try to access protobuf fields directly
                        try:
                            if hasattr(function_call.args, '_pb'):
                                pb_obj = function_call.args._pb
                                # Get all fields from the protobuf descriptor
                                if hasattr(pb_obj, 'DESCRIPTOR') and hasattr(pb_obj.DESCRIPTOR, 'fields'):
                                    for field in pb_obj.DESCRIPTOR.fields:
                                        try:
                                            field_name = field.name
                                            # Clean the field name IMMEDIATELY
                                            clean_field_name = str(field_name).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                                            
                                            if not clean_field_name:
                                                logger.warning(f"   ⚠️ Field has empty name after cleaning: {repr(field_name)}")
                                                continue
                                            
                                            # Try to get field value
                                            if hasattr(pb_obj, clean_field_name):
                                                field_value = getattr(pb_obj, clean_field_name)
                                                arguments[clean_field_name] = field_value
                                                logger.debug(f"   ✓ Extracted field: {clean_field_name}")
                                            else:
                                                logger.warning(f"   ⚠️ Field {clean_field_name} not accessible")
                                        except Exception as field_error:
                                            logger.error(f"   ❌ Error extracting field: {field_error}")
                                            continue
                                    
                                    if arguments:
                                        logger.info(f"✅ Manual field extraction successful: {len(arguments)} arguments")
                                    else:
                                        logger.warning("   No fields extracted via DESCRIPTOR")
                        except Exception as pb_field_error:
                            logger.error(f"   ❌ Protobuf field extraction failed: {pb_field_error}")
                        
                        # Method B: Direct iteration over function_call.args (CORRECT METHOD)
                        if not arguments:
                            logger.warning("   Trying direct iteration over function_call.args...")
                            try:
                                # function_call.args is a Struct, we can iterate its keys
                                for key in function_call.args:
                                    try:
                                        clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                                        if clean_key:
                                            value = function_call.args[key]
                                            arguments[clean_key] = value
                                            logger.debug(f"   ✓ Extracted via iteration: {clean_key}")
                                    except Exception as iter_error:
                                        logger.error(f"   ❌ Error iterating key {repr(key)}: {iter_error}")
                                        continue
                                
                                if arguments:
                                    logger.info(f"✅ Direct iteration successful: {len(arguments)} arguments")
                            except Exception as iter_error:
                                logger.error(f"   ❌ Direct iteration failed: {iter_error}")
                        
                        if not arguments:
                            logger.error(f"❌ No arguments extracted after all fallback attempts!")
                            logger.error(f"   function_call.args type: {type(function_call.args)}")
                            logger.error(f"   function_call.args repr: {repr(function_call.args)[:200]}")
                            
                    except Exception as fallback_error:
                        import sys
                        
                        # CRITICAL: Print to console immediately (NO EMOJIS - Windows encoding)
                        fallback_error_details = f"""
{'='*80}
[ERROR] ALL PROTOBUF CONVERSION METHODS FAILED!
{'='*80}
Function: {function_name}
Original Error Type: {type(conv_error).__name__}
Original Error Message: {conv_error}
Fallback Error Type: {type(fallback_error).__name__}
Fallback Error Message: {fallback_error}
{'='*80}
"""
                        print(fallback_error_details, flush=True)
                        sys.stdout.flush()
                        
                        logger.error(f"❌ ALL conversion methods failed")
                        logger.error(f"   Fallback error: {type(fallback_error).__name__}: {fallback_error}", exc_info=True)
                        logger.error(f"   Original error: {type(conv_error).__name__}: {conv_error}")
                        # Continue with empty arguments - better than crashing
                        arguments = {}
                        
                        # Yield a detailed error event to frontend
                        yield {
                            "type": "system",
                            "content": f"⚠️ **Function Call Parameter Extraction Failed**\n\n"
                                      f"AI attempted to call `{function_name}` but parameter parsing failed.\n\n"
                                      f"**Error:** {type(conv_error).__name__}: {str(conv_error)}\n\n"
                                      f"This is a known protobuf parsing issue. Attempting to continue with default parameters...",
                            "metadata": {
                                "error": True,
                                "error_type": type(conv_error).__name__,
                                "function": function_name,
                                "warning": True
                            }
                        }
                
                logger.info(f"📞 AI Function Call: {function_name}")
                logger.info(f"📥 Arguments ({len(arguments)} params): {list(arguments.keys())}")
                
                # CRITICAL: Convert protobuf objects to JSON-serializable types
                json_safe_arguments = {}
                for arg_key, arg_value in arguments.items():
                    try:
                        # Check if value is JSON serializable
                        import json
                        json.dumps(arg_value)  # Test serialization
                        json_safe_arguments[arg_key] = arg_value
                        logger.info(f"   Arg: {repr(arg_key)} = {repr(str(arg_value)[:100])}")
                    except (TypeError, ValueError) as json_error:
                        # Value is not JSON serializable (e.g., protobuf object)
                        logger.warning(f"   ⚠️ Arg {repr(arg_key)} is not JSON serializable: {type(arg_value)}")
                        logger.warning(f"      Converting protobuf object to string representation")
                        
                        # Convert to string or extract primitive value
                        if hasattr(arg_value, '__str__'):
                            str_value = str(arg_value)
                            json_safe_arguments[arg_key] = str_value
                            logger.info(f"   Arg (converted): {repr(arg_key)} = {repr(str_value[:100])}")
                        else:
                            logger.error(f"   ❌ Cannot convert {repr(arg_key)} to safe type, skipping")
                
                # Use json_safe_arguments instead of arguments for events
                arguments = json_safe_arguments
                
                # CRITICAL: Final sanitization - remove ALL problematic keys
                # This is the LAST LINE OF DEFENSE before yielding
                final_safe_arguments = {}
                for arg_key, arg_value in arguments.items():
                    # Ultra-aggressive key cleaning
                    ultra_clean_key = str(arg_key).strip()
                    # Remove ALL control characters (not just newlines)
                    ultra_clean_key = ''.join(char for char in ultra_clean_key if char.isprintable() and char not in ['\n', '\r', '\t', '\x0b', '\x0c'])
                    if not ultra_clean_key:
                        ultra_clean_key = f"param_{len(final_safe_arguments)}"
                        logger.warning(f"   ⚠️ Key became empty after ultra-cleaning: {repr(arg_key)}, using: {ultra_clean_key}")
                    
                    # Also ensure value is safe
                    if isinstance(arg_value, str):
                        # Remove control characters from string values too
                        ultra_clean_value = ''.join(char for char in arg_value if char.isprintable() or char in ['\n', '\t', ' '])
                        final_safe_arguments[ultra_clean_key] = ultra_clean_value
                    else:
                        final_safe_arguments[ultra_clean_key] = arg_value
                    
                    if arg_key != ultra_clean_key:
                        logger.warning(f"   🧹 Cleaned key: {repr(arg_key)} → {repr(ultra_clean_key)}")
                
                arguments = final_safe_arguments
                logger.info(f"🔒 Final safe arguments: {list(arguments.keys())}")
                
                logger.info(f"="*60)
                
                # Yield function call event (wrapped in try-except for KeyError)
                try:
                    yield {
                        "type": "function_call",
                        "content": f"⚡ AI decided to execute: **{function_name}**",
                        "metadata": {
                            "function": function_name,
                            "arguments": arguments,
                            "iteration": iteration
                        }
                    }
                    
                    # Log to chat logger (with error handling)
                    try:
                        chat_logger.log_tool(
                            f"⚡ Executing: {function_name}",
                            function=function_name,
                            arguments=arguments
                        )
                    except Exception as log_err:
                        logger.error(f"⚠️ Failed to log to chat logger: {type(log_err).__name__}: {log_err}")
                        # Continue execution - logging failure shouldn't stop the scan
                    
                except KeyError as key_err:
                    logger.error(f"❌ KeyError in function call event: {key_err}")
                    logger.error(f"   Key that caused error: {repr(str(key_err))}")
                    logger.error(f"   Available keys: {list(arguments.keys())}")
                    raise  # Re-raise to be caught by outer handler
                except Exception as event_err:
                    logger.error(f"❌ Error creating function call event: {type(event_err).__name__}: {event_err}")
                    raise
                
                # Execute function with progress updates (with real target substitution and timeout)
                try:
                    # Yield "tool starting" event
                    yield {
                        "type": "output",
                        "content": f"🔧 **Starting {function_name}...**\n\nExecuting tool with target substitution...",
                        "metadata": {
                            "tool": function_name,
                            "status": "starting"
                        }
                    }
                    
                    # Create progress task for long-running tools
                    tool_start = time.time()
                    result = None
                    execution_task = asyncio.create_task(
                        tool_executor.execute_function(function_name, arguments)
                    )
                    
                    # Progress monitoring loop
                    progress_intervals = [10, 20, 30, 45, 60, 90, 120, 180, 240]  # seconds
                    last_progress = 0
                    
                    while not execution_task.done():
                        try:
                            # Wait with short timeout
                            result = await asyncio.wait_for(
                                asyncio.shield(execution_task), 
                                timeout=1.0
                            )
                            break  # Tool completed
                        except asyncio.TimeoutError:
                            # Tool still running - check if we should send progress update
                            elapsed = time.time() - tool_start
                            
                            # Send progress update at defined intervals
                            for interval in progress_intervals:
                                if elapsed >= interval and last_progress < interval:
                                    yield {
                                        "type": "output",
                                        "content": f"⏳ **{function_name} in progress...** ({int(elapsed)}s elapsed)\n\nTool is still running, this may take a while depending on target size.",
                                        "metadata": {
                                            "tool": function_name,
                                            "elapsed": int(elapsed),
                                            "status": "running"
                                        }
                                    }
                                    last_progress = interval
                                    break
                            
                            # Check for overall timeout (5 minutes)
                            if elapsed > 300:
                                execution_task.cancel()
                                raise asyncio.TimeoutError("Tool execution exceeded 5 minutes")
                    
                    # If result not set, get it from task
                    if result is None:
                        result = execution_task.result()
                    
                except asyncio.TimeoutError:
                    logger.error(f"⏱️ Function {function_name} timed out after 5 minutes")
                    result = {
                        "status": "error",
                        "tool": function_name,
                        "message": "Tool execution timed out after 5 minutes"
                    }
                    yield {
                        "type": "output",
                        "content": f"⏱️ **{function_name} timed out**\n\nTool exceeded maximum execution time (5 minutes). Target may be unresponsive or scan too comprehensive.",
                        "metadata": {
                            "tool": function_name,
                            "status": "timeout",
                            "error": True
                        }
                    }
                except Exception as exec_error:
                    logger.error(f"❌ Function execution error: {exec_error}", exc_info=True)
                    result = {
                        "status": "error",
                        "tool": function_name,
                        "message": str(exec_error)
                    }
                    yield {
                        "type": "output",
                        "content": f"❌ **{function_name} failed**\n\n```\n{str(exec_error)}\n```",
                        "metadata": {
                            "tool": function_name,
                            "status": "error",
                            "error": True,
                            "error_message": str(exec_error)
                        }
                    }
                
                # FASE 2: Update tracking
                self.tool_call_count += 1
                self.last_action = "tool_execution"
                self.conversation_history.append({
                    "type": "tool_execution",
                    "tool": function_name,
                    "result_status": result.get('status'),
                    "iteration": iteration
                })
                
                # Process and yield result
                logger.info(f"✅ Function executed: {function_name}")
                logger.debug(f"Result (raw): {result}")
                
                # CRITICAL: Sanitize ALL keys in result dictionary before using
                def sanitize_dict_keys(d: Any) -> Any:
                    """Recursively sanitize dictionary keys to remove newlines and special chars"""
                    if isinstance(d, dict):
                        sanitized = {}
                        for key, value in d.items():
                            # Clean the key
                            clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                            if not clean_key:
                                clean_key = f"field_{len(sanitized)}"
                            # Recursively sanitize value if it's a dict
                            sanitized[clean_key] = sanitize_dict_keys(value)
                        return sanitized
                    elif isinstance(d, list):
                        return [sanitize_dict_keys(item) for item in d]
                    else:
                        return d
                
                result = sanitize_dict_keys(result)
                logger.debug(f"Result (sanitized): {result}")
                
                # Yield detailed result event
                execution_time = time.time() - tool_start
                
                if result.get('status') == 'success':
                    summary = result.get('summary', {})
                    parsed = result.get('parsed_output', {})
                    
                    # Build detailed content based on tool type
                    content = f"✅ **{result.get('tool', function_name).upper()} Completed** ({execution_time:.1f}s)\n\n"
                    
                    # Nmap results
                    if 'open_ports_count' in summary:
                        content += f"📊 **Open Ports:** {summary['open_ports_count']}\n"
                        if parsed.get('open_ports'):
                            content += f"\n```\n"
                            for port_info in parsed['open_ports'][:5]:  # Show first 5 ports
                                port = port_info.get('port', 'N/A')
                                service = port_info.get('service', 'unknown')
                                version = port_info.get('version', '')
                                content += f"{port}/tcp  {service} {version}\n".strip() + "\n"
                            if len(parsed['open_ports']) > 5:
                                content += f"... and {len(parsed['open_ports']) - 5} more ports\n"
                            content += f"```\n"
                    
                    # Nuclei/vulnerability results
                    if 'findings_count' in summary:
                        content += f"\n🔍 **Findings:** {summary['findings_count']}\n"
                        if 'severity_breakdown' in summary:
                            breakdown = summary['severity_breakdown']
                            if breakdown.get('critical', 0) > 0:
                                content += f"  🔴 Critical: {breakdown['critical']}\n"
                            if breakdown.get('high', 0) > 0:
                                content += f"  🟠 High: {breakdown['high']}\n"
                            if breakdown.get('medium', 0) > 0:
                                content += f"  🟡 Medium: {breakdown['medium']}\n"
                            if breakdown.get('low', 0) > 0:
                                content += f"  🔵 Low: {breakdown['low']}\n"
                        
                        # Show top findings
                        if parsed.get('vulnerabilities'):
                            content += f"\n**Top Findings:**\n"
                            for vuln in parsed['vulnerabilities'][:3]:
                                name = vuln.get('name', 'Unknown')
                                severity = vuln.get('severity', 'info')
                                content += f"  • [{severity.upper()}] {name}\n"
                    
                    # WhatWeb/tech detection results
                    if function_name == 'run_whatweb' and parsed:
                        if parsed.get('cms'):
                            cms = parsed['cms']
                            content += f"\n🎯 **CMS Detected:** {cms.get('name')} {cms.get('version', '')}\n"
                        if parsed.get('server'):
                            server = parsed['server']
                            content += f"🖥️ **Server:** {server.get('software')} {server.get('version', '')}\n"
                        if parsed.get('technologies'):
                            content += f"⚙️ **Technologies:** {', '.join([t.get('name', '') for t in parsed['technologies'][:5]])}\n"
                    
                    # Generic summary
                    if 'key_findings' in summary:
                        content += f"\n**Key Findings:**\n"
                        for finding in summary['key_findings'][:3]:
                            content += f"  • {finding}\n"
                    
                    # Sanitize metadata before yielding
                    safe_metadata = {
                        **result,
                        "execution_time": execution_time
                    }
                    safe_metadata = sanitize_dict_keys(safe_metadata)
                    
                    yield {
                        "type": "function_result",
                        "content": content,
                        "metadata": safe_metadata
                    }
                    chat_logger.log_output(content, **result)
                    
                elif result.get('status') == 'completed':
                    # Assessment complete!
                    completed = True
                    safe_result = sanitize_dict_keys(result)
                    yield {
                        "type": "decision",
                        "content": f"🎯 **Assessment Complete**\n\n{safe_result.get('summary')}\n\nConfidence: {safe_result.get('confidence', 0):.0%}",
                        "metadata": safe_result
                    }
                    chat_logger.log_decision(f"🎯 Assessment Complete: {result.get('summary')}")
                    
                    # Mark scan as completed
                    scan.status = ScanStatus.COMPLETED
                    scan.completed_at = datetime.utcnow()
                    db.commit()
                    
                    break
                else:
                    # Error
                    safe_result = sanitize_dict_keys(result)
                    content = f"❌ {safe_result.get('tool', function_name)} failed: {safe_result.get('message')}"
                    yield {
                        "type": "function_result",
                        "content": content,
                        "metadata": safe_result
                    }
                    chat_logger.log_output(content, **result)
                
                # Send result back to AI (with error handling)
                try:
                    function_response = genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=function_name,
                            response={'result': result}
                        )
                    )
                    
                    logger.info(f"💬 Sending function result back to AI...")
                    response = await asyncio.wait_for(
                        asyncio.to_thread(self.chat.send_message, function_response),
                        timeout=30.0  # 30 second timeout for AI response
                    )
                except asyncio.TimeoutError:
                    logger.error("⏱️ AI response timed out")
                    yield {
                        "type": "system",
                        "content": "⚠️ AI response timed out. Completing scan...",
                        "metadata": {"error": True}
                    }
                    break
                except Exception as ai_error:
                    logger.error(f"❌ Failed to communicate with AI: {ai_error}", exc_info=True)
                    yield {
                        "type": "system",
                        "content": f"❌ AI communication error: {str(ai_error)}",
                        "metadata": {"error": True}
                    }
                    break
            
            # Check if AI has text response (thinking/analysis)
            elif hasattr(part, 'text') and part.text:
                text = part.text.strip()
                if not text:
                    logger.debug("⚠️ Empty text response from AI, skipping")
                    continue
                    
                logger.info(f"💭 AI Thought: {text[:200]}...")
                
                # FASE 2: Update tracking
                self.last_action = "thought"
                self.conversation_history.append({
                    "type": "thought",
                    "content": text[:100],
                    "iteration": iteration
                })
                
                # Yield thought event with better formatting
                # Check if this is strategic thinking or just acknowledgment
                is_strategic = any(keyword in text.lower() for keyword in [
                    'strategy', 'plan', 'next', 'will', 'should', 'analyze', 
                    'assess', 'recommend', 'suggest', 'observe', 'finding'
                ])
                
                if is_strategic or len(text) > 50:
                    # Show full strategic thinking
                    yield {
                        "type": "thought",
                        "content": f"🧠 **AI Analysis:**\n\n{text}",
                        "metadata": {
                            "iteration": iteration,
                            "is_strategic": is_strategic,
                            "length": len(text)
                        }
                    }
                    chat_logger.log_thought(text, iteration=iteration)
                else:
                    # Short acknowledgment - show but less prominently
                    yield {
                        "type": "output",
                        "content": f"💬 {text}",
                        "metadata": {
                            "iteration": iteration,
                            "is_acknowledgment": True
                        }
                    }
                
                # If no more function calls and we have text, AI might be done
                # Send a follow-up to encourage function call or completion
                follow_up = "Based on your analysis, what is your next action? Call a tool or complete_assessment if objective is met."
                response = await asyncio.to_thread(self.chat.send_message, follow_up)
            
            else:
                logger.warning("⚠️ Unexpected response format from AI")
                break
        
        # Loop ended
        if iteration >= max_iterations:
            logger.warning(f"⚠️ Max iterations reached ({max_iterations})")
            yield {
                "type": "system",
                "content": f"⏱️ Maximum iterations reached. Assessment may be incomplete.",
                "metadata": {"iterations": iteration}
            }
            chat_logger.log_system(f"⏱️ Max iterations reached: {iteration}")
        
        if not completed:
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            db.commit()
        
        # FASE 2: Generate and yield cost report
        cost_report = cost_tracker.get_cost_report()
        cost_summary = cost_tracker.get_summary_text()
        
        logger.info("="*60)
        cost_tracker.log_summary()
        logger.info("="*60)
        
        yield {
            "type": "cost_report",
            "content": cost_summary,
            "metadata": cost_report
        }
        chat_logger.log_system("💰 Cost report generated", **cost_report)
        
        yield {
            "type": "system",
            "content": "✅ Autonomous assessment loop completed",
            "metadata": {
                "iterations": iteration,
                "status": "completed" if completed else "max_iterations"
            }
        }
        chat_logger.log_system("✅ Assessment loop completed", iterations=iteration)
    
    def _build_initial_prompt(self, user_objective: str) -> str:
        """
        Build initial prompt for AI (TARGET-AGNOSTIC + MULTI-TOOL INTELLIGENT CHAINING)
        
        CRITICAL: Never mention actual target names here
        Enhanced for intelligent tool chaining and context-aware decisions
        """
        prompt = """
# 🎯 AUTONOMOUS SECURITY ASSESSMENT MISSION

You are an elite AI security analyst conducting **authorized defensive security testing** to identify and fix vulnerabilities in production systems.

## 📋 YOUR OBJECTIVE:
{objective}

## 🛠️ YOUR SECURITY TOOLKIT (Function Calling)

### 1️⃣ **run_nmap** - Network Discovery & Port Scanning
**Purpose:** Discover attack surface (open ports, services, OS fingerprinting)
**When to Use:** ALWAYS use FIRST - it's the foundation for all other decisions
**Parameters:**
  - target_placeholder: ALWAYS use 'TARGET_HOST'
  - scan_profile: 'quick' (fast), 'normal' (balanced), 'aggressive' (comprehensive)
**Output:** Open ports, service versions, OS detection
**Next Step:** Analyze ports to decide which vulnerability scanners to deploy

### 2️⃣ **run_nuclei** - Automated Vulnerability Scanner
**Purpose:** Detect known CVEs, OWASP Top 10, misconfigurations
**When to Use:** AFTER nmap discovers web services (ports 80, 443, 8080, 8443, 3000, 5000, etc.)
**Parameters:**
  - target_placeholder: ALWAYS use 'TARGET_URL'
  - severity_filter: 'critical', 'high', 'medium', 'low', 'all' (recommend: 'critical,high')
  - template_category: 'cves', 'vulnerabilities', 'exposures', 'all'
**Output:** CVE findings with severity ratings
**Next Step:** Prioritize vulnerabilities by risk level

### 3️⃣ **run_whatweb** - Web Technology Fingerprinting
**Purpose:** Identify CMS, frameworks, libraries for targeted scanning
**When to Use:** AFTER nmap confirms web service, helps guide nuclei scanning
**Parameters:**
  - target_placeholder: ALWAYS use 'TARGET_URL'
  - aggression_level: 1 (stealthy), 2 (balanced), 3 (aggressive)
**Output:** Technology stack, versions, plugins
**Next Step:** Use tech info to refine vulnerability scanning

### 4️⃣ **run_sslscan** - SSL/TLS Security Analysis
**Purpose:** Identify weak encryption, certificate issues, protocol vulnerabilities
**When to Use:** WHEN nmap detects HTTPS (port 443, 8443, etc.)
**Parameters:**
  - target_placeholder: ALWAYS use 'TARGET_HOST'
**Output:** Certificate details, cipher suites, TLS versions
**Next Step:** Report encryption security posture

### 5️⃣ **complete_assessment** - Finalize & Generate Report
**Purpose:** Conclude assessment with comprehensive security report
**When to Use:** After all relevant scans OR when no further scans add value
**Parameters:**
  - summary: Brief overview of findings
  - risk_score: 1-10 (overall security risk rating)

## 🧠 INTELLIGENT CHAINING STRATEGY

### PHASE 1: Reconnaissance (MANDATORY START)
```
ACTION: Call run_nmap(target_placeholder='TARGET_HOST', scan_profile='normal')
REASONING: "I need to discover the attack surface before selecting specific vulnerability scanners"
```

### PHASE 2: Analyze & Adapt (CRITICAL DECISION POINT)
After nmap completes, analyze findings and chain tools intelligently:

**Scenario A: Web Services Detected (ports 80, 443, 8080, 8443, 3000, 5000, 8000)**
```
Priority 1: run_nuclei for vulnerability scanning
  → severity_filter='critical,high' (focus on serious issues)
Priority 2: run_whatweb for tech identification (helps interpret nuclei findings)
Priority 3: run_sslscan IF HTTPS detected (port 443/8443)
```

**Scenario B: HTTPS Only (port 443 but no HTTP)**
```
Priority 1: run_sslscan (encryption is critical for HTTPS-only services)
Priority 2: run_nuclei (web vulns still relevant)
```

**Scenario C: Non-Web Services Only (SSH, MySQL, FTP, RDP, etc.)**
```
Decision: Skip web-specific tools
Reasoning: "No web services detected. Web vulnerability scanning not applicable."
Action: complete_assessment with findings summary
```

**Scenario D: No Open Ports / All Filtered**
```
Decision: complete_assessment immediately
Reasoning: "No accessible services found. Host may be offline or heavily firewalled."
```

### PHASE 3: Deep Analysis (OPTIONAL - based on findings)
```
IF nuclei finds critical vulnerabilities:
  → Prioritize by severity
  → Provide remediation steps
  → complete_assessment

IF whatweb detects outdated CMS:
  → Already covered by nuclei
  → complete_assessment

IF minimal findings:
  → complete_assessment with "low risk" summary
```

## ✅ DECISION FRAMEWORK

**Rule 1: START WITH NMAP** - No exceptions. It guides all subsequent decisions.

**Rule 2: ANALYZE BEFORE ACTING** - After EACH tool:
- Review the output summary
- Identify key findings (ports, services, vulnerabilities)
- Ask: "What's the NEXT MOST VALUABLE scan based on what I learned?"

**Rule 3: CHAIN BASED ON EVIDENCE**
- Web ports found → Deploy web scanners (nuclei, whatweb)
- HTTPS found → Deploy sslscan
- No web services → Skip web tools (explain why)

**Rule 4: PRIORITIZE BY IMPACT**
- Critical vulnerabilities → Top priority
- Large attack surface → Comprehensive scanning
- Small attack surface → Focused scanning

**Rule 5: KNOW WHEN TO STOP** - Call complete_assessment when:
- All relevant scans completed
- No additional scans would provide value
- Sufficient data for security recommendations

**Rule 6: BE TRANSPARENT** - Explain reasoning:
- "Running nmap first to discover services..."
- "Found port 80 open, deploying nuclei for web vulnerability scanning..."
- "No HTTPS detected, skipping sslscan..."
- "Assessment complete with X findings..."

## ⚠️ CRITICAL CONSTRAINTS
1. **TARGET-AGNOSTIC:** ALWAYS use 'TARGET_HOST' or 'TARGET_URL' placeholders
2. **FUNCTION CALLS ONLY:** Don't just describe - ACTUALLY call the functions
3. **ONE TOOL AT A TIME:** Wait for results before deciding next step
4. **ADAPTIVE:** Change strategy based on findings, don't stick to rigid plans

## 🚀 START NOW
Your FIRST action should be explaining your strategy briefly, then calling **run_nmap**.

Example:
"I'll begin with network reconnaissance using nmap to discover open ports and services, which will guide my vulnerability scanning strategy."
→ run_nmap(target_placeholder='TARGET_HOST', scan_profile='normal')

Begin your assessment!
""".format(objective=user_objective)
        
        return prompt

