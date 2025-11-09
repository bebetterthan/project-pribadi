"""
Scan Context Manager - Phase 1, Day 1
Central data repository for tool findings and scan state
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.scan_context import ScanContext, FindingType
from app.utils.logger import logger


class ScanContextManager:
    """
    Manages scan context - central repository for all tool findings.
    Enables tool chaining by making previous findings queryable.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize context manager with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        logger.info("ScanContextManager initialized")
    
    def initialize_scan(self, scan_id: str, target: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Initialize scan context for a new scan.
        
        Args:
            scan_id: Unique scan identifier
            target: Original target (domain/IP)
            metadata: Additional scan metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store initial scan metadata as system context
            context = ScanContext(
                scan_id=scan_id,
                tool_name='system',
                finding_type=FindingType.METADATA,
                finding_data={
                    'target': target,
                    'scan_started': datetime.utcnow().isoformat(),
                    'metadata': metadata or {}
                },
                finding_metadata={'initialized': True}
            )
            self.db.add(context)
            self.db.commit()
            
            logger.info(f"Initialized scan context for scan {scan_id}, target: {target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scan context: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def add_findings(
        self, 
        scan_id: str, 
        tool_name: str, 
        finding_type: FindingType,
        findings: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add findings from a tool to scan context.
        
        Args:
            scan_id: Scan identifier
            tool_name: Tool that produced findings (e.g., 'subfinder')
            finding_type: Type of finding (SUBDOMAIN, PORT, VULNERABILITY, etc.)
            findings: List of finding dictionaries
            metadata: Additional metadata about findings
            
        Returns:
            Number of findings added
        """
        try:
            count = 0
            for finding_data in findings:
                context = ScanContext(
                    scan_id=scan_id,
                    tool_name=tool_name,
                    finding_type=finding_type,
                    finding_data=finding_data,
                    finding_metadata=metadata or {}
                )
                self.db.add(context)
                count += 1
            
            self.db.commit()
            logger.info(f"Added {count} {finding_type.value} findings from {tool_name} to scan {scan_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to add findings: {e}", exc_info=True)
            self.db.rollback()
            return 0
    
    def get_findings(
        self, 
        scan_id: str, 
        tool_name: Optional[str] = None,
        finding_type: Optional[FindingType] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve findings from scan context.
        
        Args:
            scan_id: Scan identifier
            tool_name: Filter by tool name (optional)
            finding_type: Filter by finding type (optional)
            
        Returns:
            List of finding dictionaries
        """
        try:
            query = self.db.query(ScanContext).filter(ScanContext.scan_id == scan_id)
            
            if tool_name:
                query = query.filter(ScanContext.tool_name == tool_name)
            
            if finding_type:
                query = query.filter(ScanContext.finding_type == finding_type)
            
            results = query.order_by(ScanContext.created_at).all()
            
            findings = [r.finding_data for r in results]
            logger.debug(f"Retrieved {len(findings)} findings for scan {scan_id}")
            return findings
            
        except Exception as e:
            logger.error(f"Failed to get findings: {e}", exc_info=True)
            return []
    
    def get_findings_by_type(self, scan_id: str, finding_type: FindingType) -> List[Dict[str, Any]]:
        """
        Get all findings of a specific type.
        
        Args:
            scan_id: Scan identifier
            finding_type: Type of findings to retrieve
            
        Returns:
            List of findings
        """
        return self.get_findings(scan_id=scan_id, finding_type=finding_type)
    
    def get_subdomains(self, scan_id: str) -> List[str]:
        """
        Get list of discovered subdomains (convenience method for tool chaining).
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            List of subdomain strings
        """
        findings = self.get_findings_by_type(scan_id, FindingType.SUBDOMAIN)
        
        # Extract subdomain strings from finding data
        subdomains = []
        for finding in findings:
            if isinstance(finding, dict):
                subdomain = finding.get('subdomain') or finding.get('domain') or finding.get('host')
                if subdomain:
                    subdomains.append(subdomain)
            elif isinstance(finding, str):
                subdomains.append(finding)
        
        logger.info(f"Retrieved {len(subdomains)} subdomains for scan {scan_id}")
        return subdomains
    
    def get_active_urls(self, scan_id: str) -> List[str]:
        """
        Get list of active URLs (convenience method for tool chaining).
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            List of active URL strings
        """
        findings = self.get_findings_by_type(scan_id, FindingType.HTTP_SERVICE)
        
        # Extract URLs from finding data
        urls = []
        for finding in findings:
            if isinstance(finding, dict):
                url = finding.get('url') or finding.get('host')
                if url:
                    urls.append(url)
            elif isinstance(finding, str):
                urls.append(finding)
        
        logger.info(f"Retrieved {len(urls)} active URLs for scan {scan_id}")
        return urls
    
    def get_open_ports(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Get list of open ports (convenience method for tool chaining).
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            List of port dictionaries with port, service, version info
        """
        return self.get_findings_by_type(scan_id, FindingType.PORT)
    
    def get_vulnerabilities(self, scan_id: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get discovered vulnerabilities.
        
        Args:
            scan_id: Scan identifier
            severity: Filter by severity (optional: 'critical', 'high', 'medium', 'low')
            
        Returns:
            List of vulnerability dictionaries
        """
        vulns = self.get_findings_by_type(scan_id, FindingType.VULNERABILITY)
        
        if severity:
            vulns = [v for v in vulns if v.get('severity', '').lower() == severity.lower()]
        
        return vulns
    
    def get_interesting_targets(self, scan_id: str, limit: int = 50) -> List[str]:
        """
        Get high-priority/interesting targets for focused scanning.
        
        Args:
            scan_id: Scan identifier
            limit: Maximum number of targets to return
            
        Returns:
            List of interesting target URLs/domains
        """
        # Get subdomains with interesting keywords
        subdomains = self.get_subdomains(scan_id)
        
        interesting_keywords = [
            'admin', 'api', 'dev', 'staging', 'test', 'internal',
            'vpn', 'mail', 'beta', 'demo', 'portal', 'dashboard',
            'manage', 'control', 'panel', 'console', 'auth'
        ]
        
        interesting = []
        for subdomain in subdomains:
            subdomain_lower = subdomain.lower()
            if any(keyword in subdomain_lower for keyword in interesting_keywords):
                interesting.append(subdomain)
        
        logger.info(f"Found {len(interesting)} interesting targets (of {len(subdomains)} total)")
        return interesting[:limit]
    
    def query_findings(
        self,
        scan_id: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Advanced query with custom filters.
        
        Args:
            scan_id: Scan identifier
            filters: Dictionary of filter criteria
                Examples:
                - {'tool_name': 'subfinder'}
                - {'finding_type': FindingType.SUBDOMAIN}
                - {'metadata.interesting': True}
                
        Returns:
            List of matching findings
        """
        try:
            query = self.db.query(ScanContext).filter(ScanContext.scan_id == scan_id)
            
            # Apply filters
            if 'tool_name' in filters:
                query = query.filter(ScanContext.tool_name == filters['tool_name'])
            
            if 'finding_type' in filters:
                query = query.filter(ScanContext.finding_type == filters['finding_type'])
            
            results = query.all()
            findings = [r.finding_data for r in results]
            
            logger.debug(f"Query returned {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"Failed to query findings: {e}", exc_info=True)
            return []
    
    def get_scan_statistics(self, scan_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics about scan findings.
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                'total_subdomains': len(self.get_subdomains(scan_id)),
                'total_active_urls': len(self.get_active_urls(scan_id)),
                'total_open_ports': len(self.get_open_ports(scan_id)),
                'total_vulnerabilities': len(self.get_vulnerabilities(scan_id)),
                'critical_vulnerabilities': len(self.get_vulnerabilities(scan_id, 'critical')),
                'high_vulnerabilities': len(self.get_vulnerabilities(scan_id, 'high')),
                'interesting_targets': len(self.get_interesting_targets(scan_id)),
            }
            
            # Count findings by tool
            all_contexts = self.db.query(ScanContext).filter(ScanContext.scan_id == scan_id).all()
            tools_executed = {}
            for ctx in all_contexts:
                if ctx.tool_name not in tools_executed:
                    tools_executed[ctx.tool_name] = 0
                tools_executed[ctx.tool_name] += 1
            
            stats['tools_executed'] = tools_executed
            stats['total_findings'] = len(all_contexts)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get scan statistics: {e}", exc_info=True)
            return {}
    
    def has_findings(self, scan_id: str, finding_type: FindingType) -> bool:
        """
        Check if scan has any findings of a specific type.
        
        Args:
            scan_id: Scan identifier
            finding_type: Type to check
            
        Returns:
            True if findings exist, False otherwise
        """
        try:
            count = self.db.query(ScanContext).filter(
                and_(
                    ScanContext.scan_id == scan_id,
                    ScanContext.finding_type == finding_type
                )
            ).count()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check findings existence: {e}", exc_info=True)
            return False

