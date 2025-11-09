from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.models.analysis import AIAnalysis
from app.tools.factory import ToolFactory
from app.services.ai_service import AIService
from app.utils.logger import logger
from app.core.exceptions import ScanExecutionError


class ScannerService:
    """Service for orchestrating scan execution"""

    def __init__(self, db: Session):
        self.db = db

    def execute_scan(self, scan_id: str, gemini_api_key: str = None):
        """Execute scan with all configured tools"""
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        # Update status to running
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Starting scan {scan_id} for target: {scan.target}")

        try:
            results = {}
            failed_tools = []

            # Execute each tool
            for tool_name in scan.tools:
                logger.info(f"Running {tool_name} on {scan.target}")
                scan.current_tool = tool_name
                self.db.commit()

                try:
                    tool = ToolFactory.get_tool(tool_name)
                    result = tool.execute(scan.target, scan.profile)

                    # Save result to database
                    scan_result = ScanResult(
                        scan_id=scan.id,
                        tool_name=tool_name,
                        raw_output=result.stdout,
                        parsed_output=result.parsed_data,
                        exit_code=result.exit_code,
                        execution_time=result.execution_time,
                        error_message=result.stderr if result.exit_code != 0 else None
                    )
                    self.db.add(scan_result)
                    self.db.commit()

                    # Store for AI analysis
                    if result.parsed_data:
                        results[tool_name] = result.parsed_data

                    logger.info(f"{tool_name} completed in {result.execution_time:.2f}s")

                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {str(e)}", exc_info=True)
                    failed_tools.append(tool_name)
                    # Continue with other tools even if one fails
                    scan_result = ScanResult(
                        scan_id=scan.id,
                        tool_name=tool_name,
                        raw_output="",
                        parsed_output=None,
                        exit_code=-1,
                        execution_time=0,
                        error_message=str(e)
                    )
                    self.db.add(scan_result)
                    self.db.commit()

            # Log summary
            if failed_tools:
                logger.warning(f"Scan {scan_id}: {len(failed_tools)} tools failed: {', '.join(failed_tools)}")

            # Run AI analysis if enabled
            if gemini_api_key and results:
                logger.info(f"Running AI analysis with {len(results)} tool results")
                try:
                    ai_service = AIService(gemini_api_key)

                    scan_data = {
                        'target': scan.target,
                        'tools': scan.tools,
                        'timestamp': scan.created_at.isoformat(),
                        'results': results
                    }

                    ai_result = ai_service.analyze_scan_results(scan_data)

                    # Save AI analysis with prompt
                    analysis = AIAnalysis(
                        scan_id=scan.id,
                        model_used=ai_result.model_used,
                        prompt_tokens=ai_result.prompt_tokens,
                        completion_tokens=ai_result.completion_tokens,
                        cost_usd=ai_result.cost_usd,
                        prompt_text=ai_result.prompt_text,  # Save full prompt
                        analysis_text=ai_result.analysis_text
                    )
                    self.db.add(analysis)
                    self.db.commit()

                    logger.info(f"AI analysis completed (${ai_result.cost_usd:.6f}, {ai_result.prompt_tokens + ai_result.completion_tokens} tokens)")

                except Exception as e:
                    logger.error(f"AI analysis failed: {str(e)}", exc_info=True)
                    # Don't fail the entire scan if AI fails - scan results are still valuable
            elif gemini_api_key and not results:
                logger.warning(f"Skipping AI analysis - no successful tool results for scan {scan_id}")

            # Mark scan as completed
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.current_tool = None
            self.db.commit()

            logger.info(f"Scan {scan_id} completed successfully")

        except Exception as e:
            # Mark scan as failed
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"Scan {scan_id} failed: {str(e)}")
            raise ScanExecutionError(f"Scan execution failed: {str(e)}")
