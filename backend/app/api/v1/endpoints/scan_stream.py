"""
Real-time streaming endpoint for AI Agent workflow
Uses Server-Sent Events (SSE) to stream AI thinking process like ChatGPT
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
from app.db.session import get_db
from app.models.scan import Scan, ScanStatus
from app.schemas.scan import ScanCreate
from app.utils.sanitizers import sanitize_target
from app.utils.logger import logger
from app.utils.json_sanitizer import sanitize_event, safe_json_dumps
from app.core.exceptions import BadRequestException
from datetime import datetime
import json
import asyncio

router = APIRouter()


def get_gemini_key(x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")) -> Optional[str]:
    """
    Extract Gemini API key from header
    Header name: X-Gemini-API-Key
    """
    if x_gemini_api_key:
        logger.debug(f"✅ Gemini API key received (length: {len(x_gemini_api_key)})")
    else:
        logger.debug("⚠️ No Gemini API key in request headers")
    return x_gemini_api_key


async def stream_agent_scan(
    scan_id: str,
    target: str,
    user_prompt: str,
    gemini_api_key: str,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    Generator that yields real-time events during AI Agent workflow

    Event types:
    - system: System messages (started, completed, error)
    - thought: AI reasoning/thinking
    - plan: Strategic planning decisions
    - tool: Tool execution started
    - output: Tool output/results
    - analysis: AI analysis of results
    - decision: Agent decision (continue/stop)
    """

    async def send_event(event_type: str, content: str, metadata: dict = None):
        """Helper to send SSE event with comprehensive sanitization"""
        event_data = {
            "type": event_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Sanitize the complete event using utility function
        safe_event = sanitize_event(event_data)
        
        # Use safe JSON dumps with automatic fallback
        json_str = safe_json_dumps(safe_event)
        
        await asyncio.sleep(0.01)  # Minimal delay for smooth streaming
        return json_str

    try:
        logger.info(f"🚀 Starting agent scan stream for scan_id={scan_id}, target={target}")
        logger.info(f"📝 User prompt: {user_prompt[:100]}..." if len(user_prompt) > 100 else f"📝 User prompt: {user_prompt}")
        logger.info(f"🔑 API key present: {bool(gemini_api_key)}, length: {len(gemini_api_key) if gemini_api_key else 0}")
        # Import here to avoid circular imports
        from app.services.ai_agent import AIAgent
        from app.tools.factory import ToolFactory
        from app.models.result import ScanResult

        # Initialize
        yield send_event("system", f"🤖 Agent-P starting analysis of {target}")
        yield send_event("thought", f"📝 User objective: {user_prompt}")

        # Get scan from DB
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"❌ Scan {scan_id} not found in database")
            yield send_event("system", "❌ Scan not found", {"error": True})
            return
        
        logger.info(f"✅ Scan record found: status={scan.status}, tools={scan.tools}")

        # Initialize AI Agent (non-blocking)
        logger.info(f"🤖 Initializing AI Agent with Gemini API...")
        yield send_event("system", "🤖 Connecting to Gemini AI...")
        
        try:
            # Run in thread pool to avoid blocking
            agent = await asyncio.to_thread(AIAgent, gemini_api_key)
            logger.info(f"✅ AI Agent initialized successfully")
            yield send_event("system", "✅ AI Agent ready!")
        except Exception as ai_error:
            logger.error(f"❌ Failed to initialize AI Agent: {str(ai_error)}", exc_info=True)
            yield send_event("system", f"❌ AI initialization failed: {str(ai_error)}", {"error": True})
            scan.status = ScanStatus.FAILED
            scan.error = str(ai_error)
            db.commit()
            return
            
        completed_tools = []
        all_results = {}
        max_iterations = 3
        iteration = 0

        # Phase 1: Initial Planning (non-blocking)
        logger.info(f"📋 Phase 1: Initial planning for target {target}")
        yield send_event("thought", "🧠 Analyzing target and creating strategic plan...")

        # Run planning in thread pool to avoid blocking
        initial_decision = await asyncio.to_thread(
            agent.initial_planning,
            target=target,
            user_objective=user_prompt or "General security assessment"
        )

        # Show planning results
        yield send_event(
            "plan",
            f"📋 Strategic Plan:\n\n**Selected Tools:** {', '.join(initial_decision.next_tools)}\n\n**Reasoning:** {initial_decision.reasoning}",
            {"tools": initial_decision.next_tools, "confidence": initial_decision.confidence_score}
        )

        # Store initial strategy in DB
        scan.ai_strategy = {
            'tools_selected': initial_decision.next_tools,
            'reasoning': initial_decision.reasoning,
            'confidence': initial_decision.confidence_score
        }
        scan.tools = initial_decision.next_tools
        db.commit()

        # Agent Loop: Execute → Observe → Refine
        while iteration < max_iterations and initial_decision.next_tools:
            iteration += 1

            yield send_event(
                "system",
                f"🔄 Iteration {iteration}/{max_iterations}",
                {"iteration": iteration, "max": max_iterations}
            )

            tools_to_run = initial_decision.next_tools

            # Phase 2: Execute Tools
            for tool_name in tools_to_run:
                if tool_name in completed_tools:
                    yield send_event("tool", f"⏭️ Skipping {tool_name} (already executed)")
                    continue

                logger.info(f"🔧 Starting execution of {tool_name} against {target}")
                yield send_event("tool", f"⚡ Executing {tool_name.upper()}...")
                yield send_event("thought", f"Running {tool_name} against {target}...")

                # Execute tool
                try:
                    logger.info(f"⚙️ Getting tool instance for {tool_name}")
                    tool = ToolFactory.get_tool(tool_name)

                    if not tool:
                        logger.warning(f"⚠️ Tool {tool_name} not available")
                        yield send_event("output", f"❌ Tool {tool_name} not available")
                        continue

                    # Run tool (non-blocking)
                    logger.info(f"▶️ Executing {tool_name}.execute()")
                    import time
                    start_time = time.time()
                    result = await asyncio.to_thread(tool.execute, target, scan.profile or "normal")
                    execution_time = time.time() - start_time
                    logger.info(f"✅ Tool {tool_name} completed in {execution_time:.2f}s")

                    # Save result to database with proper schema
                    scan_result = ScanResult(
                        scan_id=scan.id,
                        tool_name=tool_name,
                        raw_output=result.stdout if hasattr(result, 'stdout') else str(result.output if hasattr(result, 'output') else ""),
                        parsed_output=result.parsed_data if hasattr(result, 'parsed_data') else (result.findings if hasattr(result, 'findings') else None),
                        exit_code=result.exit_code if hasattr(result, 'exit_code') else 0,
                        execution_time=execution_time,
                        error_message=result.stderr if hasattr(result, 'stderr') and result.exit_code != 0 else None
                    )
                    db.add(scan_result)
                    db.commit()

                    completed_tools.append(tool_name)
                    all_results[tool_name] = result.output

                    # Show result summary with progress
                    findings_count = len(result.findings) if result.findings else 0
                    # Calculate total unique tools across all iterations
                    all_planned_tools = set(scan.tools if scan.tools else ['nmap'])
                    progress_percentage = int((len(completed_tools) / max(len(all_planned_tools), 1)) * 100)
                    
                    yield send_event(
                        "output",
                        f"✅ {tool_name.upper()} completed\n\n**Status:** {result.status}\n**Findings:** {findings_count}",
                        {
                            "tool": tool_name, 
                            "status": result.status, 
                            "findings": findings_count,
                            "progress": progress_percentage,
                            "completed": len(completed_tools),
                            "total": len(all_planned_tools)
                        }
                    )

                    # Show key findings if any
                    if result.findings and findings_count > 0:
                        findings_preview = "\n".join([f"• {f.get('title', f.get('port', 'Finding'))}" for f in result.findings[:3]])
                        yield send_event("output", f"**Key Findings:**\n{findings_preview}")

                except Exception as tool_error:
                    logger.error(f"Tool {tool_name} failed: {str(tool_error)}")
                    yield send_event("output", f"❌ {tool_name} failed: {str(tool_error)}")

            # Phase 3: Analyze & Decide Next Steps (non-blocking)
            if iteration < max_iterations:
                yield send_event("thought", "🔍 Analyzing results and deciding next steps...")

                next_decision = await asyncio.to_thread(
                    agent.analyze_and_adapt,
                    target=target,
                    user_objective=user_prompt or "General security assessment",
                    completed_tools=completed_tools,
                    tool_results=all_results
                )

                # Show analysis
                yield send_event(
                    "analysis",
                    f"**Analysis:**\n{next_decision.reasoning}\n\n**Confidence:** {next_decision.confidence_score}",
                    {"confidence": next_decision.confidence_score}
                )

                # Decision: Continue or Stop?
                if next_decision.should_continue and next_decision.next_tools:
                    yield send_event(
                        "decision",
                        f"🔄 Continuing with: {', '.join(next_decision.next_tools)}",
                        {"continue": True, "tools": next_decision.next_tools}
                    )
                    initial_decision = next_decision
                else:
                    yield send_event(
                        "decision",
                        "✅ Objective achieved. Stopping agent workflow.",
                        {"continue": False}
                    )
                    break
            else:
                yield send_event("system", "⏱️ Maximum iterations reached")
                break

        # Final: Get AI Analysis
        yield send_event("thought", "🧠 Generating final security analysis...")

        from app.services.ai_service import AIService
        ai_service = AIService(gemini_api_key)

        analysis_result = ai_service.analyze_results(
            target=target,
            results=[{"tool": k, "output": v} for k, v in all_results.items()]
        )

        if analysis_result.get('status') == 'success':
            # Save analysis to DB
            from app.models.analysis import AIAnalysis
            analysis = AIAnalysis(
                scan_id=scan.id,
                summary=analysis_result['analysis'].get('summary', ''),
                severity=analysis_result['analysis'].get('severity', 'info'),
                findings=analysis_result['analysis'].get('findings', []),
                recommendations=analysis_result['analysis'].get('recommendations', []),
                model_used=analysis_result['model_used']
            )
            db.add(analysis)

            # Update scan status
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            db.commit()

            yield send_event(
                "analysis",
                f"**Final Analysis:**\n\n{analysis_result['analysis'].get('summary', 'Analysis completed')}"
            )
            yield send_event("system", "✅ Scan completed successfully!", {"completed": True})
        else:
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            db.commit()
            yield send_event("system", "✅ Scan completed", {"completed": True})

    except Exception as e:
        import traceback
        
        error_type = type(e).__name__
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        # CRITICAL: Use BOTH logger AND print() to ensure visibility (NO EMOJIS - Windows encoding)
        print("\n" + "="*80)
        print("[ERROR] CRITICAL ERROR IN SCAN STREAM")
        print("="*80)
        print(f"Scan ID: {scan_id}")
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        print("\nFull Traceback:")
        print(error_traceback)
        print("="*80 + "\n")
        
        logger.error(f"❌ Stream error for scan {scan_id}")
        logger.error(f"   Error type: {error_type}")
        logger.error(f"   Error message: {error_msg}")
        logger.error(f"   Full traceback:\n{error_traceback}")

        # Update scan status to failed
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = ScanStatus.FAILED
                scan.error_message = f"{error_type}: {error_msg}"
                scan.completed_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Scan {scan_id} marked as FAILED in database")
        except Exception as db_error:
            logger.error(f"❌ Failed to update scan status: {str(db_error)}")

        # Send detailed error message with full context
        user_message = f"❌ **Scan Failed: {error_type}**\n\n"
        user_message += f"**Error:** {error_msg}\n\n"
        
        # Add specific guidance based on error type
        if "API" in error_msg or "key" in error_msg.lower():
            user_message += "**Possible Cause:** Invalid or expired Gemini API key\n"
            user_message += "**Solution:** Verify your API key at https://aistudio.google.com/app/apikey"
        elif "timeout" in error_msg.lower():
            user_message += "**Possible Cause:** Target is unresponsive or scan timeout exceeded\n"
            user_message += "**Solution:** Check if target is accessible and try again"
        elif "permission" in error_msg.lower():
            user_message += "**Possible Cause:** Tool not installed or insufficient permissions\n"
            user_message += "**Solution:** Run installation script or check permissions"
        elif "description" in error_msg.lower():
            user_message += "**Possible Cause:** Protobuf parsing issue with AI response\n"
            user_message += "**Solution:** This is a known issue being investigated. Please check backend logs."
        else:
            # Generic error - show more context
            user_message += "**Backend logs contain full traceback for debugging.**"
            
        yield send_event("system", user_message, {
            "error": True, 
            "error_type": error_type,
            "error_message": error_msg
        })


