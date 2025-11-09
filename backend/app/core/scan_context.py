"""
Scan Context Manager - Central data repository for tool findings
Phase 1, Day 1: Foundation Component

Purpose:
- Store all findings from all tools in structured format
- Enable queries by subsequent tools
- Maintain relationships between findings
- Persist data across tool executions
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.utils.logger import logger
import json


class ScanContextManager:
    """
    Central manager for scan findings and data flow between tools
    
    This class provides the "memory" for the scan, allowing tools to:
    - Store their discoveries
    - Query findings from previous tools
    - Build upon each other's results
    """
    
    def __init__(self, scan_id: str, db_session: Session):
        """
        Initialize scan context for a specific scan
        
        Args:
            scan_id: Unique identifier for this scan
            db_session: Database session for persistence
        """
        self.scan_id = scan_id
        self.db = db_session
        self._cache: Dict[str, Any] = {}  # In-memory cache for fast access
        
        logger.info(f"[ScanContext] Initialized for scan {scan_id}")
    
    # ========================================================================
    # CORE OPERATIONS: Add, Get, Query
    # ========================================================================
    
    def add_findings(
        self, 
        tool_name: str, 
        finding_type: str,
        findings: List[Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add findings from a tool to the scan context
        
        Args:
            tool_name: Name of tool that generated findings (e.g., 'subfinder')
            finding_type: Type of finding (e.g., 'subdomain', 'port', 'vulnerability')
            findings: List of findings (can be dicts, strings, or objects)
            metadata: Optional additional metadata about these findings
            
        Returns:
            True if successfully stored
            
        Example:
            >>> context.add_findings(
            ...     tool_name='subfinder',
            ...     finding_type='subdomain',
            ...     findings=['admin.example.com', 'api.example.com'],
            ...     metadata={'total': 2, 'interesting': 2}
            ... )
        """
        try:
            # Store in cache for fast access
            cache_key = f"{tool_name}:{finding_type}"
            self._cache[cache_key] = {
                'findings': findings,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow(),
                'count': len(findings) if isinstance(findings, list) else 1
            }
            
            # Also store in database for persistence
            from app.models.scan_context import ScanContextEntry
            
            entry = ScanContextEntry(
                scan_id=self.scan_id,
                tool_name=tool_name,
                finding_type=finding_type,
                finding_count=len(findings) if isinstance(findings, list) else 1,
                findings_json=json.dumps(findings, default=str),
                metadata_json=json.dumps(metadata, default=str) if metadata else None,
                created_at=datetime.utcnow()
            )
            
            self.db.add(entry)
            self.db.commit()
            
            logger.info(
                f"[ScanContext] Stored {len(findings) if isinstance(findings, list) else 1} "
                f"{finding_type}(s) from {tool_name}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[ScanContext] Failed to add findings: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def get_findings(
        self, 
        tool_name: str, 
        finding_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get findings from a specific tool
        
        Args:
            tool_name: Name of tool (e.g., 'subfinder')
            finding_type: Optional type filter (e.g., 'subdomain')
            
        Returns:
            Dictionary with 'findings', 'metadata', 'timestamp', 'count'
            Returns empty dict if not found
            
        Example:
            >>> subdomains = context.get_findings('subfinder', 'subdomain')
            >>> print(subdomains['count'])  # 1978
            >>> print(subdomains['findings'][:5])  # First 5 subdomains
        """
        try:
            # Try cache first (fast)
            if finding_type:
                cache_key = f"{tool_name}:{finding_type}"
                if cache_key in self._cache:
                    logger.debug(f"[ScanContext] Cache hit: {cache_key}")
                    return self._cache[cache_key]
            
            # Query database
            from app.models.scan_context import ScanContextEntry
            
            query = self.db.query(ScanContextEntry).filter(
                ScanContextEntry.scan_id == self.scan_id,
                ScanContextEntry.tool_name == tool_name
            )
            
            if finding_type:
                query = query.filter(ScanContextEntry.finding_type == finding_type)
            
            entries = query.all()
            
            if not entries:
                logger.debug(f"[ScanContext] No findings for {tool_name}:{finding_type}")
                return {}
            
            # Combine if multiple entries
            all_findings = []
            combined_metadata = {}
            latest_timestamp = None
            
            for entry in entries:
                findings = json.loads(entry.findings_json) if entry.findings_json else []
                if isinstance(findings, list):
                    all_findings.extend(findings)
                else:
                    all_findings.append(findings)
                
                if entry.metadata_json:
                    combined_metadata.update(json.loads(entry.metadata_json))
                
                if not latest_timestamp or entry.created_at > latest_timestamp:
                    latest_timestamp = entry.created_at
            
            result = {
                'findings': all_findings,
                'metadata': combined_metadata,
                'timestamp': latest_timestamp,
                'count': len(all_findings)
            }
            
            # Update cache
            if finding_type:
                cache_key = f"{tool_name}:{finding_type}"
                self._cache[cache_key] = result
            
            logger.debug(f"[ScanContext] Retrieved {len(all_findings)} findings from {tool_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"[ScanContext] Failed to get findings: {e}", exc_info=True)
            return {}
    
    def query_findings(
        self,
        finding_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query findings across all tools with optional filters
        
        Args:
            finding_type: Filter by type (e.g., 'subdomain', 'vulnerability')
            filters: Additional filters (e.g., {'severity': 'critical'})
            limit: Maximum number of results
            
        Returns:
            List of finding dictionaries
            
        Example:
            >>> # Get all subdomains
            >>> subdomains = context.query_findings(finding_type='subdomain')
            >>>
            >>> # Get all critical vulnerabilities
            >>> vulns = context.query_findings(
            ...     finding_type='vulnerability',
            ...     filters={'severity': 'critical'}
            ... )
        """
        try:
            from app.models.scan_context import ScanContextEntry
            
            query = self.db.query(ScanContextEntry).filter(
                ScanContextEntry.scan_id == self.scan_id
            )
            
            if finding_type:
                query = query.filter(ScanContextEntry.finding_type == finding_type)
            
            if limit:
                query = query.limit(limit)
            
            entries = query.all()
            
            results = []
            for entry in entries:
                findings = json.loads(entry.findings_json) if entry.findings_json else []
                metadata = json.loads(entry.metadata_json) if entry.metadata_json else {}
                
                # Apply custom filters if provided
                if filters:
                    # Filter findings based on criteria
                    filtered_findings = []
                    for finding in findings if isinstance(findings, list) else [findings]:
                        match = True
                        if isinstance(finding, dict):
                            for key, value in filters.items():
                                if finding.get(key) != value:
                                    match = False
                                    break
                        if match:
                            filtered_findings.append(finding)
                    findings = filtered_findings
                
                results.append({
                    'tool_name': entry.tool_name,
                    'finding_type': entry.finding_type,
                    'findings': findings,
                    'metadata': metadata,
                    'count': len(findings) if isinstance(findings, list) else 1,
                    'timestamp': entry.created_at
                })
            
            logger.debug(f"[ScanContext] Query returned {len(results)} result groups")
            
            return results
            
        except Exception as e:
            logger.error(f"[ScanContext] Query failed: {e}", exc_info=True)
            return []
    
    # ========================================================================
    # CONVENIENCE METHODS: Common Queries
    # ========================================================================
    
    def get_all_subdomains(self) -> List[str]:
        """
        Get all discovered subdomains from any tool
        
        Returns:
            List of subdomain strings
            
        Example:
            >>> subdomains = context.get_all_subdomains()
            >>> print(f"Found {len(subdomains)} subdomains")
        """
        subdomains = []
        
        # Get from subfinder
        subfinder_data = self.get_findings('subfinder', 'subdomain')
        if subfinder_data and 'findings' in subfinder_data:
            findings = subfinder_data['findings']
            for f in findings:
                if isinstance(f, dict):
                    subdomains.append(f.get('subdomain', ''))
                else:
                    subdomains.append(str(f))
        
        # Deduplicate
        subdomains = list(set(filter(None, subdomains)))
        
        logger.debug(f"[ScanContext] Retrieved {len(subdomains)} unique subdomains")
        
        return subdomains
    
    def get_active_urls(self) -> List[str]:
        """
        Get all active/alive URLs from HTTP probing
        
        Returns:
            List of URL strings
            
        Example:
            >>> urls = context.get_active_urls()
            >>> print(f"{len(urls)} URLs are active")
        """
        urls = []
        
        # Get from httpx
        httpx_data = self.get_findings('httpx')
        if httpx_data and 'findings' in httpx_data:
            findings = httpx_data['findings']
            if isinstance(findings, dict):
                urls = findings.get('alive_hosts', [])
            elif isinstance(findings, list):
                for f in findings:
                    if isinstance(f, dict):
                        url = f.get('url', '')
                        if url:
                            urls.append(url)
        
        logger.debug(f"[ScanContext] Retrieved {len(urls)} active URLs")
        
        return urls
    
    def get_open_ports(self) -> List[Dict[str, Any]]:
        """
        Get all open ports from port scanning
        
        Returns:
            List of port dictionaries with port, service, version info
        """
        ports = []
        
        # Get from nmap
        nmap_data = self.get_findings('nmap')
        if nmap_data and 'findings' in nmap_data:
            findings = nmap_data['findings']
            if isinstance(findings, dict):
                ports = findings.get('open_ports', [])
            elif isinstance(findings, list):
                ports = findings
        
        logger.debug(f"[ScanContext] Retrieved {len(ports)} open ports")
        
        return ports
    
    def get_vulnerabilities(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get discovered vulnerabilities, optionally filtered by severity
        
        Args:
            severity: Optional filter ('critical', 'high', 'medium', 'low')
            
        Returns:
            List of vulnerability dictionaries
        """
        vulns = []
        
        # Get from nuclei
        nuclei_data = self.get_findings('nuclei', 'vulnerability')
        if nuclei_data and 'findings' in nuclei_data:
            findings = nuclei_data['findings']
            if isinstance(findings, list):
                vulns = findings
        
        # Filter by severity if requested
        if severity and vulns:
            vulns = [v for v in vulns if v.get('severity', '').lower() == severity.lower()]
        
        logger.debug(f"[ScanContext] Retrieved {len(vulns)} vulnerabilities")
        
        return vulns
    
    # ========================================================================
    # STATISTICS & METADATA
    # ========================================================================
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """
        Get overall scan statistics
        
        Returns:
            Dictionary with counts and statistics
        """
        stats = {
            'total_subdomains': len(self.get_all_subdomains()),
            'active_urls': len(self.get_active_urls()),
            'open_ports': len(self.get_open_ports()),
            'vulnerabilities': {
                'total': len(self.get_vulnerabilities()),
                'critical': len(self.get_vulnerabilities('critical')),
                'high': len(self.get_vulnerabilities('high')),
                'medium': len(self.get_vulnerabilities('medium')),
                'low': len(self.get_vulnerabilities('low'))
            },
            'tools_executed': self._get_tool_count()
        }
        
        logger.info(f"[ScanContext] Statistics: {stats}")
        
        return stats
    
    def _get_tool_count(self) -> int:
        """Get count of unique tools that have contributed findings"""
        try:
            from app.models.scan_context import ScanContextEntry
            
            count = self.db.query(ScanContextEntry.tool_name).filter(
                ScanContextEntry.scan_id == self.scan_id
            ).distinct().count()
            
            return count
        except:
            return 0
    
    def clear_cache(self):
        """Clear in-memory cache (useful for testing or memory management)"""
        self._cache.clear()
        logger.debug("[ScanContext] Cache cleared")

