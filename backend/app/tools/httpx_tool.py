"""
httpx Tool - Fast HTTP Probe
Fase 3.6: Essential Security Toolchain
"""

import subprocess
import json
import time
from typing import List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger

class HttpxTool(BaseTool):
    """httpx quick HTTP probe wrapper"""
    
    def __init__(self):
        super().__init__()
        self.name = "httpx"
        self.timeout = 300  # 5 minutes for probing (increased for bulk targets)
        
    def is_installed(self) -> bool:
        """Check if httpx is installed"""
        try:
            paths = [
                'D:\\Project pribadi\\AI_Pentesting\\tools\\httpx.exe',
                'httpx',
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '-version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0 or 'httpx' in result.stdout.lower():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _get_httpx_path(self) -> str:
        """Get the correct httpx executable path"""
        paths = [
            'D:\\Project pribadi\\AI_Pentesting\\tools\\httpx.exe',
            'httpx',
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
        return 'httpx'
    
    def build_command(self, targets: List[str], profile: str = 'normal') -> List[str]:
        """
        Build httpx command
        
        Args:
            targets: List of hosts to probe
            profile: Not used for httpx (always quick)
        """
        httpx_cmd = self._get_httpx_path()
        
        # httpx expects stdin input for bulk probing
        # We'll write targets to a temp file
        import tempfile
        import os
        
        # Create temp file with targets
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for target in targets:
                f.write(f"{target}\n")
            temp_file = f.name
        
        cmd = [
            httpx_cmd,
            '-l', temp_file,  # Input from file
            '-silent',  # No banner
            '-json',  # JSON output
            '-timeout', '10',  # 10s per host (increased for reliability)
            '-follow-redirects',  # Follow redirects
            '-status-code',  # Include status code
            '-title',  # Include page title
            '-tech-detect',  # Basic tech detection
            '-threads', '50',  # Parallel threads for speed (OPTIMIZATION!)
            '-retries', '2',  # Retry failed requests
        ]
        
        return cmd
    
    def execute(self, targets: List[str], profile: str = 'normal') -> ToolResult:
        """Execute httpx with cleanup"""
        import os
        import tempfile
        
        # Build command (creates temp file)
        cmd = self.build_command(targets, profile)
        
        # Extract temp file path from command
        temp_file = cmd[cmd.index('-l') + 1]
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False
            )
            
            execution_time = time.time() - start_time
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            
            parsed = None
            if result.returncode == 0:
                try:
                    parsed = self.parse_output(result.stdout)
                except Exception as e:
                    parsed = {"parse_error": str(e)}
            
            return ToolResult(
                tool_name=self.name,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                parsed_data=parsed
            )
            
        except subprocess.TimeoutExpired:
            # Clean up temp file on timeout
            try:
                os.unlink(temp_file)
            except:
                pass
            
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout} seconds",
                execution_time=execution_time
            )
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_file)
            except:
                pass
            
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time
            )
    
    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """
        Parse httpx JSON output
        
        Output format: JSONL (one JSON per line)
        {"url":"https://www.example.com","status_code":200,"title":"Home","tech":["nginx"]}
        """
        try:
            results = []
            alive_hosts = []
            dead_hosts = []
            
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    
                    url = data.get('url', '')
                    status_code = data.get('status_code', 0)
                    title = data.get('title', '')
                    tech = data.get('tech', [])
                    failed = data.get('failed', False)
                    
                    if failed or status_code == 0:
                        dead_hosts.append(data.get('host', url))
                    else:
                        alive_hosts.append(url)
                        results.append({
                            'url': url,
                            'status_code': status_code,
                            'title': title,
                            'tech': tech,
                            'reachable': True
                        })
                        
                except json.JSONDecodeError:
                    continue
            
            return {
                'total_probed': len(results) + len(dead_hosts),
                'alive': len(alive_hosts),
                'dead': len(dead_hosts),
                'results': results,
                'alive_hosts': alive_hosts,
                'summary': f"Probed {len(results) + len(dead_hosts)} hosts: {len(alive_hosts)} alive, {len(dead_hosts)} dead"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse httpx output: {e}")
            return {
                'error': f"Failed to parse output: {str(e)}",
                'raw_output': stdout[:500]
            }

