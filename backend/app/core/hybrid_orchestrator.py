"""
Hybrid Orchestrator - Safe Flash/Pro Model Management

PURPOSE:
    Intelligent routing between Flash (fast/cheap) and Pro (smart/expensive)
    WITHOUT triggering Gemini SDK protobuf bugs.

KEY PRINCIPLE:
    NEVER transfer context directly between models.
    ALWAYS use explicit context serialization.

ARCHITECTURE:
    Flash Model (Fresh) → Execute Recon → Serialize Context
                                            ↓
    Pro Model (Fresh) ← Inject Context ← Context Document

NO SCHEMA REUSE. NO CHAT HISTORY TRANSFER. PURE DATA ONLY.
"""
from typing import Dict, Any, List, AsyncGenerator, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.models.scan import Scan, ScanStatus
from app.core.context_serializer import ContextSerializer
from app.utils.logger import logger
from datetime import datetime
import asyncio
import json


class HybridOrchestrator:
    """
    Orchestrates hybrid Flash/Pro workflow with safe transitions
    
    This is the CRITICAL component that prevents '\n description' errors
    by ensuring models are NEVER directly connected.
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize with API key (models created fresh per scan)
        
        Args:
            gemini_api_key: Google AI API key
        """
        self.api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        self.context_serializer = ContextSerializer()
        self.current_phase = "initialization"
        
        # Initialize Pro Analyzer and Escalation Handler
        from app.core.pro_analyzer import ProStrategicAnalyzer
        from app.core.escalation_handler import EscalationHandler
        from app.core.model_selector import ModelSelector
        
        self.pro_analyzer = ProStrategicAnalyzer(gemini_api_key)
        self.escalation_handler = EscalationHandler(self.pro_analyzer)
        self.model_selector = ModelSelector()
        
        # Context storage (NO model objects stored here)
        self.flash_context = None
        self.flash_findings = None
        self.tool_results = {}
        
        logger.info("🔀 HybridOrchestrator initialized")
    
    def _create_fresh_flash_model(self):
        """
        Create FRESH Flash model instance
        
        CRITICAL: New instance every time, no reuse
        """
        try:
            # Get fresh tool definitions for Flash
            flash_tools = self._get_flash_tool_definitions()
            
            # Flash 2.5 model for tactical execution (fast, efficient, cheap)
            # This is for ROUTINE tool execution decisions, not strategic analysis
            model_name = 'gemini-2.5-flash'  # Flash 2.5 for maximum speed
            logger.info(f"⚡ Flash 2.5 Tactical Model: {model_name} (for fast tool execution)")
            
            model = genai.GenerativeModel(
                model_name=model_name,
                tools=flash_tools,
                system_instruction="""You are a TACTICAL security assessment agent with direct access to scanning tools.

YOUR ROLE: Fast, efficient tool execution - not strategic planning (that's Pro's job).

CRITICAL RULES:
1. You MUST use function calling to execute scans
2. NEVER output JSON command structures or scan strategies as text
3. When you need to scan something, CALL THE FUNCTION directly
4. Use 'TARGET_HOST', 'TARGET_URL', or 'TARGET_DOMAIN' as placeholder values in function arguments
5. DO NOT use real target names in function calls

Your job is TACTICAL EXECUTION. Be fast, be efficient, execute immediately.""",
                generation_config={
                    'temperature': 0.5,  # Balanced for tactical decisions
                    'top_p': 0.9,  # High quality fast responses
                    'top_k': 40,
                    'max_output_tokens': 1024,  # Concise tactical decisions
                }
            )
            
            logger.info("✅ Fresh Flash model created")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create Flash model: {e}")
            raise
    
    def _create_fresh_pro_model(self):
        """
        Create FRESH Pro model instance
        
        CRITICAL: New instance every time, separate from Flash
        """
        try:
            # Get fresh tool definitions for Pro (different from Flash!)
            pro_tools = self._get_pro_tool_definitions()
            
            # This method is for creating Pro 2.5 model (for deep analysis phase)
            # But we should use ProStrategicAnalyzer instead, not create model here
            # Keeping this for backward compatibility but Pro logic should be in ProStrategicAnalyzer
            model = genai.GenerativeModel(
                model_name='gemini-2.5-pro',  # Pro 2.5 model for deep strategic analysis
                tools=pro_tools,
                generation_config={
                    'temperature': 0.4,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,
                }
            )
            
            logger.info("✅ Fresh Pro model created")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create Pro model: {e}")
            raise
    
    def _get_flash_tool_definitions(self) -> List:
        """
        Get FRESH tool definitions for Flash model (reconnaissance tools)
        
        Returns new list instance every time (NO REUSE)
        """
        from app.core.tool_definition_manager import ToolDefinitionManager
        
        # Get fresh tools from manager
        tools = ToolDefinitionManager.get_flash_tools()
        
        logger.debug(f"📋 Flash tools: {len(tools[0].function_declarations)} tools")
        return tools
    
    def _get_pro_tool_definitions(self) -> List:
        """
        Get FRESH tool definitions for Pro model (analysis tools)
        
        For now, uses same tools as Flash but created FRESH.
        In future, can have Pro-specific tools (exploit research, etc.)
        
        Returns new list instance every time (NO REUSE)
        """
        from app.core.tool_definition_manager import ToolDefinitionManager
        
        # Get fresh tools from manager (completely separate from Flash tools)
        tools = ToolDefinitionManager.get_pro_tools()
        
        logger.debug(f"📋 Pro tools: {len(tools[0].function_declarations)} tools")
        return tools
    
    async def execute_scan(
        self, 
        scan: Scan,
        db: Session,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute scan with intelligent Flash/Pro routing
        
        This is the MAIN ENTRY POINT that replaces old FunctionCallingAgent.
        
        Args:
            scan: Scan model instance
            db: Database session
            max_iterations: Max iterations per phase
            
        Yields:
            SSE events for streaming to frontend
            
        Process:
            1. Analyze request complexity
            2. PHASE 1: Flash reconnaissance (ALWAYS)
            3. Evaluate if Pro needed
            4. PHASE 2: Pro deep analysis (if needed) with SAFE context
            5. Generate unified report
        """
        target = scan.target
        user_prompt = scan.user_prompt or "Comprehensive security assessment"
        
        logger.info(f"🎯 Starting hybrid scan: {target}")
        logger.info(f"📝 User objective: {user_prompt}")
        
        # Yield start event
        yield {
            "type": "system",
            "content": f"🤖 Initializing hybrid AI agent for {target}",
            "metadata": {"phase": "initialization", "target": target}
        }
        
        # PHASE 1: Flash Reconnaissance (ALWAYS executed)
        logger.info("="*60)
        logger.info("PHASE 1: FLASH RECONNAISSANCE")
        logger.info("="*60)
        
        self.current_phase = "flash_reconnaissance"
        
        yield {
            "type": "system",
            "content": "⚡ **Phase 1: Reconnaissance** (Flash Model - Fast & Efficient)",
            "metadata": {"phase": "flash_reconnaissance", "model": "flash"}
        }
        
        # Execute Flash phase
        try:
            async for event in self._flash_reconnaissance(scan, db, max_iterations):
                yield event
        except Exception as flash_error:
            logger.error("Flash reconnaissance failed: %s", str(flash_error), exc_info=True)  # Use % to avoid formatting issues
            
            # Write to critical error file
            try:
                with open("logs/CRITICAL_ERROR.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*80}\n")
                    f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                    f.write(f"ERROR: Flash Reconnaissance Failed\n")
                    f.write(f"Target: {scan.target}\n")
                    f.write(f"Scan ID: {scan.id}\n")
                    f.write(f"Error: {flash_error}\n")
                    f.write(f"{'='*80}\n")
                    f.flush()
            except:
                pass
            
            yield {
                "type": "system",
                "content": f"❌ Flash reconnaissance failed: {str(flash_error)}",
                "metadata": {"error": True, "phase": "flash_reconnaissance"}
            }
            
            scan.status = ScanStatus.FAILED
            scan.error_message = str(flash_error)
            scan.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # PHASE 1 COMPLETE - Evaluate complexity
        logger.info("="*60)
        logger.info("EVALUATING COMPLEXITY")
        logger.info("="*60)
        
        # SAFETY CHECK: If no tools executed, mark as FAILED (not COMPLETED)
        if len(self.tool_results) == 0:
            logger.error("❌ No tools executed during Flash reconnaissance - marking as FAILED")
            
            yield {
                "type": "system",
                "content": "❌ **Scan Failed**: No reconnaissance tools were executed. This may be due to API issues or configuration problems.",
                "metadata": {"error": True, "phase": "flash_failed"}
            }
            
            scan.status = ScanStatus.FAILED
            scan.error_message = "No tools executed during reconnaissance phase"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return
        
        yield {
            "type": "system",
            "content": "🔍 Evaluating findings complexity...",
            "metadata": {"phase": "evaluation"}
        }
        
        # Decide if Pro needed
        pro_needed = self._evaluate_complexity(self.flash_findings)
        
        if not pro_needed:
            # Flash sufficient - complete scan
            logger.info("✅ Flash findings sufficient - scan complete")
            
            yield {
                "type": "system",
                "content": "✅ **Assessment Complete** - No deep analysis required",
                "metadata": {"phase": "complete", "pro_used": False}
            }
            
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Pro needed - continue to Phase 2
        logger.info("🎓 Complexity detected - escalating to Pro model")
        
        yield {
            "type": "system",
            "content": "🎓 **Transitioning to Phase 2: Deep Analysis** (Pro Model - Advanced Reasoning)",
            "metadata": {"phase": "transition", "from": "flash", "to": "pro"}
        }
        
        # PHASE 2: Pro Deep Analysis (with SAFE context)
        logger.info("="*60)
        logger.info("PHASE 2: PRO DEEP ANALYSIS")
        logger.info("="*60)
        
        self.current_phase = "pro_analysis"
        
        try:
            async for event in self._pro_deep_analysis(scan, db, max_iterations):
                yield event
        except Exception as pro_error:
            logger.error("Pro analysis failed: %s", str(pro_error), exc_info=True)  # Use % to avoid formatting issues
            
            # Write to critical error file
            try:
                with open("logs/CRITICAL_ERROR.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*80}\n")
                    f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                    f.write(f"ERROR: Pro Analysis Failed\n")
                    f.write(f"Target: {scan.target}\n")
                    f.write(f"Error: {pro_error}\n")
                    f.write(f"{'='*80}\n")
                    f.flush()
            except:
                pass
            
            yield {
                "type": "system",
                "content": f"⚠️ Pro analysis encountered error: {str(pro_error)}\n\nFlash reconnaissance results are still available.",
                "metadata": {"error": True, "phase": "pro_analysis", "flash_complete": True}
            }
            
            # Don't fail entire scan - Flash results are still valid
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # COMPLETE
        logger.info("="*60)
        logger.info("SCAN COMPLETE")
        logger.info("="*60)
        
        yield {
            "type": "system",
            "content": "✅ **Assessment Complete** - Full analysis finished",
            "metadata": {"phase": "complete", "pro_used": True}
        }
        
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        db.commit()
    
    async def _flash_reconnaissance(
        self,
        scan: Scan,
        db: Session,
        max_iterations: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute Phase 1: Flash reconnaissance
        
        CRITICAL: Uses FRESH Flash model, no context transfer
        """
        from app.tools.function_toolbox import ToolExecutor
        
        # Create FRESH Flash model
        flash_model = self._create_fresh_flash_model()
        flash_chat = flash_model.start_chat(enable_automatic_function_calling=False)
        
        # Reset tool_results for this reconnaissance phase
        self.tool_results = {}
        
        # Store reference to this generator for streaming tool events
        def create_event_streamer():
            """Factory to create event streaming callback"""
            event_queue = []
            
            async def stream_tool_event(event: Dict[str, Any]):
                """Callback to queue tool events for streaming"""
                try:
                    event_queue.append(event)
                    logger.debug(f"📡 Queued event: {event.get('type')} from {event.get('tool')}")
                except Exception as e:
                    logger.error(f"Failed to queue event: {e}")
            
            return stream_tool_event, event_queue
        
        event_callback, event_queue = create_event_streamer()
        
        # Initialize tool executor AFTER reset to ensure it has the correct reference
        tool_executor = ToolExecutor(
            real_target=scan.target,
            scan_id=scan.id,
            db_session=db,
            tool_results=self.tool_results,  # Pass tool_results for placeholder substitution
            event_callback=event_callback  # Enable real-time streaming
        )
        
        # Initial prompt for Flash - CRITICAL: Must trigger function calling
        initial_prompt = f"""You are an elite security reconnaissance AI with direct access to scanning tools via function calling.

**MISSION**: {scan.user_prompt or 'Comprehensive security reconnaissance and attack surface mapping'}
**TARGET**: {scan.target} ({self._detect_target_type(scan.target)})

**CRITICAL RULES**:
1. CALL FUNCTIONS DIRECTLY - never output JSON or text commands
2. Use placeholders: 'TARGET_DOMAIN', 'TARGET_HOST', 'TARGET_URL', 'DISCOVERED_HOSTS'
3. After subfinder finds subdomains, ALWAYS use 'DISCOVERED_HOSTS' in next tools

**SCANNING WORKFLOW** (Efficient & Intelligent):

Phase 1 - Reconnaissance:
1. run_subfinder → Discover subdomains (CRITICAL FIRST STEP)
   - Automatic DNS validation filters invalid domains
   - Only valid subdomains proceed to next phase

Phase 2 - Verification:
2. run_httpx with ['DISCOVERED_HOSTS'] → Identify active web services
   - Scans ALL valid subdomains from Phase 1
   - Identifies which hosts respond to HTTP/HTTPS
   - Returns active URLs for vulnerability scanning

Phase 3 - Intelligence Gathering:
3. run_nmap → Port scan (quick profile recommended)
4. run_whatweb → Technology fingerprinting

Phase 4 - Vulnerability Assessment:
5. run_nuclei with severity='critical,high' → Vulnerability scan
   - Focus on active URLs from httpx results
   - Faster than scanning 'all' severities

Phase 5 - Additional Verification (IF WARRANTED):
6. run_ffuf → Content discovery (if administrative interfaces found)
   - Only on security-relevant targets (admin.*, api.*, management.*)
   - Ensures comprehensive coverage of accessible resources
   
7. run_sqlmap → Database security verification (ONLY if strong indicators exist)
   - Requires Pro approval for safety validation (will escalate automatically)
   - Only use when: NUCLEI detects potential SQLi OR database error messages observed
   - Pro will assess verification feasibility before proceeding

Phase 6 - Completion:
8. complete_assessment → Provide final summary (CALL ONCE ONLY)

**CRITICAL RULES**:
- Always use ['DISCOVERED_HOSTS'] after subfinder completes
- DNS validation happens automatically (filters invalid domains)
- Only assess active/validated targets (verified by HTTPX)
- Provide brief analysis after each major tool execution
- This is an AUTHORIZED security assessment for vulnerability documentation

**IMPORTANT**: All tools are used for defensive security assessment purposes to help organizations identify and remediate vulnerabilities before they can be discovered by malicious actors.

**Begin systematic security assessment now.**"""
        
        # STEP 0: Pro generates initial strategy (strategic planning)
        yield {
            "type": "system_info",
            "subtype": "model_selection",
            "content": "🎯 PRO AI: Generating initial strategic plan...",
            "metadata": {"model": "pro-2.5", "phase": "strategic_planning"}
        }
        
        initial_strategy = await self.pro_analyzer.generate_initial_strategy(
            target=scan.target,
            target_type=self._detect_target_type(scan.target),
            user_objective=scan.user_prompt
        )
        
        if initial_strategy.get('status') == 'success':
            yield {
                "type": "analysis",
                "content": f"📋 Strategic Plan:\n\n{initial_strategy.get('strategy', '')}",
                "metadata": {"model": "pro", "phase": "initial_strategy"}
            }
        
        yield {
            "type": "system_info",
            "subtype": "model_switch",
            "content": "⚡ Switching to FLASH AI for tactical execution...",
            "metadata": {"from": "pro", "to": "flash"}
        }
        
        yield {
            "type": "thought",
            "content": f"⚡ Flash AI executing reconnaissance based on Pro's strategy...",
            "metadata": {"phase": "flash_reconnaissance", "model": "flash"}
        }
        
        # Send initial prompt with FORCED function calling
        # Option A: Force Gemini to use function calls, not text responses
        try:
            response = await asyncio.to_thread(
                flash_chat.send_message,
                initial_prompt,
                tool_config={
                    'function_calling_config': {
                        'mode': 'ANY'  # Force function calling - no text responses allowed
                    }
                }
            )
            logger.info("✅ Initial prompt sent with FORCED function calling mode")
        except Exception as prompt_error:
            logger.error(f"❌ Failed to send prompt with function calling config: {prompt_error}")
            # Fallback: try without tool_config
            response = await asyncio.to_thread(flash_chat.send_message, initial_prompt)
            logger.warning("⚠️ Sent prompt without forced function calling (fallback)")
        
        # Main loop
        iteration = 0
        # tool_results already reset above - don't reset again here!
        tools_executed_count = 0
        consecutive_no_action = 0  # Safety: track consecutive iterations without tool execution
        MAX_NO_ACTION = 3  # Stop if no tools executed for 3 consecutive iterations
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Flash iteration {iteration}/{max_iterations}")
            
            # Check if it's a function call
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning("❌ No response parts from Flash - model may be blocked or error occurred")
                logger.warning(f"   Response finish_reason: {response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'}")
                consecutive_no_action += 1
                if consecutive_no_action >= MAX_NO_ACTION:
                    logger.error(f"❌ Flash stopped responding after {consecutive_no_action} iterations without executing tools")
                    logger.error("   This may indicate: API key issues, content policy violation, or prompt confusion")
                    break
                # Try to continue with next iteration
                continue
            
            part = response.candidates[0].content.parts[0]
            
            # Check for function call with COMPREHENSIVE error protection
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                
                # CRITICAL: Wrap ALL protobuf access in try-except to catch KeyError from malformed keys
                try:
                    function_name = function_call.name
                    logger.info(f"⚡ Flash calling: {function_name}")
                except (KeyError, AttributeError) as name_error:
                    # CRITICAL: Don't use f-string with exception - logger will try to format it!
                    logger.error("❌ CRITICAL: Failed to read function_call.name due to malformed protobuf key")
                    logger.error("   Error details: %s", str(name_error))  # Use % formatting to avoid f-string issues
                    logger.error("   This is the '\\n description' bug - protobuf has newline in key name")
                    logger.error("   Skipping this function call and continuing")
                    
                    yield {
                        "type": "system",
                        "content": "⚠️ Gemini returned malformed function call (protobuf bug). Retrying...",
                        "metadata": {"error": True, "phase": "flash", "retry": True}
                    }
                    
                    consecutive_no_action += 1
                    if consecutive_no_action >= MAX_NO_ACTION:
                        logger.error("❌ Too many consecutive errors, stopping Flash reconnaissance")
                        break
                    continue  # Skip this iteration and try again
                
                # Extract arguments (with aggressive sanitization)
                arguments = {}
                try:
                    # Direct iteration over protobuf keys (safer than MessageToDict)
                    for key in function_call.args:
                        # Aggressively clean the key
                        clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '').replace('\x0b', '').replace('\x0c', '')
                        if clean_key:
                            try:
                                arguments[clean_key] = function_call.args[key]
                            except (KeyError, AttributeError) as val_error:
                                logger.warning(f"⚠️ Failed to read value for key '{clean_key}': {val_error}")
                                continue
                except Exception as arg_error:
                    logger.error(f"❌ Failed to extract arguments: {arg_error}", exc_info=True)
                    arguments = {}
                
                if not arguments:
                    logger.warning(f"⚠️ No valid arguments extracted for {function_name}, using defaults")
                    # Don't skip - some functions might have optional args
                
                yield {
                    "type": "tool",
                    "content": f"⚡ Executing {function_name.upper()}...",
                    "metadata": {"tool": function_name, "phase": "flash"}
                }
                
                # Execute tool with real-time streaming
                tool_result = await tool_executor.execute_function(function_name, arguments)
                
                # Yield any queued events from tool execution
                while event_queue:
                    queued_event = event_queue.pop(0)
                    yield queued_event
                
                # Check if assessment complete
                if function_name == 'complete_assessment':
                    logger.info("🏁 Assessment completion requested by AI")
                    # Don't store complete_assessment in tool_results
                    # Break immediately - reconnaissance phase complete
                    tools_executed_count += 1
                    yield {
                        "type": "output",
                        "content": "✅ COMPLETE_ASSESSMENT completed",
                        "metadata": {"tool": "complete_assessment", "status": "completed"}
                    }
                    break  # Exit reconnaissance loop immediately
                
                # Store result with detailed logging
                tool_key = function_name.replace('run_', '')
                self.tool_results[tool_key] = tool_result
                logger.info(f"📦 Stored tool result: {tool_key} → keys: {tool_result.keys() if isinstance(tool_result, dict) else 'not a dict'}")
                if isinstance(tool_result, dict) and tool_key == 'subfinder':
                    logger.info(f"   📊 Subfinder result has 'subdomains' key: {'subdomains' in tool_result}")
                    if 'subdomains' in tool_result:
                        logger.info(f"   📊 Subdomains count: {len(tool_result['subdomains'])}")
                
                tools_executed_count += 1
                consecutive_no_action = 0  # Reset counter on successful tool execution
                
                # Build comprehensive metadata for UI display
                output_metadata = {
                    "tool": function_name,
                    "status": tool_result.get('status'),
                    "execution_time": tool_result.get('execution_time', 0)
                }
                
                # Add tool-specific counts/findings for UI
                if 'total_subdomains' in tool_result:
                    output_metadata['findings'] = tool_result['total_subdomains']
                    output_metadata['interesting'] = len(tool_result.get('interesting_findings', []))
                elif 'findings_count' in tool_result:
                    output_metadata['findings'] = tool_result['findings_count']
                elif 'findings' in tool_result:
                    if isinstance(tool_result['findings'], list):
                        output_metadata['findings'] = len(tool_result['findings'])
                elif 'alive' in tool_result:
                    output_metadata['findings'] = tool_result['alive']
                elif 'total_found' in tool_result:
                    output_metadata['findings'] = tool_result['total_found']
                elif 'open_ports' in tool_result:
                    if isinstance(tool_result['open_ports'], list):
                        output_metadata['findings'] = len(tool_result['open_ports'])
                
                # STANDARDIZED output message with execution time and findings
                exec_time_text = ""
                findings_text = ""
                
                # Add execution time if available
                if tool_result.get('execution_time'):
                    exec_time_text = f"({tool_result['execution_time']:.1f}s)"
                
                # Use standardized findings_count or fall back to metadata
                if 'findings_count' in tool_result:
                    findings_text = f" - {tool_result['findings_count']} findings"
                elif 'findings_summary' in tool_result:
                    findings_text = f" - {tool_result['findings_summary']}"
                elif 'findings' in output_metadata and output_metadata['findings'] > 0:
                    findings_text = f" - {output_metadata['findings']} findings"
                    if 'interesting' in output_metadata:
                        findings_text += f" ({output_metadata['interesting']} interesting)"
                elif tool_result.get('status') == 'success':
                    # Make zero findings explicit
                    findings_text = " - 0 findings"
                
                yield {
                    "type": "output",
                    "content": f"✅ {function_name.upper()}{exec_time_text} completed{findings_text}",
                    "metadata": output_metadata
                }
                
                # Build intelligent response message for AI with reasoning prompt
                result_message = f"Tool execution result: {json.dumps(tool_result, default=str)}"
                
                # Add explicit guidance and request AI reasoning
                if function_name == 'run_subfinder' and tool_result.get('status') == 'success':
                    subdomain_count = tool_result.get('total_subdomains', 0)
                    if subdomain_count > 0:
                        result_message += f"\n\n**CRITICAL NEXT STEP**: {subdomain_count} subdomains discovered. You MUST call run_httpx with targets_placeholder=['DISCOVERED_HOSTS'] to probe ALL subdomains."
                        result_message += f"\n\n**PROVIDE BRIEF ANALYSIS** (1-2 sentences): What does finding {subdomain_count} subdomains tell you about the target's attack surface? Then call the next tool."
                
                elif function_name == 'run_httpx' and tool_result.get('status') == 'success':
                    alive_count = tool_result.get('alive', 0)
                    probed_count = tool_result.get('total_probed', 0)
                    if alive_count > 0:
                        result_message += f"\n\n**EXCELLENT**: Found {alive_count}/{probed_count} live web services!"
                        result_message += f"\n\n**PROVIDE BRIEF ANALYSIS** (1-2 sentences): What vulnerabilities should we check on these {alive_count} active web services? Then call run_nuclei or run_whatweb."
                    else:
                        result_message += f"\n\n**INFO**: Probed {probed_count} hosts but found no HTTP services. This is normal for non-web infrastructure."
                        result_message += f"\n\n**REASONING**: Briefly explain why we should now focus on port scanning instead of web scanning. Then call run_nmap."
                
                elif function_name == 'run_nmap' and tool_result.get('status') == 'success':
                    open_ports = tool_result.get('summary', {}).get('open_ports', []) if 'summary' in tool_result else []
                    result_message += f"\n\n**PORT SCAN COMPLETE**: Found {len(open_ports)} open ports."
                    result_message += f"\n\n**STRATEGIC ANALYSIS** (1-2 sentences): Based on discovered services, what should we investigate next? Then proceed."
                
                # Send result back to Flash with forced function calling
                try:
                    response = await asyncio.to_thread(
                        flash_chat.send_message,
                        result_message,
                        tool_config={
                            'function_calling_config': {
                                'mode': 'ANY'  # Continue forcing function calls
                            }
                        }
                    )
                except Exception as msg_error:
                    logger.warning(f"⚠️ Function calling config failed, using fallback: {msg_error}")
                    # Fallback without tool_config
                    response = await asyncio.to_thread(
                        flash_chat.send_message,
                        result_message
                    )
                
            else:
                # Text response from Flash (no function call)
                if hasattr(part, 'text') and part.text:
                    text_response = part.text.strip()
                    
                    # Check if Flash is outputting JSON instead of calling functions
                    if '{"' in text_response or 'scan_commands' in text_response or '"tool":' in text_response:
                        logger.error("❌ CRITICAL: Flash is outputting JSON instead of using function calling!")
                        logger.error("   This means the prompt is not clear enough or the model is confused")
                        logger.error("   Flash should CALL functions, not output JSON strategies")
                        
                        yield {
                            "type": "system",
                            "content": "⚠️ AI is generating strategies instead of executing tools. Retrying with clearer instructions...",
                            "metadata": {"warning": True, "phase": "flash"}
                        }
                    else:
                        # This is AI reasoning/analysis - DISPLAY IT!
                        logger.info(f"🧠 Flash providing reasoning (iteration {iteration})")
                        logger.info(f"   Reasoning preview: {text_response[:200]}...")
                        
                        yield {
                            "type": "analysis",
                            "content": f"🧠 **AI Analysis:**\n\n{text_response}",
                            "metadata": {"phase": "flash", "reasoning": True}
                        }
                    
                    # If Flash provides analysis without tool calls, it might be done
                    logger.info("Flash provided text response without tool call")
                
                # Flash is done (no more function calls)
                consecutive_no_action += 1
                if consecutive_no_action >= MAX_NO_ACTION:
                    logger.info("Flash reconnaissance complete - no more tool calls requested")
                    break
                
                # If tools were executed, Flash might be providing analysis - continue
                if tools_executed_count > 0:
                    break  # End reconnaissance phase
        
        # Extract findings from tool results
        self.flash_findings = ContextSerializer.extract_findings_from_results(self.tool_results)
        
        logger.info(f"✅ Flash reconnaissance complete - {len(self.tool_results)} tools executed")
        
        yield {
            "type": "system",
            "content": f"✅ **Phase 1 Complete** - {len(self.tool_results)} tools executed",
            "metadata": {"phase": "flash_complete", "tools_executed": len(self.tool_results)}
        }
    
    def _detect_target_type(self, target: str) -> str:
        """Detect if target is IP, domain, or URL"""
        import re
        
        # Remove protocol if present
        clean_target = target.replace('http://', '').replace('https://', '').split('/')[0]
        
        # Check if IP address
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if re.match(ip_pattern, clean_target):
            return "IP address"
        
        # Check if domain
        if '.' in clean_target:
            return "domain"
        
        return "hostname"
    
    def _evaluate_complexity(self, findings: Dict[str, Any]) -> bool:
        """
        Decide if Pro model needed based on Flash findings
        
        Decision Factors:
        - Critical vulnerabilities found
        - High-risk infrastructure
        - Large attack surface
        - Complex analysis needed
        
        Returns:
            True if Pro needed, False if Flash sufficient
        """
        if not findings:
            logger.info("No findings - Flash sufficient")
            return False
        
        # Check risk level
        risk_level = findings.get('risk_level', 'LOW')
        if risk_level in ['CRITICAL', 'HIGH']:
            logger.info(f"Risk level {risk_level} - Pro needed")
            return True
        
        # Check number of subdomains (large attack surface)
        subdomain_count = len(findings.get('subdomains', {}).get('list', []))
        if subdomain_count > 50:
            logger.info(f"{subdomain_count} subdomains - Pro needed for prioritization")
            return True
        
        # Check for critical ports (database exposure)
        open_ports = findings.get('ports', {}).get('open_ports', [])
        critical_ports = [p for p in open_ports if p.get('port') in [3306, 5432, 27017, 6379, 1433]]
        if critical_ports:
            logger.info(f"Critical ports exposed - Pro needed for deep analysis")
            return True
        
        # Check number of services (complexity)
        if len(open_ports) > 20:
            logger.info(f"{len(open_ports)} open ports - Pro needed")
            return True
        
        # Default: Flash sufficient
        logger.info("Flash findings sufficient - no Pro escalation needed")
        return False
    
    async def _pro_deep_analysis(
        self,
        scan: Scan,
        db: Session,
        max_iterations: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute Phase 2: Pro deep analysis with SAFE context
        
        CRITICAL IMPLEMENTATION:
        1. Create FRESH Pro chat (NO context transfer from Flash)
        2. Serialize Flash context to text document
        3. Pass context as PROMPT (not chat history)
        4. Define tool schemas FRESH (not transferred from Flash)
        5. Execute Pro analysis
        """
        # STEP 1: Serialize Flash context (SAFE)
        logger.info("📄 Serializing Flash context for Pro...")
        
        yield {
            "type": "system",
            "content": "📄 Preparing context document for advanced analysis...",
            "metadata": {"phase": "context_serialization"}
        }
        
        context_document = self.context_serializer.serialize(
            target=scan.target,
            tool_results=self.tool_results,
            findings=self.flash_findings
        )
        
        logger.info(f"✅ Context serialized ({len(context_document)} chars, ~{len(context_document)//4} tokens)")
        
        yield {
            "type": "system",
            "content": f"✅ Context prepared ({len(context_document)//4} tokens)",
            "metadata": {"phase": "context_ready", "tokens": len(context_document)//4}
        }
        
        # STEP 2: Create FRESH Pro chat (NO TRANSFER)
        logger.info("🎓 Creating fresh Pro model instance...")
        
        pro_model = self._create_fresh_pro_model()
        pro_chat = pro_model.start_chat(enable_automatic_function_calling=False)  # FRESH, no context
        
        yield {
            "type": "system",
            "content": "🎓 Pro model initialized (fresh instance, no context transfer)",
            "metadata": {"phase": "pro_init"}
        }
        
        # STEP 3: Inject context via prompt (SAFE)
        pro_prompt = f"""You are an advanced security analysis AI agent.

You are continuing a security assessment with deep vulnerability analysis.

{context_document}

Based on the reconnaissance findings above, perform comprehensive vulnerability assessment:

1. Analyze critical findings in detail
2. Research known exploits for identified software versions
3. Assess exploitability and impact
4. Prioritize remediation actions by risk
5. Generate detailed security recommendations

Your objective: {scan.user_prompt or 'Comprehensive vulnerability analysis and risk assessment'}

Use available tools to conduct thorough security analysis. Focus on actionable insights.

Begin the deep analysis."""
        
        yield {
            "type": "thought",
            "content": "🎓 Pro AI analyzing vulnerabilities and risks...",
            "metadata": {"phase": "pro_analysis"}
        }
        
        # STEP 4: Execute Pro analysis
        from app.tools.function_toolbox import ToolExecutor
        
        tool_executor = ToolExecutor(
            real_target=scan.target,
            scan_id=scan.id,
            db_session=db
        )
        
        # Send initial prompt to Pro
        response = await asyncio.to_thread(pro_chat.send_message, pro_prompt)
        
        # Main Pro loop
        iteration = 0
        pro_tools_executed = 0
        consecutive_no_action_pro = 0
        MAX_NO_ACTION_PRO = 3
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Pro iteration {iteration}/{max_iterations}")
            
            if not response.candidates or not response.candidates[0].content.parts:
                logger.info("No response parts from Pro")
                consecutive_no_action_pro += 1
                if consecutive_no_action_pro >= MAX_NO_ACTION_PRO:
                    logger.warning(f"Pro stopped responding after {consecutive_no_action_pro} iterations")
                    break
                continue
            
            part = response.candidates[0].content.parts[0]
            
            # Check for function call with COMPREHENSIVE error protection
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                
                # CRITICAL: Wrap ALL protobuf access in try-except to catch KeyError from malformed keys
                try:
                    function_name = function_call.name
                    logger.info(f"🎓 Pro calling: {function_name}")
                except (KeyError, AttributeError) as name_error:
                    # CRITICAL: Don't use f-string with exception - logger will try to format it!
                    logger.error("❌ CRITICAL: Failed to read function_call.name due to malformed protobuf key")
                    logger.error("   Error details: %s", str(name_error))  # Use % formatting to avoid f-string issues
                    logger.error("   This is the '\\n description' bug - protobuf has newline in key name")
                    logger.error("   Skipping this function call and continuing")
                    
                    yield {
                        "type": "system",
                        "content": "⚠️ Gemini returned malformed function call (protobuf bug). Retrying...",
                        "metadata": {"error": True, "phase": "pro", "retry": True}
                    }
                    
                    consecutive_no_action += 1
                    if consecutive_no_action >= MAX_NO_ACTION:
                        logger.error("❌ Too many consecutive errors, stopping Pro analysis")
                        break
                    continue  # Skip this iteration and try again
                
                # Extract arguments (with aggressive sanitization)
                arguments = {}
                try:
                    # Direct iteration over protobuf keys (safer than MessageToDict)
                    for key in function_call.args:
                        # Aggressively clean the key
                        clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '').replace('\x0b', '').replace('\x0c', '')
                        if clean_key:
                            try:
                                arguments[clean_key] = function_call.args[key]
                            except (KeyError, AttributeError) as val_error:
                                logger.warning(f"⚠️ Failed to read value for key '{clean_key}': {val_error}")
                                continue
                except Exception as arg_error:
                    logger.error(f"❌ Failed to extract arguments: {arg_error}", exc_info=True)
                    arguments = {}
                
                if not arguments:
                    logger.warning(f"⚠️ No valid arguments extracted for {function_name}, using defaults")
                    # Don't skip - some functions might have optional args
                
                yield {
                    "type": "tool",
                    "content": f"🎓 Executing {function_name.upper()}...",
                    "metadata": {"tool": function_name, "phase": "pro"}
                }
                
                # Execute tool
                tool_result = await tool_executor.execute_function(function_name, arguments)
                pro_tools_executed += 1
                consecutive_no_action_pro = 0  # Reset on successful execution
                
                yield {
                    "type": "output",
                    "content": f"✅ {function_name.upper()} completed",
                    "metadata": {"tool": function_name, "status": tool_result.get('status')}
                }
                
                # Send result back to Pro
                response = await asyncio.to_thread(
                    pro_chat.send_message,
                    f"Tool execution result: {json.dumps(tool_result, default=str)}"
                )
                
            else:
                # Text response from Pro (analysis/conclusion)
                if hasattr(part, 'text') and part.text:
                    yield {
                        "type": "analysis",
                        "content": part.text,
                        "metadata": {"phase": "pro"}
                    }
                    logger.info("Pro provided analysis without tool call - likely complete")
                
                # Pro is done
                consecutive_no_action_pro += 1
                if consecutive_no_action_pro >= MAX_NO_ACTION_PRO or pro_tools_executed > 0:
                    logger.info("Pro analysis complete")
                    break
        
        logger.info("✅ Pro analysis complete")
        
        yield {
            "type": "system",
            "content": "✅ **Phase 2 Complete** - Advanced analysis finished",
            "metadata": {"phase": "pro_complete"}
        }

