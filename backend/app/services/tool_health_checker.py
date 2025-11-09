"""
Tool Health Checker - Verify all pentesting tools are available and healthy
"""
import subprocess
import shutil
from typing import Dict, Any, List
from dataclasses import dataclass
from app.utils.logger import logger


@dataclass
class ToolHealthStatus:
    """Health status for a tool"""
    tool_name: str
    is_installed: bool
    version: str = "unknown"
    install_path: str = "not found"
    health_status: str = "unknown"  # healthy, degraded, unavailable
    error_message: str = None


class ToolHealthChecker:
    """
    Check health of all pentesting tools
    
    Used by:
    - Application startup (verify all tools before accepting requests)
    - Health check endpoint (/health)
    - Tool Registry (before registering tools)
    """
    
    @staticmethod
    def check_nmap() -> ToolHealthStatus:
        """Check Nmap installation and health"""
        tool_name = "nmap"
        
        # Try to find nmap
        nmap_path = shutil.which("nmap")
        if not nmap_path:
            # Try common Windows paths
            common_paths = [
                "C:\\Program Files (x86)\\Nmap\\nmap.exe",
                "C:\\Program Files\\Nmap\\nmap.exe"
            ]
            for path in common_paths:
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0:
                        nmap_path = path
                        break
                except:
                    continue
        
        if not nmap_path:
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=False,
                health_status="unavailable",
                error_message="Nmap not found in PATH or common installation directories"
            )
        
        # Get version
        try:
            result = subprocess.run(
                [nmap_path, "--version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
            
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=True,
                version=version_line.strip(),
                install_path=nmap_path,
                health_status="healthy"
            )
        except Exception as e:
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=True,
                install_path=nmap_path,
                health_status="degraded",
                error_message=f"Nmap found but version check failed: {str(e)}"
            )
    
    @staticmethod
    def check_nuclei() -> ToolHealthStatus:
        """Check Nuclei installation and health"""
        tool_name = "nuclei"
        
        # Try common paths first (project folder prioritized)
        common_paths = [
            "D:\\Project pribadi\\AI_Pentesting\\tools\\nuclei.exe",  # Project tools folder (portable)
            "C:\\Tools\\nuclei.exe",  # System installation
            "C:\\PentestTools\\nuclei.exe"  # Alternative
        ]
        
        nuclei_path = None
        for path in common_paths:
            try:
                # Direct test by running the command
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                # Nuclei always returns 0 and outputs version info to stderr
                if result.returncode == 0 and (result.stderr or result.stdout):
                    nuclei_path = path
                    break
            except (FileNotFoundError, PermissionError, OSError):
                # File doesn't exist or can't be executed
                continue
            except subprocess.TimeoutExpired:
                # Timeout - tool exists but hung
                nuclei_path = path
                break
            except Exception as e:
                # Unknown error - log and continue
                logger.debug(f"Error checking Nuclei at {path}: {e}")
                continue
        
        # If not found in common paths, try PATH
        if not nuclei_path:
            nuclei_path = shutil.which("nuclei")
        
        if not nuclei_path:
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=False,
                health_status="unavailable",
                error_message="Nuclei not found. Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
            )
        
        # Get version (Nuclei outputs to STDERR!)
        try:
            result = subprocess.run(
                [nuclei_path, "-version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            # Parse version from stderr (Nuclei uses stderr for informational output)
            output = result.stderr + result.stdout
            version = "v3.x"  # Default
            
            # Extract version from output like "[INF] Nuclei Engine Version: v3.3.7"
            import re
            version_match = re.search(r'Version:\s*(v[\d.]+)', output)
            if version_match:
                version = version_match.group(1)
            
            # Check templates availability
            try:
                # Try a dry-run to check templates
                test_result = subprocess.run(
                    [nuclei_path, "-list", "-silent"],
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                templates_ok = test_result.returncode == 0
            except:
                templates_ok = False
            
            health = "healthy" if templates_ok else "degraded"
            error = None if templates_ok else "Templates not found. Run: nuclei -update-templates"
            
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=True,
                version=version,
                install_path=nuclei_path,
                health_status=health,
                error_message=error
            )
        except Exception as e:
            return ToolHealthStatus(
                tool_name=tool_name,
                is_installed=True,
                install_path=nuclei_path,
                health_status="degraded",
                error_message=f"Nuclei found but health check failed: {str(e)}"
            )
    
    @staticmethod
    def check_all_tools() -> Dict[str, ToolHealthStatus]:
        """
        Check health of all tools
        
        Returns:
            Dictionary mapping tool name to health status
        """
        logger.info("🔍 Checking health of all pentesting tools...")
        
        results = {}
        
        # Check Nmap
        nmap_status = ToolHealthChecker.check_nmap()
        results['nmap'] = nmap_status
        if nmap_status.is_installed:
            logger.info(f"✅ Nmap: {nmap_status.health_status} - {nmap_status.version}")
        else:
            logger.warning(f"⚠️ Nmap: {nmap_status.health_status} - {nmap_status.error_message}")
        
        # Check Nuclei
        nuclei_status = ToolHealthChecker.check_nuclei()
        results['nuclei'] = nuclei_status
        if nuclei_status.is_installed:
            logger.info(f"✅ Nuclei: {nuclei_status.health_status} at {nuclei_status.install_path}")
            if nuclei_status.error_message:
                logger.warning(f"   ⚠️ Warning: {nuclei_status.error_message}")
        else:
            logger.warning(f"⚠️ Nuclei: {nuclei_status.health_status} - {nuclei_status.error_message}")
        
        # Summary
        healthy_count = sum(1 for s in results.values() if s.health_status == "healthy")
        total_count = len(results)
        
        logger.info(f"📊 Tool Health Summary: {healthy_count}/{total_count} tools healthy")
        
        return results
    
    @staticmethod
    def get_health_summary() -> Dict[str, Any]:
        """
        Get summary for health check endpoint
        
        Returns:
            Dictionary with overall status and per-tool status
        """
        statuses = ToolHealthChecker.check_all_tools()
        
        overall_status = "healthy"
        if any(s.health_status == "unavailable" for s in statuses.values()):
            overall_status = "degraded"
        elif any(s.health_status == "degraded" for s in statuses.values()):
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "tools": {
                name: {
                    "status": status.health_status,
                    "installed": status.is_installed,
                    "version": status.version,
                    "path": status.install_path,
                    "error": status.error_message
                }
                for name, status in statuses.items()
            }
        }