@router.post("/stream/create")
async def create_scan_for_streaming(
    scan_data: ScanCreate,
    db: Session = Depends(get_db),
    gemini_key: Optional[str] = Depends(get_gemini_key)
):
    """
    Create a scan and return scan_id for streaming

    Step 1: Call this endpoint to create the scan
    Step 2: Connect to GET /stream/{scan_id} for SSE stream
    """
    logger.info(f"📥 Received scan creation request for target: {scan_data.target}")
    logger.info(f"   Enable AI: {scan_data.enable_ai}")
    logger.info(f"   API key provided: {bool(gemini_key)}")
    logger.info(f"   User prompt: {scan_data.user_prompt[:50] if scan_data.user_prompt else 'None'}...")
    
    # Validate and sanitize target
    try:
        clean_target = sanitize_target(scan_data.target)
        logger.info(f"✅ Target validated: {clean_target}")
    except ValueError as e:
        logger.warning(f"⚠️ Invalid target: {str(e)}")
        raise BadRequestException(f"Invalid target: {str(e)}")

    # Check if AI is enabled but no key provided
    if scan_data.enable_ai and not gemini_key:
        logger.warning(f"⚠️ AI enabled but no API key provided")
        raise BadRequestException("Gemini API key required when AI analysis is enabled. Please provide X-Gemini-API-Key header.")

    # Validate API key format if provided
    if gemini_key and len(gemini_key.strip()) < 10:
        logger.warning(f"⚠️ API key too short (length: {len(gemini_key)})")
        raise BadRequestException("Invalid Gemini API key: key appears to be too short")

    # Only support streaming for AI Agent mode
    if not scan_data.enable_ai or not gemini_key or not scan_data.user_prompt:
        logger.warning(f"⚠️ Streaming requires AI agent mode with prompt")
        raise BadRequestException("Streaming only available for AI Agent mode with user prompt")

    # Create scan record
    scan = Scan(
        target=clean_target,
        user_prompt=scan_data.user_prompt,
        ai_strategy=None,
        agent_thoughts=None,
        tools=scan_data.tools or ['nmap'],
        profile=scan_data.profile,
        status=ScanStatus.RUNNING,
        started_at=datetime.utcnow(),
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    logger.info(f"✅ Created streaming scan {scan.id} for target: {clean_target}")

    # Start background task for agent workflow
    import asyncio
    from app.config import settings

    async def run_agent_background(scan_id: str, api_key: str):
        """Background task to run AI agent workflow with provided API key"""
        from app.db.session import SessionLocal
        from app.models.scan import Scan  # local import to avoid circular ref
        bg_db = SessionLocal()
        try:
            logger.info(f"{'='*60}")
            logger.info(f"🚀 BACKGROUND TASK STARTED: scan {scan_id}")
            logger.info(f"🛡️ Safe AI Mode: {settings.USE_SAFE_AI_MODE}")
            logger.info(f"⚡ NEW: Function Calling Architecture")
            logger.info(f"🔑 API Key: {'✅ Provided' if api_key else '❌ Missing'}")
            logger.info(f"{'='*60}")
            
            db_scan = bg_db.query(Scan).filter(Scan.id == scan_id).first()
            if not db_scan:
                logger.error(f"❌ Background agent: scan {scan_id} not found in database")
                return
            
            logger.info(f"✅ Scan found in DB: {db_scan.target}")
            logger.info(f"🤖 Starting FUNCTION CALLING agent workflow...")
            
            # USE CONTEXT-SAFE HYBRID MODE: HybridOrchestrator
            from app.core.hybrid_orchestrator import HybridOrchestrator
            from app.models.chat_message import ChatMessage
            
            logger.info(f"🎬 Starting Context-Safe Hybrid Mode agent...")
            
            # Initialize HybridOrchestrator
            orchestrator = HybridOrchestrator(gemini_api_key=api_key)
            
            # Run and save events to database for SSE streaming
            sequence = 0
            event_count = 0
            async for event in orchestrator.execute_scan(db_scan, bg_db, max_iterations=10):
                sequence += 1
                event_count += 1
                
                # Save to database so SSE endpoint can stream it
                try:
                    # Merge subtype into metadata if present
                    metadata_dict = event.get('metadata', {})
                    if 'subtype' in event:
                        metadata_dict['subtype'] = event['subtype']
                    
                    chat_msg = ChatMessage(
                        scan_id=scan_id,
                        message_type=event['type'],
                        content=event['content'],
                        sequence=sequence,
                        metadata_json=json.dumps(metadata_dict) if metadata_dict else None
                    )
                    bg_db.add(chat_msg)
                    bg_db.commit()
                    
                    # Log every event for debugging
                    if event_count <= 5 or event_count % 10 == 0:
                        logger.info(f"✅ Saved event #{sequence}: {event['type']} - {event['content'][:80]}...")
                    else:
                        logger.debug(f"✅ Saved event #{sequence}: {event['type']}")
                except Exception as save_error:
                    logger.error(f"❌ Failed to save event #{sequence}: {save_error}", exc_info=True)
                    # Continue anyway - don't break the stream
            
            logger.info(f"✅ Agent completed - Total {event_count} events saved")
            
            logger.info(f"{'='*60}")
            logger.info(f"✅ BACKGROUND TASK COMPLETED: scan {scan_id}")
            logger.info(f"{'='*60}")
        except Exception as bg_error:
            import traceback
            
            error_type = type(bg_error).__name__
            error_msg = str(bg_error)
            error_traceback = traceback.format_exc()
            
            logger.error(f"{'='*60}")
            logger.error(f"❌ BACKGROUND TASK FAILED: scan {scan_id}")
            logger.error("   Error type: %s", error_type)  # Use % to avoid f-string formatting issues
            logger.error("   Error message: %s", error_msg)  # Avoid f-string with error messages
            logger.error("   Full traceback:")
            logger.error("%s", error_traceback)  # Log traceback separately
            logger.error(f"{'='*60}")
            
            # Create comprehensive error message for database (avoid f-string formatting issues)
            detailed_error = "{}: {}".format(error_type, error_msg)  # Use .format() to avoid brace issues
            if "KeyError" in error_type:
                detailed_error += "\n\nThis appears to be a protobuf parsing issue. Check backend logs for full details."
            
            # Update scan status with detailed error
            try:
                db_scan = bg_db.query(Scan).filter(Scan.id == scan_id).first()
                if db_scan:
                    db_scan.status = ScanStatus.FAILED
                    db_scan.error_message = detailed_error
                    bg_db.commit()
                    logger.info(f"   Updated scan {scan_id} status to FAILED")
                    
                    # Also save error as chat message for SSE streaming
                    from app.models.chat_message import ChatMessage
                    error_chat = ChatMessage(
                        scan_id=scan_id,
                        message_type="system",
                        content=f"❌ **Scan Failed: {error_type}**\n\n{error_msg}\n\nCheck backend logs for full details.",
                        sequence=9999,
                        metadata_json=json.dumps({"error": True, "error_type": error_type})
                    )
                    bg_db.add(error_chat)
                    bg_db.commit()
                    logger.info(f"   Saved error message to chat history")
            except Exception as db_error:
                logger.error(f"   Failed to update scan status: {db_error}")
                pass
        finally:
            bg_db.close()
            logger.info(f"🔒 Background DB session closed for scan {scan_id}")

    # Run in background (non-blocking)
    logger.info(f"🚀 Spawning background task for scan {scan.id}")
    logger.info(f"🔑 Passing API key to background task: {bool(gemini_key)}")
    asyncio.create_task(run_agent_background(scan.id, gemini_key))
    logger.info(f"✨ Background task spawned successfully")

    # Return scan ID for streaming connection
    return {
        "scan_id": scan.id,
        "stream_url": f"/api/v1/scan/stream/{scan.id}",
        "target": clean_target,
        "status": "RUNNING"
    }


@router.get("/stream/{scan_id}")
async def get_scan_stream(
    scan_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Stream scan progress via Server-Sent Events (SSE)

    This endpoint polls the database for updates and streams them to the client.
    Works by checking scan status and results every second.
    
    CRITICAL: This uses EventSourceResponse which auto-formats data as SSE.
    Just yield JSON strings, EventSourceResponse adds "data: " prefix automatically.
    """
    logger.info(f"🌐 SSE Connection request for scan {scan_id}")
    logger.info(f"   Client: {request.client.host if request.client else 'unknown'}")
    
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        logger.error(f"❌ Scan {scan_id} not found in database")
        raise HTTPException(status_code=404, detail="Scan not found")
    
    logger.info(f"✅ Scan found: {scan.target}, status: {scan.status}")

    async def stream_scan_progress():
        """Poll database and stream updates"""
        sent_result_ids = set()
        last_status = scan.status
        
        # Import json inside function scope to avoid free variable issue
        import json as json_module

        def send_event(event_type: str, content: str, metadata: dict = None):
            """Create SSE-formatted event (NOT async - just JSON formatting)"""
            event_data = {
                "type": event_type,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            return json_module.dumps(event_data)

        # Send IMMEDIATE initial messages (EventSourceResponse auto-formats)
        # This MUST yield immediately to establish SSE connection
        logger.info(f"📡 SSE Stream opened for scan {scan_id}")
        
        try:
            yield send_event("system", f"✅ Connected to scan stream", {"scan_id": scan_id})
            logger.info("   ✓ Sent connection confirmation")
            
            yield send_event("system", f"🎯 Target: {scan.target}")
            logger.info("   ✓ Sent target info")
            
            yield send_event("thought", f"🤖 Initializing AI Agent for pentesting...")
            logger.info("   ✓ Sent initialization message")
        except Exception as e:
            logger.error(f"❌ Error sending initial SSE messages: {e}", exc_info=True)
            raise

        # If scan already completed, send summary (but only if it's an OLD scan)
        # Recent scans (< 10 seconds) might be still initializing, don't exit early
        if scan.status == ScanStatus.COMPLETED:
            scan_age_seconds = (datetime.utcnow() - scan.started_at).total_seconds()
            
            # Only treat as "already completed" if it's an old scan (> 10 seconds)
            if scan_age_seconds > 10:
                logger.info(f"Scan {scan_id} is old ({scan_age_seconds}s) and COMPLETED - sending summary")
                yield send_event("system", "✅ Scan already completed")

                # Send results summary
                from app.models.result import ScanResult
                results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()

                for result in results:
                    findings_count = len(result.findings) if result.findings else 0
                    yield send_event(
                        "output",
                        f"**{result.tool_name.upper()}** completed\n\nFindings: {findings_count}",
                        {"tool": result.tool_name, "findings": findings_count}
                    )

                yield send_event("system", "End of scan results", {"completed": True})
                return
            else:
                # Recent scan - might be race condition, proceed to polling
                logger.info(f"Scan {scan_id} is recent ({scan_age_seconds}s) and COMPLETED - waiting for background task")
                # Don't return, continue to polling loop

        # Stream live updates from chat messages
        yield send_event("thought", "🧠 AI Agent starting...")

        # NEW: Poll chat_messages table for real-time events
        from app.models.chat_message import ChatMessage
        from app.models.result import ScanResult
        
        poll_count = 0
        max_polls = 360  # 6 minutes max (with adaptive polling)
        last_message_sequence = 0
        poll_interval = 0.5  # Start with 0.5s polling
        messages_since_last_poll = 0
        
        while poll_count < max_polls:
            poll_count += 1
            
            # Refresh scan from DB
            db.refresh(scan)
            
            # Check for NEW chat messages (PRIORITY!)
            new_messages = db.query(ChatMessage).filter(
                ChatMessage.scan_id == scan_id,
                ChatMessage.sequence > last_message_sequence
            ).order_by(ChatMessage.sequence.asc()).all()
            
            if new_messages:
                messages_since_last_poll = len(new_messages)
                # Fast polling when active (0.3s)
                poll_interval = 0.3
                
                for msg in new_messages:
                    logger.info(f"📡 Streaming chat message: {msg.message_type} - {msg.content[:50]}...")
                    
                    # Map message_type to event_type
                    event_type_map = {
                        'system': 'system',
                        'thought': 'thought',
                        'plan': 'plan',
                        'tool': 'tool',
                        'output': 'output',
                        'function_call': 'tool',
                        'function_result': 'output',
                        'analysis': 'analysis',
                        'decision': 'decision'
                    }
                    
                    event_type = event_type_map.get(msg.message_type, 'system')
                    
                    # Parse metadata if exists
                    metadata = {}
                    if msg.metadata_json:
                        try:
                            metadata = json_module.loads(msg.metadata_json)
                        except Exception as parse_error:
                            logger.warning(f"Failed to parse metadata JSON: {parse_error}")
                            pass
                    
                    yield send_event(event_type, msg.content, metadata)
                    last_message_sequence = msg.sequence
            else:
                # Slow down polling when idle (adaptive: 0.5s -> 1s -> 2s max)
                messages_since_last_poll = 0
                poll_interval = min(poll_interval * 1.2, 2.0)  # Max 2s
            
            # Send keepalive only if no new messages
            if not new_messages and poll_count % 20 == 0:
                elapsed = poll_count
                yield send_event("system", f"⏳ AI Agent working... ({elapsed}s elapsed)", {"keepalive": True, "elapsed": elapsed})
                logger.debug(f"📡 Keepalive sent for scan {scan_id} ({elapsed}s)")

            # DISABLED: Database result streaming (was causing duplicates)
            # HybridOrchestrator sends all events via chat_messages in real-time
            # This legacy code was streaming database results creating duplicates (RUN_X + X)
            
            # Check for scan completion (query results but don't stream them)
            results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()

            # DISABLED LOOP - no longer streaming database results
            if False and result in results:  # Disabled
                if result.id not in sent_result_ids:
                    sent_result_ids.add(result.id)

                    # Send tool execution start
                    yield send_event("tool", f"⚡ Executing {result.tool_name.upper()}...")

                    # Wait a bit (simulate real-time feeling)
                    await asyncio.sleep(0.5)

                    parsed_output = result.parsed_output or {}
                    findings_count = 0
                    findings_preview = None

                    if isinstance(parsed_output, dict):
                        findings_data = parsed_output.get("findings")
                        if isinstance(findings_data, list):
                            findings_count = len(findings_data)
                            if findings_data:
                                preview_items = findings_data[:3]
                                findings_preview = "\n".join(
                                    [
                                        f"• {item.get('title') or item.get('template_id') or item.get('port') or 'Finding'}"
                                        if isinstance(item, dict)
                                        else f"• {str(item)}"
                                        for item in preview_items
                                    ]
                                )
                        elif isinstance(findings_data, dict):
                            # Some parsers return severity counts
                            findings_count = sum(
                                value for value in findings_data.values()
                                if isinstance(value, (int, float))
                            )

                    status_label = "success" if result.exit_code == 0 else "error"
                    
                    # Calculate progress based on completed results
                    total_results = len(results)
                    all_planned_tools = set(scan.tools if scan.tools else ['nmap'])
                    progress_percentage = int((total_results / max(len(all_planned_tools), 1)) * 100)

                    # Send tool result with progress
                    yield send_event(
                        "output",
                        f"✅ {result.tool_name.upper()} completed\n\n**Status:** {status_label}\n**Findings:** {findings_count}",
                        {
                            "tool": result.tool_name, 
                            "status": status_label, 
                            "findings": findings_count,
                            "progress": progress_percentage,
                            "completed": total_results,
                            "total": len(all_planned_tools)
                        }
                    )

                    # Show key findings
                    if findings_preview:
                        yield send_event("output", f"**Key Findings:**\n{findings_preview}")

            # Check status change
            if scan.status != last_status:
                if scan.status == ScanStatus.COMPLETED:
                    yield send_event("system", "✅ Scan completed successfully!", {"completed": True})

                    # Send final analysis if available
                    if scan.analysis:
                        yield send_event(
                            "analysis",
                            f"**Final Analysis:**\n\n{scan.analysis.summary[:500]}..."
                        )

                    break
                elif scan.status == ScanStatus.FAILED:
                    yield send_event("system", f"❌ Scan failed: {scan.error_message or 'Unknown error'}", {"error": True})
                    break

                last_status = scan.status

            # Stop if scan is no longer running
            if scan.status not in [ScanStatus.RUNNING, ScanStatus.PENDING]:
                break

            # Adaptive polling interval (faster when active, slower when idle)
            await asyncio.sleep(poll_interval)

        # Check if we timed out
        if poll_count >= max_polls:
            yield send_event("system", "⏱️ Scan timeout - please check results manually", {"timeout": True})
        else:
            yield send_event("system", "Stream ended", {"completed": True})
        
        logger.info(f"📡 SSE Stream closed for scan {scan_id}")

    # Return SSE response with keepalive pings every 15 seconds
    return EventSourceResponse(
        stream_scan_progress(),
        ping=15,  # Send ping every 15s to keep connection alive
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
