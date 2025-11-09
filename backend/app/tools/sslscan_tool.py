from typing import Dict, Any, List
import subprocess
import xmltodict
from app.tools.base import BaseTool


class SSLScanTool(BaseTool):
    """sslscan SSL/TLS scanner wrapper"""

    def __init__(self):
        super().__init__()
        self.name = "sslscan"
        self.timeout = 120  # 2 minutes

    def is_installed(self) -> bool:
        try:
            result = subprocess.run(
                ['sslscan', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def build_command(self, target: str, profile: str) -> List[str]:
        """Build sslscan command"""
        # Remove protocol if present
        target = target.replace('https://', '').replace('http://', '')

        cmd = ['sslscan', '--xml=-', target]

        return cmd

    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse sslscan XML output"""
        try:
            data = xmltodict.parse(stdout)
            ssltest = data.get('document', {}).get('ssltest', {})

            # Extract certificate info
            certificate = {}
            cert_data = ssltest.get('certificate', {})
            if cert_data:
                certificate = {
                    'valid': True,
                    'subject': cert_data.get('subject', ''),
                    'issuer': cert_data.get('issuer', ''),
                    'not_valid_before': cert_data.get('not-valid-before', ''),
                    'not_valid_after': cert_data.get('not-valid-after', ''),
                    'signature_algorithm': cert_data.get('signature-algorithm', '')
                }

            # Extract cipher information
            ciphers = ssltest.get('cipher', [])
            if not isinstance(ciphers, list):
                ciphers = [ciphers] if ciphers else []

            weak_ciphers = []
            strong_ciphers = []

            for cipher in ciphers:
                if cipher.get('@status') == 'accepted':
                    strength = cipher.get('@strength', '')
                    cipher_info = {
                        'name': cipher.get('@cipher', ''),
                        'strength': strength,
                        'sslversion': cipher.get('@sslversion', '')
                    }

                    if strength in ['weak', 'medium']:
                        weak_ciphers.append(cipher_info)
                    else:
                        strong_ciphers.append(cipher_info)

            # Check for vulnerabilities
            vulnerabilities = []

            # Check for SSLv2/SSLv3 (vulnerable)
            for cipher in ciphers:
                if cipher.get('@sslversion') in ['SSLv2', 'SSLv3']:
                    if 'SSLv2/SSLv3 Enabled' not in vulnerabilities:
                        vulnerabilities.append('SSLv2/SSLv3 Enabled (INSECURE)')

            # Check for weak ciphers
            if weak_ciphers:
                vulnerabilities.append(f'{len(weak_ciphers)} Weak Ciphers Detected')

            return {
                'certificate': certificate,
                'weak_ciphers': weak_ciphers,
                'strong_ciphers': strong_ciphers,
                'vulnerabilities': vulnerabilities,
                'total_ciphers_tested': len(ciphers)
            }
        except Exception as e:
            return {'error': f"Failed to parse sslscan output: {str(e)}"}
