"""
WhatWeb Tool - Technology Detection
Fase 3.6: Essential Security Toolchain
Note: WhatWeb is Ruby-based, check if installed via gem or standalone
"""

import subprocess
import json
import time
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger

class WhatWebTool(BaseTool):
    """WhatWeb technology detection wrapper"""
    
    def __init__(self):
        super().__init__()
        self.name = "whatweb"
        self.timeout = 60  # 1 minute for tech detection
        
    def is_installed(self) -> bool:
        """Check if WhatWeb is installed"""
        try:
            paths = [
                'D:\\Project pribadi\\AI_Pentesting\\tools\\whatweb\\whatweb',  # Windows Ruby script
                'whatweb',  # In PATH
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '--version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if 'whatweb' in result.stdout.lower() or 'whatweb' in result.stderr.lower():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _get_whatweb_path(self) -> str:
        """Get WhatWeb executable path"""
        paths = [
            'D:\\Project pribadi\\AI_Pentesting\\tools\\whatweb\\whatweb',
            'whatweb',
        ]
        for path in paths:
            try:
                result = subprocess.run(
                    [path, '--version'], 
                    capture_output=True, 
                    timeout=2,
                    text=True
                )
                if result.returncode == 0 or 'whatweb' in result.stdout.lower():
                    return path
            except:
                continue
        return 'whatweb'
    
    def build_command(self, target: str, profile: str = 'normal') -> List[str]:
        """
        Build WhatWeb command
        
        Args:
            target: Target URL
            profile: Scan profile (maps to aggression level)
        """
        whatweb_cmd = self._get_whatweb_path()
        
        # Map profile to aggression level
        aggression_map = {
            'quick': 1,  # Stealthy
            'normal': 3,  # Aggressive (standard)
            'aggressive': 4,  # Heavy
        }
        aggression = aggression_map.get(profile, 3)
        
        cmd = [
            whatweb_cmd,
            target,
            '-a', str(aggression),  # Aggression level
            '--log-json=-',  # Output JSON to stdout
            '--quiet',  # Suppress banner
            '--color=never',  # No ANSI colors
        ]
        
        return cmd
    
    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """
        Parse WhatWeb JSON output
        
        Output format: JSON array
        [{"target":"https://example.com","plugins":{"WordPress":{"version":["6.4.2"]}}}]
        """
        try:
            # WhatWeb outputs JSON array
            data = json.loads(stdout) if stdout.strip() else []
            
            if not data or len(data) == 0:
                return {
                    'error': 'No data returned',
                    'url': '',
                    'technologies': []
                }
            
            result = data[0]  # First (and usually only) result
            target = result.get('target', '')
            plugins = result.get('plugins', {})
            
            # Extract key technologies
            cms = None
            server = None
            frameworks = []
            languages = []
            
            # Common CMS
            for cms_name in ['WordPress', 'Drupal', 'Joomla', 'Magento']:
                if cms_name in plugins:
                    plugin_data = plugins[cms_name]
                    version = plugin_data.get('version', ['unknown'])[0] if 'version' in plugin_data else 'unknown'
                    cms = {'name': cms_name, 'version': version}
                    break
            
            # Server
            if 'nginx' in plugins:
                server = {'name': 'nginx', 'version': plugins['nginx'].get('version', [''])[0]}
            elif 'Apache' in plugins:
                server = {'name': 'Apache', 'version': plugins['Apache'].get('version', [''])[0]}
            elif 'Microsoft-IIS' in plugins:
                server = {'name': 'IIS', 'version': plugins['Microsoft-IIS'].get('version', [''])[0]}
            
            # Frameworks
            for fw in ['jQuery', 'React', 'Vue', 'Angular', 'Bootstrap']:
                if fw in plugins:
                    version = plugins[fw].get('version', [''])[0]
                    frameworks.append({'name': fw, 'version': version})
            
            # Languages
            if 'PHP' in plugins:
                languages.append('PHP')
            if 'ASP.NET' in plugins or 'ASP-NET' in plugins:
                languages.append('ASP.NET')
            if 'Python' in plugins:
                languages.append('Python')
            
            # Count total plugins detected
            total_plugins = len(plugins)
            
            return {
                'url': target,
                'cms': cms,
                'server': server,
                'frameworks': frameworks,
                'languages': languages,
                'total_plugins_detected': total_plugins,
                'all_plugins': list(plugins.keys()),
                'summary': f"Detected: {cms['name'] if cms else 'No CMS'}, {server['name'] if server else 'Unknown server'}, {len(frameworks)} frameworks"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WhatWeb JSON: {e}")
            return {
                'error': f"JSON parse error: {str(e)}",
                'raw_output': stdout[:500]
            }
        except Exception as e:
            logger.error(f"Failed to parse WhatWeb output: {e}")
            return {
                'error': f"Parse error: {str(e)}",
                'raw_output': stdout[:500]
            }
