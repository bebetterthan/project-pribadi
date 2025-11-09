"""
Target Sanitizer - Remove sensitive target info before sending to AI
Implements placeholder pattern for safety
"""
from typing import Dict, Any, List
import re
from urllib.parse import urlparse


class TargetSanitizer:
    """
    Sanitize scan results by replacing real targets with placeholders
    This prevents AI from seeing specific target information
    """
    
    def __init__(self, target: str):
        """
        Initialize sanitizer with target to hide
        
        Args:
            target: The actual target (e.g., "unair.ac.id", "192.168.1.1")
        """
        self.target = target.strip()
        self.placeholder = "TARGET_HOST"
        self.url_placeholder = "TARGET_URL"
        
        # Extract domain/hostname for better matching
        self.domain = self._extract_domain(target)
        self.ip_pattern = self._create_ip_pattern(target)
    
    def _extract_domain(self, target: str) -> str:
        """Extract domain from target"""
        # Remove protocol if present
        if '://' in target:
            parsed = urlparse(target)
            return parsed.netloc or parsed.path
        return target
    
    def _create_ip_pattern(self, target: str) -> str:
        """Create regex pattern for IP if target is IP"""
        # Check if it's an IP address
        ip_regex = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_regex, target):
            return re.escape(target)
        return None
    
    def sanitize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize scan results by replacing target with placeholders
        
        Args:
            results: Raw scan results containing target info
        
        Returns:
            Sanitized results safe for AI processing
        """
        if not results:
            return {}
        
        # Deep copy and sanitize
        sanitized = self._sanitize_recursive(results)
        return sanitized
    
    def _sanitize_recursive(self, obj: Any) -> Any:
        """Recursively sanitize data structures"""
        if isinstance(obj, dict):
            return {k: self._sanitize_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._sanitize_string(obj)
        else:
            return obj
    
    def _sanitize_string(self, text: str) -> str:
        """Replace target occurrences in string"""
        if not text:
            return text
        
        result = text
        
        # Replace full URLs
        url_patterns = [
            f'https://{self.domain}',
            f'http://{self.domain}',
            f'https://{self.target}',
            f'http://{self.target}',
        ]
        for pattern in url_patterns:
            result = result.replace(pattern, f'{self.url_placeholder}')
        
        # Replace domain/hostname
        result = result.replace(self.domain, self.placeholder)
        result = result.replace(self.target, self.placeholder)
        
        # Replace IP if applicable
        if self.ip_pattern:
            result = re.sub(self.ip_pattern, self.placeholder, result)
        
        return result
    
    def create_summary(self, results: Dict[str, Any]) -> str:
        """
        Create sanitized summary of results for AI
        
        Args:
            results: Raw scan results
        
        Returns:
            Human-readable summary with placeholders
        """
        summary = []
        
        for tool_name, tool_result in results.items():
            if not tool_result:
                continue
            
            summary.append(f"## {tool_name.upper()} Results:\n")
            
            # Nmap results
            if tool_name == "nmap" and isinstance(tool_result, dict):
                open_ports = tool_result.get('open_ports', [])
                summary.append(f"- Discovered {len(open_ports)} open ports on {self.placeholder}")
                
                for port in open_ports[:5]:  # Top 5
                    port_num = port.get('port', '?')
                    service = port.get('service', 'unknown')
                    version = port.get('version', '')
                    summary.append(f"  - Port {port_num}/{service} {version}".strip())
                
                if len(open_ports) > 5:
                    summary.append(f"  - ... and {len(open_ports) - 5} more ports")
            
            # Nuclei results
            elif tool_name == "nuclei" and isinstance(tool_result, dict):
                findings = tool_result.get('findings', [])
                summary.append(f"- Found {len(findings)} security findings")
                
                # Group by severity
                severity_count = {}
                for finding in findings:
                    sev = finding.get('severity', 'unknown')
                    severity_count[sev] = severity_count.get(sev, 0) + 1
                
                for sev, count in severity_count.items():
                    summary.append(f"  - {sev.upper()}: {count} findings")
            
            # WhatWeb results
            elif tool_name == "whatweb" and isinstance(tool_result, dict):
                tech = tool_result.get('technologies', {})
                summary.append(f"- Technology stack identified:")
                if 'server' in tech:
                    summary.append(f"  - Server: {tech['server']}")
                if 'cms' in tech:
                    summary.append(f"  - CMS: {tech['cms']}")
                if 'framework' in tech:
                    summary.append(f"  - Framework: {tech['framework']}")
            
            # SSLScan results
            elif tool_name == "sslscan" and isinstance(tool_result, dict):
                summary.append(f"- SSL/TLS configuration analyzed")
                if 'tls_versions' in tool_result:
                    summary.append(f"  - Supported versions: {', '.join(tool_result['tls_versions'])}")
            
            summary.append("\n")
        
        return "\n".join(summary)
    
    def restore_target(self, text: str) -> str:
        """
        Restore placeholders back to real target (for final output)
        
        Args:
            text: Text with placeholders
        
        Returns:
            Text with real targets restored
        """
        if not text:
            return text
        
        result = text.replace(self.placeholder, self.target)
        result = result.replace(self.url_placeholder, f'http://{self.target}')
        
        return result


def sanitize_for_ai(target: str, results: Dict[str, Any]) -> Dict[str, str]:
    """
    Convenience function to sanitize results for AI analysis
    
    Args:
        target: The actual target to hide
        results: Raw scan results
    
    Returns:
        Dict with 'summary' (sanitized text) and 'data' (sanitized JSON)
    """
    sanitizer = TargetSanitizer(target)
    
    return {
        'summary': sanitizer.create_summary(results),
        'data': sanitizer.sanitize_results(results),
        'sanitizer': sanitizer  # Return for later restoration
    }

