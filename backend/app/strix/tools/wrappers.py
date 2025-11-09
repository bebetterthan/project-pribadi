"""
SUBFINDER Tool Wrapper
Subdomain enumeration tool
"""
import re
from typing import Dict, Any, Optional, List
from app.strix.tools.base import BaseTool, ToolCategory, ToolParameters
from app.utils.sanitizers import sanitize_target


class SubfinderTool(BaseTool):
    """
    Wrapper for subfinder - subdomain enumeration tool
    
    Purpose: Discover subdomains for a given domain
    Output: List of discovered subdomains
    """
    
    def __init__(self):
        super().__init__(
            tool_name="subfinder",
            category=ToolCategory.RECONNAISSANCE,
            description="Fast subdomain discovery tool",
            required_params=[]
        )
    
    def _build_command(self, params: ToolParameters) -> List[str]:
        """
        Build subfinder command
        
        Example: subfinder -d example.com -silent -o output.txt
        """
        command = [self.executable_path or "subfinder"]
        
        # Add domain
        command.extend(["-d", params.target])
        
        # Add options
        if params.options.get("silent", True):
            command.append("-silent")
        
        if params.options.get("recursive", False):
            command.append("-recursive")
        
        if "sources" in params.options:
            sources = params.options["sources"]
            if isinstance(sources, list):
                command.extend(["-sources", ",".join(sources)])
        
        # Add timeout
        if params.timeout:
            command.extend(["-timeout", str(params.timeout)])
        
        # JSON output
        command.append("-json")
        
        # Extra args
        command.extend(params.extra_args)
        
        return command
    
    def _parse_output(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """
        Parse subfinder JSON output
        
        Subfinder outputs one JSON object per line:
        {"host":"www.example.com","source":"crtsh"}
        {"host":"api.example.com","source":"virustotal"}
        """
        subdomains = []
        sources = {}
        
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            try:
                import json
                data = json.loads(line)
                host = data.get("host")
                source = data.get("source", "unknown")
                
                if host:
                    subdomains.append(host)
                    sources[source] = sources.get(source, 0) + 1
            except:
                # Fallback: treat as plain text subdomain
                if line and "." in line:
                    subdomains.append(line.strip())
        
        # Deduplicate
        subdomains = list(set(subdomains))
        
        return {
            "subdomains": sorted(subdomains),
            "count": len(subdomains),
            "sources": sources,
            "unique_sources": len(sources)
        }
    
    def _validate_target(self, target: str) -> tuple[bool, Optional[str]]:
        """
        Validate domain target
        
        Must be a valid domain name
        """
        try:
            # Remove protocol if present
            if "://" in target:
                target = target.split("://")[1]
            
            # Remove path if present
            if "/" in target:
                target = target.split("/")[0]
            
            # Basic domain validation
            domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
            if not re.match(domain_pattern, target):
                return False, f"Invalid domain format: {target}"
            
            return True, None
        except Exception as e:
            return False, f"Target validation error: {str(e)}"


class NmapTool(BaseTool):
    """
    Wrapper for nmap - network scanning tool
    
    Purpose: Port scanning and service detection
    Output: Open ports and service information
    """
    
    def __init__(self):
        super().__init__(
            tool_name="nmap",
            category=ToolCategory.ENUMERATION,
            description="Network exploration and security auditing",
            required_params=[]
        )
    
    def _build_command(self, params: ToolParameters) -> List[str]:
        """
        Build nmap command
        
        Example: nmap -sV -T4 example.com -oX output.xml
        """
        command = [self.executable_path or "nmap"]
        
        # Scan type
        scan_type = params.options.get("scan_type", "-sV")
        command.append(scan_type)
        
        # Timing
        timing = params.options.get("timing", "-T4")
        command.append(timing)
        
        # Ports
        if "ports" in params.options:
            command.extend(["-p", params.options["ports"]])
        
        # Scripts
        if "scripts" in params.options:
            scripts = params.options["scripts"]
            if isinstance(scripts, list):
                command.extend(["--script", ",".join(scripts)])
            else:
                command.extend(["--script", scripts])
        
        # Output format (XML for parsing)
        command.extend(["-oX", "-"])  # Output to stdout
        
        # Target
        command.append(params.target)
        
        # Extra args
        command.extend(params.extra_args)
        
        return command
    
    def _parse_output(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """
        Parse nmap XML output
        
        Extracts: open ports, services, versions
        """
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(stdout)
            
            results = {
                "hosts": [],
                "total_ports_found": 0,
                "services": {}
            }
            
            for host in root.findall(".//host"):
                host_data = {
                    "address": "",
                    "ports": []
                }
                
                # Get address
                addr = host.find(".//address[@addrtype='ipv4']")
                if addr is not None:
                    host_data["address"] = addr.get("addr")
                
                # Get ports
                for port in host.findall(".//port"):
                    state = port.find("state")
                    if state is not None and state.get("state") == "open":
                        service = port.find("service")
                        port_data = {
                            "port": port.get("portid"),
                            "protocol": port.get("protocol"),
                            "service": service.get("name") if service is not None else "unknown",
                            "version": service.get("product", "") if service is not None else ""
                        }
                        host_data["ports"].append(port_data)
                        
                        # Count services
                        svc_name = port_data["service"]
                        results["services"][svc_name] = results["services"].get(svc_name, 0) + 1
                
                if host_data["ports"]:
                    results["hosts"].append(host_data)
                    results["total_ports_found"] += len(host_data["ports"])
            
            return results
        except Exception as e:
            # Fallback: return error info
            return {
                "error": f"Failed to parse nmap output: {str(e)}",
                "raw_output_lines": len(stdout.split("\n"))
            }
    
    def _validate_target(self, target: str) -> tuple[bool, Optional[str]]:
        """
        Validate target (domain or IP)
        """
        # Simple validation - nmap accepts domains and IPs
        if not target or len(target) < 3:
            return False, "Target is too short"
        
        # Check for dangerous characters
        dangerous = [";", "|", "&", "`", "$", "(", ")", "<", ">"]
        for char in dangerous:
            if char in target:
                return False, f"Dangerous character detected: {char}"
        
        return True, None
