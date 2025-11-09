"""
ffuf Tool - Fast Web Fuzzer (Content Discovery)
Fase 3.6: Essential Security Toolchain
"""

import subprocess
import json
import time
import os
from typing import List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger

class FfufTool(BaseTool):
    """ffuf web content discovery wrapper"""
    
    def __init__(self):
        super().__init__()
        self.name = "ffuf"
        self.timeout = 900  # 15 minutes max for deep scans
        self.wordlist_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'wordlists')
        
    def is_installed(self) -> bool:
        """Check if ffuf is installed"""
        try:
            paths = [
                'D:\\Project pribadi\\AI_Pentesting\\tools\\ffuf.exe',
                'ffuf',
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '-V'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0 or 'ffuf' in result.stdout.lower():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _get_ffuf_path(self) -> str:
        """Get ffuf executable path"""
        paths = [
            'D:\\Project pribadi\\AI_Pentesting\\tools\\ffuf.exe',
            'ffuf',
        ]
        for path in paths:
            try:
                result = subprocess.run(
                    [path, '-V'], 
                    capture_output=True, 
                    timeout=2,
                    text=True
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        return 'ffuf'
    
    def _get_wordlist_path(self, size: str) -> str:
        """Get wordlist path based on size"""
        wordlist_map = {
            'quick': 'common.txt',  # Minimal wordlist (bundled)
            'standard': 'common.txt',  # Use common for now
            'deep': 'common.txt',  # Use common for now (user can add bigger wordlists later)
        }
        
        wordlist_file = wordlist_map.get(size, 'common.txt')
        wordlist_path = os.path.join(self.wordlist_dir, wordlist_file)
        
        # Check if wordlist exists
        if not os.path.exists(wordlist_path):
            logger.warning(f"Wordlist not found: {wordlist_path}, using default")
            # Return a minimal inline wordlist as fallback
            return None
        
        return wordlist_path
    
    def build_command(self, target: str, profile: str = 'normal') -> List[str]:
        """
        Build ffuf command
        
        Args:
            target: Target URL with FUZZ placeholder (e.g., https://example.com/FUZZ)
            profile: Scan profile (quick/standard/deep)
        """
        ffuf_cmd = self._get_ffuf_path()
        
        # Get wordlist
        wordlist_size_map = {
            'quick': 'quick',
            'normal': 'standard',
            'aggressive': 'deep',
        }
        wordlist_size = wordlist_size_map.get(profile, 'standard')
        wordlist_path = self._get_wordlist_path(wordlist_size)
        
        if not wordlist_path:
            raise FileNotFoundError("Wordlist not found. Please ensure wordlists are in backend/wordlists/")
        
        cmd = [
            ffuf_cmd,
            '-u', target,  # URL with FUZZ placeholder
            '-w', wordlist_path,  # Wordlist
            '-mc', '200,204,301,302,307,401,403',  # Match these status codes
            '-t', '40',  # Threads
            '-timeout', '10',  # 10s timeout per request
            '-o', '-',  # Output to stdout
            '-of', 'json',  # JSON output
            '-s',  # Silent mode (no banner)
        ]
        
        return cmd
    
    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """
        Parse ffuf JSON output
        
        Output format: JSON object
        {"results":[{"input":{"FUZZ":"admin"},"status":302,"url":"https://example.com/admin"}]}
        """
        try:
            data = json.loads(stdout) if stdout.strip() else {}
            
            if not data or 'results' not in data:
                return {
                    'total_requests': 0,
                    'total_found': 0,
                    'discovered_paths': [],
                    'summary': 'No paths discovered'
                }
            
            results = data.get('results', [])
            discovered_paths = []
            
            # Risk level mapping
            def get_risk_level(path: str, status: int) -> str:
                path_lower = path.lower()
                
                # Critical indicators
                if any(x in path_lower for x in ['backup', '.zip', '.sql', '.git', '.env', '.config', 'database', 'db.', 'admin.', 'root.']):
                    return 'critical'
                
                # High indicators
                if any(x in path_lower for x in ['admin', 'panel', 'dashboard', 'phpmyadmin', '.log', 'error', 'debug']):
                    return 'high'
                
                # Medium indicators
                if any(x in path_lower for x in ['api', 'upload', 'file', 'temp', 'test', 'dev']):
                    return 'medium'
                
                # Low indicators
                return 'low'
            
            for result in results:
                input_data = result.get('input', {})
                fuzz_value = input_data.get('FUZZ', '')
                status = result.get('status', 0)
                url = result.get('url', '')
                length = result.get('length', 0)
                redirect = result.get('redirectlocation', '')
                
                path = f"/{fuzz_value}"
                risk = get_risk_level(path, status)
                
                discovered_paths.append({
                    'path': path,
                    'full_url': url,
                    'status_code': status,
                    'size_bytes': length,
                    'risk_level': risk,
                    'redirect_to': redirect if redirect else None,
                })
            
            # Sort by risk level
            risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            discovered_paths.sort(key=lambda x: risk_order.get(x['risk_level'], 4))
            
            # Extract interesting findings
            interesting = [p for p in discovered_paths if p['risk_level'] in ['critical', 'high']]
            
            return {
                'total_requests': data.get('config', {}).get('wordlist_size', len(results)),
                'total_found': len(discovered_paths),
                'discovered_paths': discovered_paths,
                'interesting_findings': [f"{p['path']} ({p['risk_level'].upper()})" for p in interesting],
                'summary': f"Discovered {len(discovered_paths)} paths ({len(interesting)} high-risk)"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ffuf JSON: {e}")
            return {
                'error': f"JSON parse error: {str(e)}",
                'raw_output': stdout[:500]
            }
        except Exception as e:
            logger.error(f"Failed to parse ffuf output: {e}")
            return {
                'error': f"Parse error: {str(e)}",
                'raw_output': stdout[:500]
            }

