"""
Chain Orchestrator - Phase 3, Days 7-8
Master coordinator that integrates ALL Phase 1 & 2 components for intelligent tool chaining
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.core.scan_context_manager import ScanContextManager
from app.core.tool_dependency import DependencyResolver, ToolName
from app.core.parameter_builder import ParameterBuilderFactory, build_tool_parameters
from app.core.ai_reasoning import AIReasoningManager, ReasoningTrigger
from app.tools.function_toolbox import ToolExecutor
from app.utils.logger import logger


class ChainOrchestrator:
    """
    Master orchestrator that brings together:
    - Scan Context Manager (Phase 1): Data sharing between tools
    - Dependency Resolver (Phase 1): Execution order management  
    - Parameter Builder (Phase 1): Dynamic command construction
    - AI Reasoning Manager (Phase 2): Strategic decision-making
    
    This enables TRUE tool chaining where:
    - Each tool can access findings from previous tools
    - AI reasons about findings and suggests next steps
    - Parameters are optimized based on discovered data
    - Scan adapts strategy dynamically
    """
    
    def __init__(self, gemini_api_key: str, db_session: Session):
        """
        Initialize chain orchestrator.
        
        Args:
            gemini_api_key: Gemini API key for AI reasoning
            db_session: SQLAlchemy database session
        """
        self.api_key = gemini_api_key
        self.db = db_session
        
        # Initialize all Phase 1 & 2 components
        self.context_manager = ScanContextManager(db_session)
        self.dependency_resolver = DependencyResolver()
        self.ai_reasoning = AIReasoningManager(gemini_api_key)
        
        logger.info("ChainOrchestrator initialized with all components")
    
    async def execute_scan(
        self,
        scan: Scan,
        event_stream: Optional[AsyncGenerator] = None
    ) -> Dict[str, Any]:
        """
        Execute scan with intelligent tool chaining.
        
        Args:
            scan: Scan model instance
            event_stream: Optional SSE event stream for real-time updates
            
        Returns:
            Dictionary with execution results
        """
        scan_id = scan.id
        target = scan.target
        
        logger.info(f"[CHAIN] Starting intelligent scan for {target}")
        
        try:
            # ================================================================
            # PHASE 1: INITIALIZATION
            # ================================================================
            
            await self._emit_event(event_stream, {
                "type": "phase",
                "phase": "initialization",
                "message": "Initializing scan context and AI reasoning"
            })
            
            # Initialize scan context
            self.context_manager.initialize_scan(
                scan_id=scan_id,
                target=target,
                metadata={"user_prompt": scan.user_prompt}
            )
            
            logger.info(f"[CHAIN] Scan context initialized")
            
            # ================================================================
            # PHASE 2: AI INITIAL STRATEGY
            # ================================================================
            
            await self._emit_event(event_stream, {
                "type": "phase",
                "phase": "strategy",
                "message": "AI analyzing target and planning strategy"
            })
            
            # Get AI's initial strategy
            strategy = await asyncio.to_thread(
                self.ai_reasoning.get_initial_strategy,
                target=target,
                user_prompt=scan.user_prompt,
                available_tools=scan.tools if scan.tools else None
            )
            
            # Store strategy in scan
            scan.ai_strategy = {
                'analysis': strategy['analysis'],
                'recommended_tools': strategy['recommended_tools'],
                'reasoning': strategy['reasoning']
            }
            self.db.commit()
            
            # Emit reasoning to user
            await self._emit_event(event_stream, {
                "type": "reasoning",
                "trigger": "initial_strategy",
                "content": strategy['reasoning'],
                "metadata": {
                    "recommended_tools": strategy['recommended_tools'],
                    "execution_order": strategy.get('execution_order', [])
                }
            })
            
            logger.info(f"[CHAIN] AI Strategy: {strategy['recommended_tools']}")
            
            # Get execution order from dependency resolver
            tools_to_execute = strategy['recommended_tools']
            execution_levels = self.dependency_resolver.get_execution_order(tools_to_execute)
            
            logger.info(f"[CHAIN] Execution order: {execution_levels}")
            
            # ================================================================
            # PHASE 3: TOOL EXECUTION LOOP
            # ================================================================
            
            completed_tools = []
            all_results = {}
            
            for level_idx, tool_group in enumerate(execution_levels, 1):
                await self._emit_event(event_stream, {
                    "type": "phase",
                    "phase": f"execution_level_{level_idx}",
                    "message": f"Executing Level {level_idx} tools: {', '.join(tool_group)}"
                })
                
                # Execute tools in this level (can be parallel)
                for tool_name in tool_group:
                    result = await self._execute_single_tool(
                        tool_name, scan, scan_id, target, event_stream
                    )
                    
                    if result['success']:
                        completed_tools.append(tool_name)
                        all_results[tool_name] = result['data']
                        
                        # AI analyzes tool results
                        analysis = await self._analyze_tool_results(
                            tool_name, result['data'], scan_id, event_stream
                        )
                        
                        # Check if should adjust strategy
                        if analysis.get('significance') == 'critical':
                            await self._handle_critical_finding(
                                analysis, scan_id, event_stream
                            )
                    else:
                        logger.warning(f"[CHAIN] Tool {tool_name} failed: {result.get('error')}")
            
            # ================================================================
            # PHASE 4: FINAL ASSESSMENT
            # ================================================================
            
            await self._emit_event(event_stream, {
                "type": "phase",
                "phase": "assessment",
                "message": "Generating final security assessment"
            })
            
            # AI generates final assessment
            assessment = await asyncio.to_thread(
                self.ai_reasoning.generate_final_assessment,
                self.context_manager,
                scan_id,
                target
            )
            
            # Emit final assessment
            await self._emit_event(event_stream, {
                "type": "reasoning",
                "trigger": "final_assessment",
                "content": assessment['executive_summary'],
                "metadata": {
                    "risk_assessment": assessment['risk_assessment'],
                    "key_findings": assessment['key_findings'],
                    "recommendations": assessment['recommendations']
                }
            })
            
            # Update scan status
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"[CHAIN] Scan completed successfully")
            
            return {
                'success': True,
                'completed_tools': completed_tools,
                'statistics': self.context_manager.get_scan_statistics(scan_id),
                'assessment': assessment
            }
            
        except Exception as e:
            logger.error(f"[CHAIN] Scan failed: {e}", exc_info=True)
            
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            self.db.commit()
            
            await self._emit_event(event_stream, {
                "type": "error",
                "message": f"Scan failed: {str(e)}"
            })
            
            return {
                'success': False,
                'error': str(e),
                'completed_tools': []
            }
    
    async def _execute_single_tool(
        self,
        tool_name: str,
        scan: Scan,
        scan_id: str,
        target: str,
        event_stream: Optional[AsyncGenerator]
    ) -> Dict[str, Any]:
        """Execute a single tool with intelligent parameter building"""
        
        logger.info(f"[CHAIN] Executing {tool_name}")
        
        try:
            # Check dependencies
            ready, reason = self.dependency_resolver.check_dependencies_met(
                tool_name, self.context_manager, scan_id
            )
            
            if not ready:
                skip, skip_reason = self.dependency_resolver.should_skip_tool(
                    tool_name, self.context_manager, scan_id
                )
                
                if skip:
                    logger.info(f"[CHAIN] Skipping {tool_name}: {skip_reason}")
                    await self._emit_event(event_stream, {
                        "type": "tool_skipped",
                        "tool": tool_name,
                        "reason": skip_reason
                    })
                    return {'success': False, 'skipped': True}
            
            # Build parameters based on scan context
            params = await asyncio.to_thread(
                build_tool_parameters,
                tool_name,
                self.context_manager,
                scan_id,
                target
            )
            
            # Check if tool should be skipped due to no data
            if params.get('skip'):
                logger.info(f"[CHAIN] Skipping {tool_name}: {params['reasoning']}")
                await self._emit_event(event_stream, {
                    "type": "tool_skipped",
                    "tool": tool_name,
                    "reason": params['reasoning']
                })
                return {'success': False, 'skipped': True}
            
            # Emit tool start with reasoning
            await self._emit_event(event_stream, {
                "type": "tool_start",
                "tool": tool_name,
                "reasoning": params['reasoning'],
                "targets": len(params.get('target_hosts', []))
            })
            
            # Execute tool with optimized parameters
            executor = ToolExecutor(
                real_target=target,
                scan_id=scan_id,
                db_session=self.db,
                tool_results={}  # Will be populated from context if needed
            )
            
            # Get function for this tool
            tool_func = getattr(executor, f"_exec_{tool_name}", None)
            if not tool_func:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            start_time = datetime.utcnow()
            
            # Execute (this is async-compatible)
            result = await asyncio.to_thread(tool_func, params.get('target_hosts', [target])[0])
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store results in scan context based on tool type
            await self._store_tool_findings(tool_name, result, scan_id)
            
            # Emit completion
            await self._emit_event(event_stream, {
                "type": "tool_complete",
                "tool": tool_name,
                "duration": execution_time,
                "status": result.get('status', 'unknown')
            })
            
            logger.info(f"[CHAIN] {tool_name} completed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'data': result,
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"[CHAIN] Tool {tool_name} failed: {e}", exc_info=True)
            
            await self._emit_event(event_stream, {
                "type": "tool_error",
                "tool": tool_name,
                "error": str(e)
            })
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _store_tool_findings(
        self,
        tool_name: str,
        result: Dict[str, Any],
        scan_id: str
    ):
        """Store tool findings in scan context based on tool type"""
        
        from app.models.scan_context import FindingType
        
        findings = []
        finding_type = None
        
        # Map tool to finding type and extract findings
        if tool_name == 'subfinder':
            finding_type = FindingType.SUBDOMAIN
            if 'subdomains' in result:
                findings = [{'subdomain': sd} for sd in result['subdomains']] if isinstance(result['subdomains'], list) else []
        
        elif tool_name == 'httpx':
            finding_type = FindingType.HTTP_SERVICE
            if 'discovered_paths' in result:
                findings = [{'url': path} for path in result['discovered_paths']]
        
        elif tool_name == 'nmap':
            finding_type = FindingType.PORT
            if 'open_ports' in result:
                findings = result['open_ports'] if isinstance(result['open_ports'], list) else []
        
        elif tool_name == 'nuclei':
            finding_type = FindingType.VULNERABILITY
            if 'findings' in result:
                findings = result['findings'] if isinstance(result['findings'], list) else []
        
        elif tool_name == 'whatweb':
            finding_type = FindingType.TECHNOLOGY
            if 'technologies' in result:
                findings = result['technologies'] if isinstance(result['technologies'], list) else []
        
        # Store findings in context
        if findings and finding_type:
            await asyncio.to_thread(
                self.context_manager.add_findings,
                scan_id, tool_name, finding_type, findings
            )
            logger.info(f"[CHAIN] Stored {len(findings)} {finding_type.value} findings")
    
    async def _analyze_tool_results(
        self,
        tool_name: str,
        result: Dict[str, Any],
        scan_id: str,
        event_stream: Optional[AsyncGenerator]
    ) -> Dict[str, Any]:
        """AI analyzes tool results and provides insights"""
        
        analysis = await asyncio.to_thread(
            self.ai_reasoning.analyze_tool_results,
            tool_name, result, self.context_manager, scan_id
        )
        
        # Emit AI analysis
        await self._emit_event(event_stream, {
            "type": "reasoning",
            "trigger": "tool_analysis",
            "tool": tool_name,
            "content": analysis['interpretation'],
            "metadata": {
                "significance": analysis['significance'],
                "next_actions": analysis['next_actions']
            }
        })
        
        return analysis
    
    async def _handle_critical_finding(
        self,
        analysis: Dict[str, Any],
        scan_id: str,
        event_stream: Optional[AsyncGenerator]
    ):
        """Handle critical findings with special AI guidance"""
        
        # Get critical vulnerability details from context
        critical_vulns = self.context_manager.get_vulnerabilities(scan_id, 'critical')
        
        if critical_vulns:
            guidance = await asyncio.to_thread(
                self.ai_reasoning.respond_to_critical_finding,
                critical_vulns[0], self.context_manager, scan_id
            )
            
            await self._emit_event(event_stream, {
                "type": "critical_alert",
                "content": guidance['impact_assessment'],
                "metadata": {
                    "priority": guidance['priority'],
                    "remediation": guidance['remediation']
                }
            })
    
    async def _emit_event(
        self,
        event_stream: Optional[AsyncGenerator],
        event_data: Dict[str, Any]
    ):
        """Emit event to SSE stream if available"""
        if event_stream is not None:
            try:
                # In actual implementation, this would yield to the stream
                # For now, just log
                logger.debug(f"[SSE] {event_data['type']}: {event_data.get('message', '')}")
            except Exception as e:
                logger.warning(f"Failed to emit event: {e}")

