"""
Mock tools for development/testing without actual tool installation
"""
from typing import Dict, Any, List
import time
from app.tools.base import BaseTool, ToolResult


class MockNmapTool(BaseTool):
    """Mock Nmap tool for development"""

    def __init__(self):
        super().__init__()
        self.name = "nmap"
        self.timeout = 60

    def is_installed(self) -> bool:
        return True

    def build_command(self, target: str, profile: str) -> List[str]:
        return ['echo', 'mock nmap']

    def parse_output(self, stdout: str) -> Dict[str, Any]:
        return {
            'open_ports': [
                {'port': '80', 'protocol': 'tcp', 'service': 'http', 'version': 'nginx 1.18.0'},
                {'port': '443', 'protocol': 'tcp', 'service': 'https', 'version': 'nginx 1.18.0'},
                {'port': '22', 'protocol': 'tcp', 'service': 'ssh', 'version': 'OpenSSH 8.2p1'}
            ],
            'os_detection': 'Linux 5.4',
            'host_status': 'up',
            'scan_type': 'mock scan'
        }

    def execute(self, target: str, profile: str = 'normal') -> ToolResult:
        """Mock execution"""
        time.sleep(2)  # Simulate scan time
        return ToolResult(
            tool_name=self.name,
            exit_code=0,
            stdout="Mock Nmap scan completed",
            stderr="",
            execution_time=2.0,
            parsed_data=self.parse_output("")
        )


class MockNucleiTool(BaseTool):
    """Mock Nuclei tool for development"""

    def __init__(self):
        super().__init__()
        self.name = "nuclei"
        self.timeout = 60

    def is_installed(self) -> bool:
        return True

    def build_command(self, target: str, profile: str) -> List[str]:
        return ['echo', 'mock nuclei']

    def parse_output(self, stdout: str, target: str = '') -> Dict[str, Any]:
        return {
            'findings': [
                {
                    'template_id': 'CVE-2021-41773',
                    'template_name': 'Apache Path Traversal',
                    'severity': 'critical',
                    'matched_at': f'https://{target}/cgi-bin/.%2e/' if target else 'https://example.com/cgi-bin/.%2e/',
                    'cve_id': 'CVE-2021-41773',
                    'description': 'Apache HTTP Server 2.4.49 path traversal'
                },
                {
                    'template_id': 'exposed-git-config',
                    'template_name': 'Exposed Git Config',
                    'severity': 'medium',
                    'matched_at': f'https://{target}/.git/config' if target else 'https://example.com/.git/config',
                    'cve_id': None,
                    'description': 'Git configuration file exposed'
                }
            ],
            'total_findings': 2,
            'severity_count': {'critical': 1, 'high': 0, 'medium': 1, 'low': 0}
        }

    def execute(self, target: str, profile: str = 'normal') -> ToolResult:
        """Mock execution"""
        time.sleep(3)  # Simulate scan time
        parsed_data = self.parse_output("mock output", target)
        return ToolResult(
            tool_name=self.name,
            exit_code=0,
            stdout="Mock Nuclei scan completed",
            stderr="",
            execution_time=3.0,
            parsed_data=parsed_data
        )


class MockWhatwebTool(BaseTool):
    """Mock WhatWeb tool for development"""

    def __init__(self):
        super().__init__()
        self.name = "whatweb"
        self.timeout = 30

    def is_installed(self) -> bool:
        return True

    def build_command(self, target: str, profile: str) -> List[str]:
        return ['echo', 'mock whatweb']

    def parse_output(self, stdout: str, target: str = '') -> Dict[str, Any]:
        target_url = f'http://{target}' if target and not target.startswith('http') else (target if target else 'http://example.com')
        return {
            'technologies': {
                'server': 'nginx/1.18.0',
                'cms': 'WordPress',
                'language': 'PHP',
                'js_frameworks': ['jQuery', 'Bootstrap'],
                'meta_info': {
                    'title': 'Example Website',
                    'country': 'US'
                }
            },
            'all_plugins': ['HTTPServer', 'nginx', 'WordPress', 'PHP', 'jQuery', 'Bootstrap'],
            'target_url': target_url
        }

    def execute(self, target: str, profile: str = 'normal') -> ToolResult:
        """Mock execution"""
        time.sleep(1)  # Simulate scan time
        if not target.startswith(('http://', 'https://')):
            target = f'http://{target}'

        parsed_data = self.parse_output("mock output", target)
        return ToolResult(
            tool_name=self.name,
            exit_code=0,
            stdout="Mock WhatWeb scan completed",
            stderr="",
            execution_time=1.0,
            parsed_data=parsed_data
        )


class MockSSLScanTool(BaseTool):
    """Mock SSLScan tool for development"""

    def __init__(self):
        super().__init__()
        self.name = "sslscan"
        self.timeout = 30

    def is_installed(self) -> bool:
        return True

    def build_command(self, target: str, profile: str) -> List[str]:
        return ['echo', 'mock sslscan']

    def parse_output(self, stdout: str) -> Dict[str, Any]:
        return {
            'certificate': {
                'valid': True,
                'subject': 'CN=example.com',
                'issuer': 'CN=Let\'s Encrypt Authority',
                'not_valid_before': '2024-01-01',
                'not_valid_after': '2025-01-01',
                'signature_algorithm': 'sha256WithRSAEncryption'
            },
            'weak_ciphers': [
                {'name': 'TLS_RSA_WITH_3DES_EDE_CBC_SHA', 'strength': 'weak', 'sslversion': 'TLSv1.0'}
            ],
            'strong_ciphers': [
                {'name': 'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384', 'strength': 'strong', 'sslversion': 'TLSv1.3'}
            ],
            'vulnerabilities': ['1 Weak Ciphers Detected'],
            'total_ciphers_tested': 2
        }

    def execute(self, target: str, profile: str = 'normal') -> ToolResult:
        """Mock execution"""
        time.sleep(1.5)  # Simulate scan time
        target = target.replace('https://', '').replace('http://', '')

        return ToolResult(
            tool_name=self.name,
            exit_code=0,
            stdout="Mock SSLScan completed",
            stderr="",
            execution_time=1.5,
            parsed_data=self.parse_output(target)
        )
