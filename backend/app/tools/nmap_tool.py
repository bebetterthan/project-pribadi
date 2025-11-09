from typing import Dict, Any, List
import subprocess
import xmltodict
from app.tools.base import BaseTool


class NmapTool(BaseTool):
    """Nmap network scanner wrapper"""

    def __init__(self):
        super().__init__()
        self.name = "nmap"
        self.timeout = 600  # 10 minutes for aggressive scans

    def is_installed(self) -> bool:
        try:
            # Try multiple possible nmap paths
            paths = [
                'nmap',
                'C:\\Program Files (x86)\\Nmap\\nmap.exe',
                'C:\\Program Files\\Nmap\\nmap.exe'
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '--version'],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return True
                except:
                    continue
            return False
        except:
            return False

    def build_command(self, target: str, profile: str) -> List[str]:
        """Build nmap command based on profile"""
        # Try to find nmap executable
        nmap_cmd = 'nmap'
        paths = [
            'C:\\Program Files (x86)\\Nmap\\nmap.exe',
            'C:\\Program Files\\Nmap\\nmap.exe'
        ]
        for path in paths:
            try:
                result = subprocess.run([path, '--version'], capture_output=True, timeout=2)
                if result.returncode == 0:
                    nmap_cmd = path
                    break
            except:
                continue

        cmd = [nmap_cmd]

        if profile == 'quick':
            # Fast scan - top 100 ports
            cmd.extend(['-F', '-sV'])
        elif profile == 'aggressive':
            # Aggressive scan
            cmd.extend(['-A', '-T4'])
        else:  # normal
            # Default ports with version detection
            cmd.extend(['-sV', '-sC'])

        # Output as XML to stdout
        cmd.extend(['-oX', '-'])
        cmd.append(target)

        return cmd

    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse nmap XML output"""
        try:
            data = xmltodict.parse(stdout)
            nmaprun = data.get('nmaprun', {})
            host = nmaprun.get('host', {})

            # Extract open ports
            open_ports = []
            ports = host.get('ports', {}).get('port', [])

            # Handle single port (not a list)
            if isinstance(ports, dict):
                ports = [ports]

            for port in ports:
                state = port.get('state', {})
                if state.get('@state') == 'open':
                    service = port.get('service', {})
                    open_ports.append({
                        'port': port.get('@portid'),
                        'protocol': port.get('@protocol'),
                        'service': service.get('@name', 'unknown'),
                        'version': service.get('@product', '') + ' ' + service.get('@version', ''),
                        'extrainfo': service.get('@extrainfo', '')
                    })

            # Extract OS detection
            os_match = None
            os_info = host.get('os', {}).get('osmatch', [])
            if os_info:
                if isinstance(os_info, list):
                    os_match = os_info[0].get('@name')
                else:
                    os_match = os_info.get('@name')

            return {
                'open_ports': open_ports,
                'os_detection': os_match,
                'host_status': host.get('status', {}).get('@state'),
                'scan_type': nmaprun.get('@args')
            }
        except Exception as e:
            return {'error': f"Failed to parse nmap output: {str(e)}"}
