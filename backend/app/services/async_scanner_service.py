"""
Async Scanner Service - Parallel Tool Execution
Runs multiple pentesting tools concurrently for better performance
"""
import asyncio
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.models.analysis import AIAnalysis
from app.tools.factory import ToolFactory
from app.services.ai_service import AIService
from app.utils.logger import logger
from app.core.exceptions import ScanExecutionError
from app.config import settings

# Type ignore for SQLAlchemy Column assignments - these are false positives
# At runtime, SQLAlchemy ORM properly converts Column types to their Python equivalents


class AsyncScannerService:
    """Async service for parallel scan execution"""

    def __init__(self, db: Session):
        self.db = db

    async def execute_tool_async(
        self, 
        tool_name: str, 
        target: str, 
        profile: str,
        scan_id: str
    ) -> tuple[str, Optional[ScanResult]]:
        """Execute a single tool asynchronously"""
        logger.info(f"[{scan_id}] Starting {tool_name} on {target}")
        
        try:
            # Get tool instance
            tool = ToolFactory.get_tool(tool_name)
            
            # Run tool in executor (since tools are sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                tool.execute, 
                target, 
                profile
            )

            # Create result record
            scan_result = ScanResult(
                scan_id=scan_id,
                tool_name=tool_name,
                raw_output=result.stdout,
                parsed_output=result.parsed_data,
                exit_code=result.exit_code,
                execution_time=result.execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            
            # Save to database
            self.db.add(scan_result)
            self.db.commit()

            logger.info(f"[{scan_id}] ✓ {tool_name} completed in {result.execution_time:.2f}s")
            return tool_name, scan_result

        except Exception as e:
            logger.error(f"[{scan_id}] ✗ {tool_name} failed: {str(e)}", exc_info=True)
            
            # Create error result
            scan_result = ScanResult(
                scan_id=scan_id,
                tool_name=tool_name,
                raw_output="",
                parsed_output=None,
                exit_code=-1,
                execution_time=0,
                error_message=str(e)
            )
            self.db.add(scan_result)
            self.db.commit()
            
            return tool_name, None

    async def execute_scan_async(
        self, 
        scan_id: str, 
        gemini_api_key: Optional[str] = None
    ):
        """Execute scan with parallel tool execution"""
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        # Update status to running
        scan.status = ScanStatus.RUNNING  # type: ignore
        scan.started_at = datetime.utcnow()  # type: ignore
        self.db.commit()

        logger.info(f"[{scan_id}] 🚀 Starting parallel scan for: {scan.target}")
        logger.info(f"[{scan_id}] Tools to run: {', '.join(scan.tools)}")  # type: ignore

        try:
            # Create tasks for all tools (parallel execution)
            tasks = [
                self.execute_tool_async(
                    tool_name=tool_name,  # type: ignore
                    target=scan.target,  # type: ignore
                    profile=scan.profile,  # type: ignore
                    scan_id=scan.id  # type: ignore
                )
                for tool_name in scan.tools  # type: ignore
            ]

            # Execute all tools in parallel with timeout
            start_time = datetime.utcnow()
            
            # Use semaphore to limit concurrent executions
            semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TOOL_EXECUTIONS)
            
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            # Run with overall timeout
            results = await asyncio.wait_for(
                asyncio.gather(*[limited_task(task) for task in tasks]),
                timeout=settings.NMAP_TIMEOUT * len(scan.tools)  # type: ignore
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"[{scan_id}] All tools completed in {execution_time:.2f}s")

            # Collect successful results for AI analysis
            successful_results = {}
            failed_tools = []
            
            for tool_name, result in results:
                if result and result.parsed_output:
                    successful_results[tool_name] = result.parsed_output
                else:
                    failed_tools.append(tool_name)

            # Log summary
                if failed_tools:
                    logger.warning(
                        f"[{scan_id}] {len(failed_tools)}/{len(scan.tools)} tools failed: "  # type: ignore
                        f"{', '.join(failed_tools)}"
                    )
                else:
                    logger.info(f"[{scan_id}] ✓ All {len(scan.tools)} tools succeeded")  # type: ignore            # Run AI analysis if enabled
            if gemini_api_key and successful_results:
                logger.info(
                    f"[{scan_id}] Running AI analysis with {len(successful_results)} results"
                )
                
                try:
                    ai_service = AIService(gemini_api_key)

                    scan_data = {
                        'target': scan.target,
                        'tools': scan.tools,
                        'timestamp': scan.created_at.isoformat(),
                        'results': successful_results
                    }

                    # Run AI analysis in executor
                    loop = asyncio.get_event_loop()
                    ai_result = await loop.run_in_executor(
                        None,
                        ai_service.analyze_scan_results,
                        scan_data
                    )

                    # Save AI analysis
                    analysis = AIAnalysis(
                        scan_id=scan.id,
                        model_used=ai_result.model_used,
                        prompt_tokens=ai_result.prompt_tokens,
                        completion_tokens=ai_result.completion_tokens,
                        cost_usd=ai_result.cost_usd,
                        prompt_text=ai_result.prompt_text,
                        analysis_text=ai_result.analysis_text
                    )
                    self.db.add(analysis)
                    self.db.commit()

                    logger.info(
                        f"[{scan_id}] ✓ AI analysis completed "
                        f"(${ai_result.cost_usd:.6f}, "
                        f"{ai_result.prompt_tokens + ai_result.completion_tokens} tokens)"
                    )

                except Exception as e:
                    logger.error(f"[{scan_id}] AI analysis failed: {str(e)}", exc_info=True)

            elif gemini_api_key and not successful_results:
                logger.warning(
                    f"[{scan_id}] Skipping AI analysis - no successful tool results"
                )

            # Mark scan as completed
            scan.status = ScanStatus.COMPLETED  # type: ignore
            scan.completed_at = datetime.utcnow()  # type: ignore
            scan.current_tool = None  # type: ignore
            self.db.commit()

            total_time = (scan.completed_at - scan.started_at).total_seconds()  # type: ignore
            logger.info(f"[{scan_id}] ✓ Scan completed in {total_time:.2f}s")

        except asyncio.TimeoutError:
            scan.status = ScanStatus.FAILED  # type: ignore
            scan.error_message = "Scan timeout exceeded"  # type: ignore
            scan.completed_at = datetime.utcnow()  # type: ignore
            self.db.commit()
            logger.error(f"[{scan_id}] ✗ Scan timeout")
            raise ScanExecutionError(tool_name="Multi-tool scan", reason="Scan execution timeout")

        except Exception as e:
            scan.status = ScanStatus.FAILED  # type: ignore
            scan.error_message = str(e)  # type: ignore
            scan.completed_at = datetime.utcnow()  # type: ignore
            self.db.commit()
            logger.error(f"[{scan_id}] ✗ Scan failed: {str(e)}")
            raise ScanExecutionError(tool_name="Multi-tool scan", reason=f"Scan execution failed: {str(e)}")

    def execute_scan(self, scan_id: str, gemini_api_key: Optional[str] = None):
        """Wrapper to run async scan from sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.execute_scan_async(scan_id, gemini_api_key)
        )
