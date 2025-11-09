"""
Orchestrator for AI Agent workflow
Handles the iterative agent loop: Plan → Execute → Observe → Refine
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.services.ai_agent import AIAgent, AgentDecision
from app.services.persistence_manager import PersistenceManager
from app.tools.factory import ToolFactory
from app.utils.logger import logger
from datetime import datetime
import asyncio


class AgentOrchestrator:
    """
    Manages the full agent workflow:
    1. Initial planning based on user objective
    2. Execute selected tools
    3. Analyze results
    4. Decide next steps (continue or stop)
    5. Repeat until objective met or no more value
    """

    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.agent = None  # Will be initialized async

    async def run_agent_workflow(
        self,
        scan: Scan,
        db: Session
    ) -> Dict[str, Any]:
        """
        Main agent loop - runs until completion or max iterations
        """
        max_iterations = 3  # Prevent infinite loops
        iteration = 0

        completed_tools = []
        all_results = {}

        logger.info(f"🤖 Starting AI Agent workflow for scan {scan.id}")
        logger.info(f"📝 User objective: {scan.user_prompt}")

        # Initialize Persistence Manager for dual-write pattern
        persistence = PersistenceManager(scan, db)

        try:
            # Initialize AI Agent (async, non-blocking)
            logger.info("🔧 Initializing AI Agent...")
            persistence.log_agent_thought(
                "🤖 Connecting to Google Gemini AI...",
                {"phase": "init", "step": "connecting"}
            )
            
            self.agent = await asyncio.to_thread(AIAgent, self.gemini_api_key)
            logger.info("✅ AI Agent initialized")
            
            persistence.log_agent_thought(
                "✅ AI Agent connected successfully",
                {"phase": "init", "step": "connected"}
            )
            await asyncio.sleep(0.5)  # Give frontend time to show message
            
            # Phase 1: Initial Planning (async, non-blocking)
            logger.info("🧠 Phase 1: Initial Strategic Planning")
            persistence.log_agent_thought(
                "🧠 AI analyzing target and planning attack strategy...",
                {"phase": "planning", "step": "analyzing"}
            )
            
            initial_decision = await asyncio.to_thread(
                self.agent.initial_planning,
                target=scan.target,
                user_objective=scan.user_prompt or "General security assessment"
            )

            if not initial_decision.next_tools:
                logger.warning("Agent returned no initial tools, falling back to nmap")
                initial_decision.next_tools = ["nmap"]

            logger.info(f"✅ Agent decided to use: {initial_decision.next_tools}")
            logger.info(f"💭 Reasoning: {initial_decision.reasoning[:200]}...")

            # Store initial strategy
            scan.ai_strategy = {
                'tools_selected': initial_decision.next_tools,
                'reasoning': initial_decision.reasoning,
                'confidence': initial_decision.confidence_score
            }
            scan.tools = initial_decision.next_tools
            
            # Log AI's strategic reasoning (DUAL-WRITE)
            strategy_message = f"🧠 **AI Strategy:**\n\n{initial_decision.reasoning[:300]}...\n\n**Selected Tools:** {', '.join(initial_decision.next_tools)}"
            persistence.log_agent_thought(
                strategy_message,
                {
                    "phase": "planning", 
                    "step": "strategy_ready",
                    "tools": initial_decision.next_tools,
                    "reasoning": initial_decision.reasoning,
                    "confidence": initial_decision.confidence_score
                }
            )
            await asyncio.sleep(1.2)  # Let frontend display full strategy

            # Agent Loop: Execute → Observe → Refine
            while iteration < max_iterations and initial_decision.next_tools:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 Iteration {iteration}/{max_iterations}")
                logger.info(f"{'='*60}")

                # Get tools to execute this iteration
                tools_to_run = initial_decision.next_tools

                # Phase 2: Execute Tools
                logger.info(f"⚙️ Phase 2: Executing tools: {tools_to_run}")
                for tool in tools_to_run:
                    if tool in completed_tools:
                        logger.info(f"⏭️ Skipping {tool} (already executed)")
                        continue

                    logger.info(f"🔧 Running {tool}...")
                    
                    # Log tool execution start (DUAL-WRITE)
                    tool_instance = ToolFactory.get_tool(tool)
                    persistence.log_tool_execution_start(
                        tool_name=tool,
                        target=scan.target,
                        command=f"{tool} {scan.target}"
                    )

                    # Execute tool and get result (async, non-blocking)
                    start_time = datetime.utcnow()
                    tool_result = await asyncio.to_thread(tool_instance.execute, scan.target, scan.profile)
                    execution_time = (datetime.utcnow() - start_time).total_seconds()

                    # Save result to database (via persistence manager)
                    scan_result = persistence.save_tool_result(
                        tool_name=tool,
                        raw_output=tool_result.stdout,
                        parsed_output=tool_result.parsed_data,
                        exit_code=tool_result.exit_code,
                        execution_time=execution_time,
                        error_message=tool_result.stderr if tool_result.exit_code != 0 else None,
                        command_executed=f"{tool} {scan.target}"
                    )

                    # Store parsed data for AI analysis
                    if tool_result.parsed_data:
                        all_results[tool] = tool_result.parsed_data
                    else:
                        all_results[tool] = {
                            'raw_output': tool_result.stdout[:500],
                            'exit_code': tool_result.exit_code
                        }

                    completed_tools.append(tool)
                    logger.info(f"✅ {tool} completed in {execution_time:.2f}s")
                    
                    # Extract and save vulnerabilities
                    vuln_count = persistence.extract_and_save_vulnerabilities(scan_result, tool)
                    
                    # Update progress with completion AND tool output summary
                    findings_count = len(tool_result.parsed_data.get('findings', [])) if tool_result.parsed_data else 0
                    
                    # Create human-readable output summary
                    output_preview = ""
                    if tool_result.parsed_data and isinstance(tool_result.parsed_data, dict):
                        if 'findings' in tool_result.parsed_data and findings_count > 0:
                            findings = tool_result.parsed_data['findings'][:3]  # Top 3
                            output_preview = "\n\n**Key Findings:**\n"
                            for idx, finding in enumerate(findings, 1):
                                if isinstance(finding, dict):
                                    title = finding.get('template_id') or finding.get('port') or finding.get('info', {}).get('name') or 'Finding'
                                    output_preview += f"{idx}. {title}\n"
                    elif tool_result.stdout:
                        output_preview = f"\n\n**Output preview:**\n```\n{tool_result.stdout[:200]}\n```"
                    
                    # Log tool completion (DUAL-WRITE)
                    persistence.log_tool_execution_complete(
                        tool_name=tool,
                        duration=execution_time,
                        findings_count=findings_count,
                        summary=output_preview
                    )
                    await asyncio.sleep(0.5)  # Let frontend display results

                # Phase 3: Analyze and Decide Next Steps
                logger.info(f"\n🧠 Phase 3: Analyzing results and planning next steps")
                persistence.log_agent_thought(
                    "🧠 AI analyzing scan results...",
                    {
                        "phase": "analysis",
                        "completed_tools": completed_tools,
                        "iteration": iteration
                    }
                )

                decision = await asyncio.to_thread(
                    self.agent.analyze_and_adapt,
                    target=scan.target,
                    user_objective=scan.user_prompt or "General security assessment",
                    completed_tools=completed_tools,
                    tool_results=all_results
                )

                if decision.continue_scan and not decision.next_tools:
                    logger.warning("Agent chose to continue without selecting tools; defaulting to nmap")
                    decision.next_tools = [tool for tool in ['nmap', 'nuclei', 'whatweb', 'sslscan'] if tool not in completed_tools][:1] or ['nmap']

                logger.info(f"📊 Continue scanning: {decision.continue_scan}")
                logger.info(f"💭 Agent reasoning: {decision.reasoning[:200]}...")
                logger.info(f"📈 Confidence score: {decision.confidence_score:.2f}")

                # Store thought process
                scan.agent_thoughts = self.agent.get_thought_process()
                
                # Send AI's analysis and decision to frontend (DUAL-WRITE)
                decision_msg = "🧠 **AI ANALYSIS:**\n\n"
                decision_msg += f"{decision.reasoning[:400]}\n\n"
                decision_msg += f"**Continue Scanning:** {'Yes' if decision.continue_scan else 'No'}\n"
                decision_msg += f"**Confidence:** {decision.confidence_score:.0%}"
                
                persistence.log_agent_thought(
                    decision_msg,
                    {
                        "phase": "decision",
                        "continue": decision.continue_scan,
                        "confidence": decision.confidence_score,
                        "reasoning": decision.reasoning,
                        "next_tools": decision.next_tools if decision.continue_scan else []
                    }
                )
                await asyncio.sleep(1.0)  # Let user read AI's thinking

                # Check if should continue
                if not decision.continue_scan:
                    logger.info("🎯 Agent decided to stop: Objective met or no more value")
                    persistence.log_agent_thought(
                        "🎯 AI decided objective is met - Finalizing results...",
                        {"phase": "completion", "reason": "objective_met"}
                    )
                    break

                if not decision.next_tools:
                    logger.info("🎯 No more tools needed")
                    break

                # Prepare for next iteration
                initial_decision = decision

                logger.info(f"➡️ Next tools: {decision.next_tools}")

            # Finalize scan with summary (DUAL-WRITE)
            total_findings = sum(len(r.get('findings', [])) if isinstance(r, dict) else 0 for r in all_results.values())
            persistence.finalize_scan(
                completed_tools=completed_tools,
                total_findings=total_findings,
                iterations=iteration
            )
            persistence.update_scan_status(ScanStatus.COMPLETED)

            # Final summary
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Agent workflow completed after {iteration} iterations")
            logger.info(f"🔧 Tools executed: {', '.join(completed_tools)}")
            logger.info(f"🧠 Total thoughts: {len(self.agent.thoughts)}")
            logger.info(f"{'='*60}\n")

            return {
                'success': True,
                'iterations': iteration,
                'completed_tools': completed_tools,
                'results': all_results,
                'thought_process': self.agent.get_thought_process()
            }

        except Exception as e:
            import traceback
            
            # CRITICAL: Print to console for immediate visibility (NO EMOJIS - Windows encoding)
            print("\n" + "="*80)
            print("[ERROR] CRITICAL ERROR IN AGENT ORCHESTRATOR")
            print("="*80)
            print(f"Scan ID: {scan.id}")
            print(f"Target: {scan.target}")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print("\nFull Traceback:")
            print(traceback.format_exc())
            print("="*80 + "\n")
            
            logger.error(f"❌ Agent workflow failed: {str(e)}", exc_info=True)
            
            # Mark scan as failed
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.progress_message = f"❌ Scan failed: {str(e)[:100]}"
            scan.progress_metadata = {
                "phase": "failed",
                "error": str(e),
                "completed_tools": completed_tools
            }
            scan.completed_at = datetime.utcnow()
            db.commit()

            return {
                'success': False,
                'error': str(e),
                'completed_tools': completed_tools,
                'results': all_results
            }
