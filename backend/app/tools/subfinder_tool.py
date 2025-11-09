"""
Subfinder Tool - Subdomain Enumeration
Fase 3.6: Essential Security Toolchain
"""

import subprocess
import json
import time
from typing import List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger

class SubfinderTool(BaseTool):
    """Subfinder subdomain enumeration wrapper"""
    
    def __init__(self):
        super().__init__()
        self.name = "subfinder"
        self.timeout = 300  # 5 minutes max for subdomain discovery
        
    def is_installed(self) -> bool:
        """Check if Subfinder is installed"""
        try:
            paths = [
                'D:\\Project pribadi\\AI_Pentesting\\tools\\subfinder.exe',
                'subfinder',  # If in PATH
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '-version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0 or 'subfinder' in result.stdout.lower():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _get_subfinder_path(self) -> str:
        """Get the correct subfinder executable path"""
        paths = [
            'D:\\Project pribadi\\AI_Pentesting\\tools\\subfinder.exe',
            'subfinder',
        ]
        for path in paths:
            try:
                result = subprocess.run(
                    [path, '-version'], 
                    capture_output=True, 
                    timeout=2,
                    text=True
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        return 'subfinder'
    
    def build_command(self, target: str, profile: str = 'normal') -> List[str]:
        """
        Build subfinder command
        
        Args:
            target: Domain to enumerate (e.g., 'example.com')
            profile: 'quick' (60s), 'normal' (180s), 'deep' (300s)
        """
        subfinder_cmd = self._get_subfinder_path()
        
        # Base command
        cmd = [
            subfinder_cmd,
            '-d', target,
            '-silent',  # Silent mode (no banner)
            '-json',  # JSON output
            '-recursive',  # Find subdomains recursively
        ]
        
        # Timeout based on profile
        if profile == 'quick':
            cmd.extend(['-timeout', '60'])
        elif profile == 'deep':
            cmd.extend(['-timeout', '300'])
        else:  # normal
            cmd.extend(['-timeout', '180'])
        
        # Sources (all free sources)
        cmd.extend([
            '-all',  # Use all sources
        ])
        
        return cmd
    
    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """
        Parse Subfinder JSON output
        
        Output format: JSONL (one JSON object per line)
        {"host":"www.example.com","source":"crtsh"}
        {"host":"api.example.com","source":"censys"}
        """
        try:
            subdomains = []
            sources_used = set()
            
            # Parse JSONL (each line is a JSON object)
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    subdomain = data.get('host', '')
                    source = data.get('source', 'unknown')
                    
                    if subdomain:
                        subdomains.append({
                            'subdomain': subdomain,
                            'source': source
                        })
                        sources_used.add(source)
                except json.JSONDecodeError:
                    # Skip invalid lines
                    continue
            
            # Remove duplicates (keep first occurrence)
            seen = set()
            unique_subdomains = []
            for sub in subdomains:
                if sub['subdomain'] not in seen:
                    seen.add(sub['subdomain'])
                    unique_subdomains.append(sub)
            
            # Identify interesting subdomains
            interesting_keywords = ['dev', 'staging', 'test', 'admin', 'api', 'vpn', 'mail', 'beta', 'demo', 'internal']
            interesting_findings = []
            
            for sub in unique_subdomains:
                subdomain = sub['subdomain'].lower()
                for keyword in interesting_keywords:
                    if keyword in subdomain:
                        interesting_findings.append(f"{sub['subdomain']} ({keyword} - potential high-value target)")
                        break
            
            return {
                'total_subdomains': len(unique_subdomains),
                'subdomains': unique_subdomains,
                'sources_used': list(sources_used),
                'interesting_findings': interesting_findings,
                'summary': f"Discovered {len(unique_subdomains)} subdomains using {len(sources_used)} sources"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Subfinder output: {e}")
            return {
                'error': f"Failed to parse output: {str(e)}",
                'raw_output': stdout[:500]  # First 500 chars for debugging
            }

