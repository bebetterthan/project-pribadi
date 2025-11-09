"""
Persistence Manager - Dual-write pattern for scan data
Writes to both SSE stream (real-time) and database (persistence)
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Scan, ScanStatus
from app.models.chat_message import ChatMessage
from app.models.result import ScanResult
from app.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.utils.logger import logger


class PersistenceManager:
    """
    Manages persistence of scan data with dual-write pattern:
    - Write to database (permanent storage)
    - Write to scan record for SSE streaming
    """
    
    def __init__(self, scan: Scan, db: Session):
        self.scan = scan
        self.db = db
        self.scan_repo = ScanRepository(db)
        self.vuln_repo = VulnerabilityRepository(db)
        self._message_sequence = 0
    
    def log_agent_thought(
        self,
        thought: str,
        metadata: Optional[Dict[str, Any]] = None,
        model_used: str = "flash"
    ):
        """
        Log agent's reasoning/thought process
        Dual-write: chat_messages table + scan.progress_message
        """
        self._message_sequence += 1
        
        # Write to database (permanent)
        import json
        chat_msg = ChatMessage(
            scan_id=self.scan.id,
            sequence=self._message_sequence,
            message_type="thought",
            content=thought,
            metadata_json=json.dumps(metadata or {})
        )
        self.db.add(chat_msg)
        
        # Write to scan for SSE streaming (real-time)
        self.scan.progress_message = thought
        self.scan.progress_metadata = metadata or {}
        
        self.db.commit()
        logger.debug(f"[Persistence] Agent thought logged (seq {self._message_sequence})")
    
    def log_tool_execution_start(
        self,
        tool_name: str,
        target: str,
        command: Optional[str] = None
    ):
        """Log when tool execution starts"""
        self._message_sequence += 1
        
        message = f"⚡ Executing {tool_name.upper()} against {target}"
        
        import json
        chat_msg = ChatMessage(
            scan_id=self.scan.id,
            sequence=self._message_sequence,
            message_type="tool",
            content=message,
            metadata_json=json.dumps({
                "tool_name": tool_name,
                "target": target,
                "command": command,
                "started_at": datetime.utcnow().isoformat(),
                "status": "starting"
            })
        )
        self.db.add(chat_msg)
        
        self.scan.current_tool = tool_name
        self.scan.progress_message = message
        self.scan.progress_metadata = {"tool": tool_name, "status": "running"}
        
        self.db.commit()
        logger.debug(f"[Persistence] Tool execution start logged: {tool_name}")
    
    def log_tool_execution_complete(
        self,
        tool_name: str,
        duration: float,
        findings_count: int = 0,
        summary: Optional[str] = None
    ):
        """Log when tool execution completes"""
        self._message_sequence += 1
        
        message = f"✅ **{tool_name.upper()} COMPLETED**\n\n"
        message += f"**Findings:** {findings_count}\n"
        message += f"**Time:** {duration:.1f}s"
        
        if summary:
            message += f"\n\n{summary}"
        
        import json
        chat_msg = ChatMessage(
            scan_id=self.scan.id,
            sequence=self._message_sequence,
            message_type="output",
            content=message,
            metadata_json=json.dumps({
                "tool_name": tool_name,
                "duration_seconds": duration,
                "findings_count": findings_count,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            })
        )
        self.db.add(chat_msg)
        
        self.scan.progress_message = message
        self.scan.progress_metadata = {
            "tool": tool_name,
            "status": "completed",
            "findings": findings_count,
            "duration": duration
        }
        
        self.db.commit()
        logger.debug(f"[Persistence] Tool execution complete logged: {tool_name}")
    
    def log_tool_execution_failed(
        self,
        tool_name: str,
        error: str,
        duration: float = 0
    ):
        """Log when tool execution fails"""
        self._message_sequence += 1
        
        message = f"❌ {tool_name.upper()} FAILED: {error}"
        
        import json
        chat_msg = ChatMessage(
            scan_id=self.scan.id,
            sequence=self._message_sequence,
            message_type="tool",
            content=message,
            metadata_json=json.dumps({
                "tool_name": tool_name,
                "error": error,
                "duration_seconds": duration,
                "failed_at": datetime.utcnow().isoformat(),
                "status": "failed"
            })
        )
        self.db.add(chat_msg)
        
        self.scan.progress_message = message
        self.scan.progress_metadata = {
            "tool": tool_name,
            "status": "failed",
            "error": error
        }
        
        self.db.commit()
        logger.warning(f"[Persistence] Tool execution failed logged: {tool_name} - {error}")
    
    def save_tool_result(
        self,
        tool_name: str,
        raw_output: str,
        parsed_output: Optional[Dict[str, Any]],
        exit_code: int,
        execution_time: float,
        error_message: Optional[str] = None,
        command_executed: Optional[str] = None
    ) -> ScanResult:
        """Save tool execution result to database"""
        from app.models.result import ScanResult as SR
        scan_result = SR(
            scan_id=self.scan.id,
            tool_name=tool_name,
            raw_output=raw_output,
            parsed_output=parsed_output,
            exit_code=exit_code,
            execution_time=execution_time,
            error_message=error_message
        )
        self.db.add(scan_result)
        self.db.commit()
        self.db.refresh(scan_result)
        
        logger.debug(f"[Persistence] Tool result saved: {tool_name} (ID: {scan_result.id})")
        return scan_result
    
    def save_vulnerability(
        self,
        tool_result_id: str,
        cve_id: Optional[str],
        title: str,
        description: str,
        severity: VulnerabilitySeverity,
        affected_host: Optional[str] = None,
        affected_url: Optional[str] = None,
        cvss_score: Optional[float] = None,
        remediation: Optional[str] = None,
        **kwargs
    ) -> Vulnerability:
        """Save discovered vulnerability"""
        vuln = Vulnerability(
            scan_id=self.scan.id,
            tool_result_id=tool_result_id,
            cve_id=cve_id,
            title=title,
            description=description,
            severity=severity,
            affected_host=affected_host or self.scan.target,
            affected_url=affected_url,
            cvss_score=cvss_score,
            remediation=remediation,
            status=VulnerabilityStatus.OPEN,
            **kwargs
        )
        self.db.add(vuln)
        self.db.commit()
        self.db.refresh(vuln)
        
        logger.info(f"[Persistence] Vulnerability saved: {title} (Severity: {severity})")
        return vuln
    
    def extract_and_save_vulnerabilities(
        self,
        tool_result: ScanResult,
        tool_name: str
    ) -> int:
        """
        Extract vulnerabilities from tool result and save them
        Returns count of vulnerabilities saved
        """
        if not tool_result.parsed_output:
            return 0
        
        vuln_count = 0
        
        # Extract from Nuclei results
        if tool_name == "nuclei" and "findings" in tool_result.parsed_output:
            for finding in tool_result.parsed_output["findings"]:
                severity_map = {
                    "critical": VulnerabilitySeverity.CRITICAL,
                    "high": VulnerabilitySeverity.HIGH,
                    "medium": VulnerabilitySeverity.MEDIUM,
                    "low": VulnerabilitySeverity.LOW,
                    "info": VulnerabilitySeverity.INFO,
                }
                
                severity = severity_map.get(
                    finding.get("info", {}).get("severity", "info").lower(),
                    VulnerabilitySeverity.INFO
                )
                
                self.save_vulnerability(
                    tool_result_id=tool_result.id,
                    cve_id=finding.get("info", {}).get("classification", {}).get("cve-id"),
                    title=finding.get("info", {}).get("name", "Unknown Vulnerability"),
                    description=finding.get("info", {}).get("description", "No description available"),
                    severity=severity,
                    affected_url=finding.get("matched-at"),
                    template_id=finding.get("template-id"),
                    tool_name=tool_name,
                    references=finding.get("info", {}).get("reference", [])
                )
                vuln_count += 1
        
        # Extract from Nmap results (open ports as attack surface)
        elif tool_name == "nmap" and "open_ports" in tool_result.parsed_output:
            for port_info in tool_result.parsed_output["open_ports"]:
                # Only flag potentially risky services
                risky_services = ["mysql", "postgresql", "mongodb", "redis", "telnet", "ftp"]
                service = port_info.get("service", "").lower()
                
                if service in risky_services:
                    self.save_vulnerability(
                        tool_result_id=tool_result.id,
                        cve_id=None,
                        title=f"{service.upper()} Service Exposed",
                        description=f"Port {port_info.get('port')} running {service} is exposed to the internet.",
                        severity=VulnerabilitySeverity.HIGH if service in ["mysql", "postgresql", "mongodb"] else VulnerabilitySeverity.MEDIUM,
                        affected_port=port_info.get("port"),
                        tool_name=tool_name,
                        remediation=f"Restrict {service} access to internal networks only. Implement strong authentication."
                    )
                    vuln_count += 1
        
        return vuln_count
    
    def update_scan_status(
        self,
        status: ScanStatus,
        error_message: Optional[str] = None
    ):
        """Update scan status"""
        self.scan_repo.update_status(
            self.scan.id,
            status,
            error_message=error_message
        )
        logger.info(f"[Persistence] Scan status updated: {status}")
    
    def finalize_scan(
        self,
        completed_tools: list,
        total_findings: int,
        iterations: int
    ):
        """Finalize scan with summary"""
        # Calculate summary
        vuln_counts = self.vuln_repo.count_by_severity(self.scan.id)
        
        summary = {
            "tools_executed": len(completed_tools),
            "tool_names": completed_tools,
            "iterations": iterations,
            "total_findings": total_findings,
            "vulnerabilities": vuln_counts,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Update scan with summary
        self.scan_repo.update_summary(self.scan.id, summary)
        
        # Log completion
        self._message_sequence += 1
        completion_msg = f"✅ **SCAN COMPLETED**\n\n"
        completion_msg += f"**Tools Executed:** {len(completed_tools)}\n"
        completion_msg += f"**Iterations:** {iterations}\n"
        completion_msg += f"**Total Findings:** {total_findings}\n"
        completion_msg += f"**Vulnerabilities:**\n"
        completion_msg += f"  - Critical: {vuln_counts.get('critical', 0)}\n"
        completion_msg += f"  - High: {vuln_counts.get('high', 0)}\n"
        completion_msg += f"  - Medium: {vuln_counts.get('medium', 0)}\n"
        completion_msg += f"  - Low: {vuln_counts.get('low', 0)}\n"
        
        import json
        chat_msg = ChatMessage(
            scan_id=self.scan.id,
            sequence=self._message_sequence,
            message_type="system",
            content=completion_msg,
            metadata_json=json.dumps(summary)
        )
        self.db.add(chat_msg)
        
        self.scan.progress_message = completion_msg
        self.scan.progress_metadata = summary
        
        self.db.commit()
        
        logger.info(f"[Persistence] Scan finalized: {len(completed_tools)} tools, {total_findings} findings")

