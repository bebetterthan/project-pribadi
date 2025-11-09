"""
Insight Extraction Engine
Fase 3.5: Extract actionable insights from scan results
"""

from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from app.utils.logger import logger

class InsightType(str, Enum):
    """Types of insights"""
    CRITICAL_FINDING = "critical_finding"
    BEST_PRACTICE_VIOLATION = "best_practice_violation"
    RECOMMENDATION = "recommendation"
    ATTACK_SURFACE = "attack_surface"

class SeverityLevel(str, Enum):
    """Insight severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Insight:
    """Single actionable insight"""
    type: InsightType
    severity: SeverityLevel
    title: str
    description: str
    recommendation: str
    affected_resource: str = ""
    references: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "affected_resource": self.affected_resource,
            "references": self.references or [],
        }


class InsightExtractor:
    """
    Rule-based insight extraction from scan results
    """
    
    def __init__(self):
        self.insights = []
        
    def extract_insights(self, scan_results: Dict[str, Any]) -> List[Insight]:
        """
        Extract insights from scan results
        
        Args:
            scan_results: Combined results from all tools
            
        Returns:
            List of insights
        """
        self.insights = []
        
        # Extract from Nmap results
        if 'nmap' in scan_results:
            self._extract_from_nmap(scan_results['nmap'])
        
        # Extract from Nuclei results
        if 'nuclei' in scan_results:
            self._extract_from_nuclei(scan_results['nuclei'])
        
        # Extract from Subfinder results
        if 'subfinder' in scan_results:
            self._extract_from_subfinder(scan_results['subfinder'])
        
        # Extract from ffuf results
        if 'ffuf' in scan_results:
            self._extract_from_ffuf(scan_results['ffuf'])
        
        # Cross-tool correlation insights
        self._extract_correlations(scan_results)
        
        # Sort by severity
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4,
        }
        self.insights.sort(key=lambda x: severity_order.get(x.severity, 5))
        
        logger.info(f"Extracted {len(self.insights)} insights")
        return self.insights
    
    def _extract_from_nmap(self, nmap_data: Dict[str, Any]):
        """Extract insights from Nmap results"""
        parsed = nmap_data.get('parsed_output', {})
        open_ports = parsed.get('open_ports', [])
        
        # Rule 1: Check for risky ports
        risky_ports = {
            22: "SSH",
            23: "Telnet (unencrypted)",
            21: "FTP (unencrypted)",
            3306: "MySQL",
            5432: "PostgreSQL",
            1433: "MS SQL",
            6379: "Redis",
            27017: "MongoDB",
            3389: "RDP",
        }
        
        for port_info in open_ports:
            port = port_info.get('port')
            if port in risky_ports:
                service_name = risky_ports[port]
                
                if port in [23, 21]:  # Unencrypted services
                    self.insights.append(Insight(
                        type=InsightType.CRITICAL_FINDING,
                        severity=SeverityLevel.HIGH,
                        title=f"{service_name} Exposed on Port {port}",
                        description=f"Unencrypted {service_name} service detected. All traffic including credentials transmitted in plaintext.",
                        recommendation=f"Disable {service_name} and use encrypted alternatives (SSH instead of Telnet, SFTP/SCP instead of FTP).",
                        affected_resource=f"Port {port}/tcp"
                    ))
                elif port in [3306, 5432, 1433, 6379, 27017]:  # Databases
                    self.insights.append(Insight(
                        type=InsightType.CRITICAL_FINDING,
                        severity=SeverityLevel.HIGH,
                        title=f"Database Port {port} ({service_name}) Exposed",
                        description=f"Database service accessible from internet. Risk of unauthorized access and data breach.",
                        recommendation=f"Restrict {service_name} access to internal networks only. Implement firewall rules and VPN access.",
                        affected_resource=f"Port {port}/tcp"
                    ))
        
        # Rule 2: Too many open ports
        if len(open_ports) > 10:
            self.insights.append(Insight(
                type=InsightType.RECOMMENDATION,
                severity=SeverityLevel.MEDIUM,
                title="Large Attack Surface Detected",
                description=f"{len(open_ports)} open ports found. Each open port increases attack surface.",
                recommendation="Review all services and close unnecessary ports. Implement principle of least privilege.",
                affected_resource=f"{len(open_ports)} ports"
            ))
        
        # Rule 3: Check for HTTP without HTTPS
        has_http = any(p.get('port') == 80 for p in open_ports)
        has_https = any(p.get('port') == 443 for p in open_ports)
        
        if has_http and not has_https:
            self.insights.append(Insight(
                type=InsightType.BEST_PRACTICE_VIOLATION,
                severity=SeverityLevel.MEDIUM,
                title="No HTTPS Detected",
                description="Website accessible only via HTTP. Traffic not encrypted, vulnerable to eavesdropping and MITM attacks.",
                recommendation="Implement HTTPS with valid SSL/TLS certificate. Redirect all HTTP traffic to HTTPS.",
                affected_resource="Port 80/tcp",
                references=["https://letsencrypt.org/"]
            ))
    
    def _extract_from_nuclei(self, nuclei_data: Dict[str, Any]):
        """Extract insights from Nuclei results"""
        parsed = nuclei_data.get('parsed_output', {})
        findings = parsed.get('findings', [])
        
        # Rule 1: Critical CVEs with high CVSS
        for finding in findings:
            if finding.get('severity') == 'critical':
                cvss = finding.get('cvss_score', 0)
                cve_id = finding.get('cve_id', '')
                
                if cvss >= 9.0:
                    self.insights.append(Insight(
                        type=InsightType.CRITICAL_FINDING,
                        severity=SeverityLevel.CRITICAL,
                        title=f"Critical Vulnerability: {cve_id or finding.get('name', 'Unknown')}",
                        description=f"CVSS {cvss}/10.0 vulnerability detected. {finding.get('description', '')}",
                        recommendation="Apply security patches immediately. If patch unavailable, implement compensating controls or isolate affected service.",
                        affected_resource=finding.get('matched_at', ''),
                        references=[f"https://nvd.nist.gov/vuln/detail/{cve_id}"] if cve_id else []
                    ))
        
        # Rule 2: Count findings by severity
        critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
        high_count = sum(1 for f in findings if f.get('severity') == 'high')
        
        if critical_count + high_count >= 5:
            self.insights.append(Insight(
                type=InsightType.ATTACK_SURFACE,
                severity=SeverityLevel.HIGH,
                title="Multiple High-Severity Vulnerabilities Detected",
                description=f"{critical_count} critical and {high_count} high severity vulnerabilities found. High risk of compromise.",
                recommendation="Prioritize patching based on CVSS scores and exploit availability. Consider engaging security team for immediate review.",
                affected_resource=f"{critical_count + high_count} vulnerabilities"
            ))
    
    def _extract_from_subfinder(self, subfinder_data: Dict[str, Any]):
        """Extract insights from Subfinder results"""
        parsed = subfinder_data.get('parsed_output', {})
        total = parsed.get('total_subdomains', 0)
        interesting = parsed.get('interesting_findings', [])
        
        if total > 20:
            self.insights.append(Insight(
                type=InsightType.ATTACK_SURFACE,
                severity=SeverityLevel.MEDIUM,
                title="Large Subdomain Footprint",
                description=f"{total} subdomains discovered. Large attack surface with potential for forgotten/abandoned services.",
                recommendation="Audit all subdomains for necessity. Decommission unused subdomains. Implement subdomain monitoring.",
                affected_resource=f"{total} subdomains"
            ))
        
        # Highlight interesting subdomains
        if interesting:
            for finding in interesting[:3]:  # Top 3 only
                self.insights.append(Insight(
                    type=InsightType.RECOMMENDATION,
                    severity=SeverityLevel.MEDIUM,
                    title="Potentially Sensitive Subdomain Detected",
                    description=finding,
                    recommendation="Review access controls for development/staging/admin subdomains. Ensure proper authentication and network restrictions.",
                    affected_resource=finding.split('(')[0].strip()
                ))
    
    def _extract_from_ffuf(self, ffuf_data: Dict[str, Any]):
        """Extract insights from ffuf results"""
        parsed = ffuf_data.get('parsed_output', {})
        paths = parsed.get('discovered_paths', [])
        
        # Rule 1: Check for sensitive files
        sensitive_patterns = {
            '.git': "Git repository exposed - source code disclosure risk",
            '.env': "Environment file exposed - may contain secrets",
            'backup': "Backup file exposed - may contain sensitive data",
            '.sql': "Database dump exposed - data breach risk",
            'config': "Configuration file exposed - may reveal system details",
            'admin': "Admin panel found - brute force target",
        }
        
        for path_info in paths:
            path = path_info.get('path', '').lower()
            risk_level = path_info.get('risk_level', 'low')
            
            for pattern, description in sensitive_patterns.items():
                if pattern in path:
                    severity = SeverityLevel.CRITICAL if risk_level == 'critical' else SeverityLevel.HIGH
                    
                    self.insights.append(Insight(
                        type=InsightType.CRITICAL_FINDING,
                        severity=severity,
                        title=f"Sensitive Path Exposed: {path}",
                        description=description,
                        recommendation=f"Immediately remove or restrict access to {path}. Implement proper access controls.",
                        affected_resource=path_info.get('full_url', path)
                    ))
                    break
    
    def _extract_correlations(self, scan_results: Dict[str, Any]):
        """Extract insights from cross-tool correlations"""
        # Correlation 1: Open web ports + no HTTPS = priority
        nmap_data = scan_results.get('nmap', {}).get('parsed_output', {})
        open_ports = nmap_data.get('open_ports', [])
        
        web_ports = [p for p in open_ports if p.get('port') in [80, 8080, 8000, 3000]]
        https_ports = [p for p in open_ports if p.get('port') in [443, 8443]]
        
        if web_ports and not https_ports:
            self.insights.append(Insight(
                type=InsightType.ATTACK_SURFACE,
                severity=SeverityLevel.MEDIUM,
                title="Unencrypted Web Services",
                description=f"{len(web_ports)} web service(s) found without HTTPS. All traffic unencrypted.",
                recommendation="Implement HTTPS for all web services. Use Let's Encrypt for free certificates.",
                affected_resource=f"Ports: {', '.join(str(p.get('port')) for p in web_ports)}"
            ))
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of insights by category and severity
        
        Returns:
            Summary statistics
        """
        summary = {
            'total_insights': len(self.insights),
            'by_severity': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
            },
            'by_type': {
                'critical_finding': 0,
                'best_practice_violation': 0,
                'recommendation': 0,
                'attack_surface': 0,
            },
            'top_critical': [],
        }
        
        for insight in self.insights:
            # Count by severity
            summary['by_severity'][insight.severity] += 1
            
            # Count by type
            summary['by_type'][insight.type] += 1
            
            # Collect top critical
            if insight.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                summary['top_critical'].append({
                    'title': insight.title,
                    'severity': insight.severity,
                })
        
        # Limit top critical to 5
        summary['top_critical'] = summary['top_critical'][:5]
        
        return summary


# Convenience function
def extract_insights(scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract insights from scan results
    
    Args:
        scan_results: Combined results from all tools
        
    Returns:
        List of insights as dictionaries
    """
    extractor = InsightExtractor()
    insights = extractor.extract_insights(scan_results)
    return [insight.to_dict() for insight in insights]

