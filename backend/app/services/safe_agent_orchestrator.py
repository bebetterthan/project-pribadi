"""
Safe Agent Orchestrator - Uses 2-Phase approach for AI safety
Phase 1: Abstract planning (no target info)
Phase 2: Concrete execution with sanitized feedback
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.services.ai_planner_v2 import SafeAIPlanner, SafeAIAnalyzer
from app.tools.factory import ToolFactory
from app.utils.logger import logger
from app.utils.target_sanitizer import TargetSanitizer
from datetime import datetime
import asyncio


class SafeAgentOrchestrator:
    """
    Safe orchestrator that separates abstract planning from concrete execution
    AI never sees real target names - only abstract strategies
    """
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.planner = SafeAIPlanner(gemini_api_key)
        self.analyzer = SafeAIAnalyzer(gemini_api_key)
    
    async def run_safe_workflow(self, scan: Scan, db: Session) -> Dict[str, Any]:
        """
        Execute safe agent workflow with 2-phase approach
        
        Phase 1: AI creates abstract assessment plan (no target)
        Phase 2: Backend executes tools and sanitizes results for AI analysis
        """
        logger.info(f"🛡️ Starting SAFE agent workflow for scan {scan.id}")
        logger.info(f"📝 User objective: {scan.user_prompt}")
        logger.info(f"🎯 Target: {scan.target} (will be hidden from AI)")
        
        completed_tools = []
        all_results = {}
        sanitizer = TargetSanitizer(scan.target)
        
        try:
            # === PHASE 1: ABSTRACT PLANNING (No Target Info) ===
            logger.info("\n" + "="*60)
            logger.info("🧠 PHASE 1: SAFE AI PLANNING (Abstract)")
            logger.info("="*60)
            
            scan.progress_message = "🤖 Consulting AI security advisor (safe mode)..."
            scan.progress_metadata = {"phase": "init", "step": "connecting"}
            db.commit()
            
            # Get abstract plan (AI doesn't know target)
            plan = await asyncio.to_thread(
                self.planner.create_assessment_plan,
                user_objective=scan.user_prompt or "General security assessment"
            )
            
            logger.info(f"✅ AI Plan received: {plan.recommended_tools}")
            logger.info(f"💭 Rationale: {plan.tool_order_rationale}")
            
            # Store strategy
            scan.ai_strategy = {
                'objective': plan.objective,
                'recommended_tools': plan.recommended_tools,
                'rationale': plan.tool_order_rationale,
                'expected_findings': plan.expected_finding_types,
                'confidence': plan.confidence
            }
            scan.tools = plan.recommended_tools
            
            # Send AI reasoning to frontend
            strategy_msg = "🧠 **AI SECURITY ASSESSMENT STRATEGY:**\n\n"
            strategy_msg += f"{plan.tool_order_rationale}\n\n"
            strategy_msg += f"**Recommended Tools:** {', '.join(plan.recommended_tools)}\n"
            strategy_msg += f"**Expected Findings:** {', '.join(plan.expected_finding_types[:3])}\n"
            strategy_msg += f"**Confidence:** {plan.confidence:.0%}"
            
            scan.progress_message = strategy_msg
            scan.progress_metadata = {
                "phase": "planning",
                "step": "strategy_ready",
                "tools": plan.recommended_tools,
                "confidence": plan.confidence
            }
            db.commit()
            await asyncio.sleep(1.5)  # Let frontend display
            
            # === PHASE 2: CONCRETE EXECUTION ===
            logger.info("\n" + "="*60)
            logger.info(f"🔧 PHASE 2: TOOL EXECUTION (Against {scan.target})")
            logger.info("="*60)
            
            for tool_name in plan.recommended_tools:
                logger.info(f"\n🔧 Executing {tool_name} against {scan.target}")
                
                # Update progress
                scan.current_tool = tool_name
                scan.progress_message = f"⚡ Executing {tool_name.upper()} against target..."
                scan.progress_metadata = {
                    "phase": "execution",
                    "tool": tool_name,
                    "target_hidden": True  # Flag that target is hidden from AI
                }
                db.commit()
                
                try:
                    # Get tool instance
                    tool = ToolFactory.get_tool(tool_name)
                    if not tool:
                        logger.warning(f"⚠️ Tool {tool_name} not available")
                        continue
                    
                    # Execute tool
                    start_time = datetime.utcnow()
                    result = await asyncio.to_thread(
                        tool.execute,
                        scan.target,
                        scan.profile
                    )
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    logger.info(f"✅ {tool_name} completed in {execution_time:.2f}s")
                    
                    # Save to database
                    scan_result = ScanResult(
                        scan_id=scan.id,
                        tool_name=tool_name,
                        raw_output=result.stdout,
                        parsed_output=result.parsed_data,
                        exit_code=result.exit_code,
                        execution_time=execution_time,
                        error_message=result.stderr if result.exit_code != 0 else None
                    )
                    db.add(scan_result)
                    db.commit()
                    
                    # Store results
                    completed_tools.append(tool_name)
                    all_results[tool_name] = result.parsed_data
                    
                    # Create sanitized preview for user (NOT for AI yet)
                    findings_count = 0
                    if result.parsed_data and isinstance(result.parsed_data, dict):
                        findings_count = len(result.parsed_data.get('findings', []))
                    
                    completion_msg = f"✅ **{tool_name.upper()} COMPLETED**\n\n"
                    completion_msg += f"**Status:** {'Success' if result.exit_code == 0 else 'Error'}\n"
                    completion_msg += f"**Findings:** {findings_count}\n"
                    completion_msg += f"**Time:** {execution_time:.1f}s"
                    
                    scan.progress_message = completion_msg
                    scan.progress_metadata = {
                        "phase": "execution",
                        "tool": tool_name,
                        "status": "completed",
                        "findings": findings_count,
                        "execution_time": execution_time
                    }
                    db.commit()
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"❌ Tool {tool_name} failed: {e}")
                    scan.progress_message = f"❌ {tool_name} failed: {str(e)[:100]}"
                    db.commit()
            
            # === PHASE 3: SAFE AI ANALYSIS (Sanitized Results) ===
            logger.info("\n" + "="*60)
            logger.info("🧠 PHASE 3: SAFE AI ANALYSIS (Sanitized)")
            logger.info("="*60)
            
            scan.progress_message = "🧠 AI analyzing results (safe mode)..."
            scan.progress_metadata = {"phase": "analysis", "sanitized": True}
            db.commit()
            
            # Sanitize results before sending to AI
            sanitized_summary = sanitizer.create_summary(all_results)
            logger.info("📄 Created sanitized summary for AI")
            logger.debug(f"Summary preview: {sanitized_summary[:200]}...")
            
            # Get AI analysis (with sanitized data)
            analysis = await asyncio.to_thread(
                self.analyzer.analyze_results,
                objective=scan.user_prompt or "General assessment",
                completed_tools=completed_tools,
                sanitized_results={'summary': sanitized_summary}
            )
            
            logger.info(f"✅ AI Analysis: objective_met={analysis.get('objective_met')}")
            
            # Send analysis to frontend
            analysis_msg = "🧠 **AI ANALYSIS:**\n\n"
            analysis_msg += f"{analysis.get('reasoning', 'Analysis complete')}\n\n"
            analysis_msg += f"**Objective Met:** {'✅ Yes' if analysis.get('objective_met') else '⏳ Partial'}\n"
            
            if analysis.get('recommendations'):
                analysis_msg += f"\n**Recommendations:**\n"
                for rec in analysis['recommendations'][:3]:
                    analysis_msg += f"• {rec}\n"
            
            scan.progress_message = analysis_msg
            scan.progress_metadata = {
                "phase": "analysis",
                "objective_met": analysis.get('objective_met'),
                "recommendations": analysis.get('recommendations', [])
            }
            db.commit()
            await asyncio.sleep(1.2)
            
            # Mark complete
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.current_tool = None
            scan.progress_message = f"✅ Scan completed! Executed {len(completed_tools)} tools successfully."
            scan.progress_metadata = {
                "phase": "completed",
                "tools_executed": completed_tools,
                "total_findings": sum(
                    len(r.get('findings', [])) if isinstance(r, dict) else 0
                    for r in all_results.values()
                )
            }
            db.commit()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ SAFE workflow completed: {len(completed_tools)} tools executed")
            logger.info(f"{'='*60}\n")
            
            return {
                'success': True,
                'tools_executed': completed_tools,
                'results': all_results,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Safe workflow failed: {e}", exc_info=True)
            
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.progress_message = f"❌ Scan failed: {str(e)[:100]}"
            scan.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'tools_executed': completed_tools
            }

