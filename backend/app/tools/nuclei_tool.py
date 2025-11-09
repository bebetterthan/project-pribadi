from typing import Dict, Any, List
import subprocess
import json
from app.tools.base import BaseTool


class NucleiTool(BaseTool):
    """Nuclei vulnerability scanner wrapper"""

    def __init__(self):
        super().__init__()
        self.name = "nuclei"
        self.timeout = 900  # 15 minutes for aggressive scans

    def is_installed(self) -> bool:
        try:
            # Try multiple possible nuclei paths (updated for actual installation)
            paths = [
                'D:\\Project pribadi\\AI_Pentesting\\tools\\nuclei.exe',
                'nuclei',
                'C:\\Tools\\nuclei.exe',
                'C:\\PentestTools\\nuclei.exe'
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, '-version'],
                        capture_output=True,
                        timeout=5
                    )
                    # Nuclei returns 0 even with -version
                    if result.returncode == 0 or 'nuclei' in result.stdout.decode().lower():
                        return True
                except:
                    continue
            return False
        except:
            return False

    def _get_nuclei_path(self) -> str:
        """Get the correct nuclei executable path"""
        paths = [
            'D:\\Project pribadi\\AI_Pentesting\\tools\\nuclei.exe',  # Project tools folder
            'C:\\Tools\\nuclei.exe',  # System installation
            'nuclei',  # If in PATH
            'C:\\PentestTools\\nuclei.exe'  # Fallback
        ]
        for path in paths:
            try:
                result = subprocess.run(
                    [path, '-version'],
                    capture_output=True,
                    timeout=2,
                    stderr=subprocess.STDOUT
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        return 'nuclei'  # Default fallback

    def build_command(self, target: str, profile: str) -> List[str]:
        """Build nuclei command based on profile"""
        nuclei_cmd = self._get_nuclei_path()

        cmd = [nuclei_cmd, '-u', target, '-json']

        if profile == 'quick':
            # Critical only - fastest
            cmd.extend(['-severity', 'critical'])
            cmd.extend(['-rate-limit', '150'])  # Faster rate
        elif profile == 'aggressive':
            # All severities for comprehensive scan
            cmd.extend(['-severity', 'critical,high,medium,low'])
            cmd.extend(['-rate-limit', '100'])
        else:  # normal
            # High and critical - balanced
            cmd.extend(['-severity', 'critical,high'])
            cmd.extend(['-rate-limit', '120'])

        # Performance and output options
        cmd.extend([
            '-duc',  # Disable update check
            '-silent',  # Suppress banner
            '-nc',  # No color in output
            '-stats'  # Show statistics
        ])

        return cmd

    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse nuclei JSON output"""
        findings = []

        try:
            # Nuclei outputs one JSON object per line
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    finding = json.loads(line)
                    findings.append({
                        'template_id': finding.get('template-id'),
                        'template_name': finding.get('info', {}).get('name'),
                        'severity': finding.get('info', {}).get('severity'),
                        'matched_at': finding.get('matched-at'),
                        'extracted_results': finding.get('extracted-results', []),
                        'matcher_name': finding.get('matcher-name'),
                        'type': finding.get('type'),
                        'cve_id': finding.get('info', {}).get('classification', {}).get('cve-id'),
                        'description': finding.get('info', {}).get('description')
                    })
                except json.JSONDecodeError:
                    continue

            # Group by severity
            severity_count = {
                'critical': len([f for f in findings if f['severity'] == 'critical']),
                'high': len([f for f in findings if f['severity'] == 'high']),
                'medium': len([f for f in findings if f['severity'] == 'medium']),
                'low': len([f for f in findings if f['severity'] == 'low'])
            }

            return {
                'findings': findings,
                'total_findings': len(findings),
                'severity_count': severity_count
            }
        except Exception as e:
            return {'error': f"Failed to parse nuclei output: {str(e)}"}
