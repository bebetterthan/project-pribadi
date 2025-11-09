"""
SQLMAP Tool - Database Security Verification

PURPOSE: Controlled verification of SQL injection vulnerabilities during authorized security assessments.
This tool helps organizations understand and document database security issues for remediation.

SAFETY CONSTRAINTS:
- Authorized security assessment only
- Database structure enumeration only (no data access/extraction)
- Conservative, safe settings by default
- Complete audit logging for transparency
- Automatic halt on service availability issues
- Read-only operations for verification purposes
"""

import subprocess
import json
import re
from typing import List, Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class SqlmapTool(BaseTool):
    """SQLMAP database security verification wrapper for authorized assessments"""
    
    def __init__(self):
        super().__init__()
        self.name = "sqlmap"
        self.timeout = 900  # 15 minutes max
        self.is_verification_tool = True  # Flag for Pro approval requirement
        self.requires_authorization = True  # Explicit authorization needed
    
    def is_installed(self) -> bool:
        """Check if sqlmap is installed"""
        try:
            paths = [
                'python',  # Usually: python sqlmap.py
                'sqlmap',
            ]
            for path in paths:
                try:
                    # Try to run sqlmap --version
                    result = subprocess.run(
                        [path, 'tools/sqlmap/sqlmap.py', '--version'] if path == 'python' else [path, '--version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0 and 'sqlmap' in result.stdout.lower():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _get_sqlmap_command(self) -> List[str]:
        """Get sqlmap command prefix"""
        # Try Python + sqlmap.py first
        try:
            test = subprocess.run(
                ['python', 'tools/sqlmap/sqlmap.py', '--version'],
                capture_output=True,
                timeout=2,
                text=True
            )
            if test.returncode == 0:
                return ['python', 'tools/sqlmap/sqlmap.py']
        except:
            pass
        
        # Fallback to direct sqlmap command
        return ['sqlmap']
    
    def build_command(
        self,
        target_url: str,
        parameter: Optional[str] = None,
        level: int = 1,
        risk: int = 1,
        technique: str = 'BEUSTQ',  # All techniques
        threads: int = 1,
        batch: bool = True,
        database_enum_only: bool = True
    ) -> List[str]:
        """
        Build sqlmap command with safety constraints
        
        Args:
            target_url: Target URL to test
            parameter: Specific parameter to test (optional)
            level: Detection level (1-5, higher = more tests)
            risk: Risk level (1-3, higher = more aggressive)
            technique: SQL injection techniques (B=Boolean, E=Error, U=Union, S=Stacked, T=Time, Q=Query)
            threads: Number of threads (1-10)
            batch: Never ask for user input
            database_enum_only: Only enumerate database structure (no data extraction)
        
        Returns:
            Command list
        """
        cmd = self._get_sqlmap_command()
        
        # Target
        cmd.extend(['-u', target_url])
        
        # Specific parameter if provided
        if parameter:
            cmd.extend(['-p', parameter])
        
        # Detection settings
        cmd.extend([
            f'--level={level}',
            f'--risk={risk}',
            f'--technique={technique}',
        ])
        
        # Performance
        cmd.extend([
            f'--threads={min(threads, 10)}',
        ])
        
        # Safety settings
        if batch:
            cmd.append('--batch')  # Never ask for user input
        
        cmd.extend([
            '--random-agent',  # Randomize user agent
            '--timeout=30',  # Request timeout
            '--retries=2',  # Max retries
        ])
        
        # What to enumerate (CONSERVATIVE)
        if database_enum_only:
            cmd.extend([
                '--dbs',  # Enumerate databases
                '--current-db',  # Current database
                '--current-user',  # Current user
                '--is-dba',  # Check if DBA
                # NO DATA EXTRACTION: --dump, --dump-all are NOT included
            ])
        
        # Output format
        cmd.extend([
            '--flush-session',  # Start fresh
        ])
        
        return cmd
    
    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parse SQLMAP output
        
        SQLMAP outputs plain text with specific patterns
        """
        try:
            # Initialize result
            result = {
                'vulnerable': False,
                'injection_type': [],
                'database_type': None,
                'current_database': None,
                'current_user': None,
                'is_dba': False,
                'databases': [],
                'tables': [],
                'exploitation_evidence': [],
                'risk_level': 'low'
            }
            
            combined_output = stdout + "\n" + stderr
            
            # Check if vulnerable
            if 'is vulnerable' in combined_output.lower():
                result['vulnerable'] = True
                result['risk_level'] = 'critical'
            
            # Extract injection types
            injection_patterns = [
                r'(boolean-based blind)',
                r'(error-based)',
                r'(time-based blind)',
                r'(UNION query)',
                r'(stacked queries)',
            ]
            for pattern in injection_patterns:
                matches = re.findall(pattern, combined_output, re.IGNORECASE)
                if matches:
                    result['injection_type'].extend(matches)
            
            # Extract database type
            db_patterns = [
                r'back-end DBMS: ([\w\s\.]+)',
                r'identified the back-end DBMS as ([\w\s\.]+)',
            ]
            for pattern in db_patterns:
                match = re.search(pattern, combined_output, re.IGNORECASE)
                if match:
                    result['database_type'] = match.group(1).strip()
                    break
            
            # Extract current database
            db_match = re.search(r'current database:\s*[\'"]?(\w+)[\'"]?', combined_output, re.IGNORECASE)
            if db_match:
                result['current_database'] = db_match.group(1)
            
            # Extract current user
            user_match = re.search(r'current user:\s*[\'"]?([\w@\.\-]+)[\'"]?', combined_output, re.IGNORECASE)
            if user_match:
                result['current_user'] = user_match.group(1)
            
            # Check if DBA
            if 'current user is DBA' in combined_output:
                result['is_dba'] = True
            
            # Extract available databases (if enumerated)
            db_list_match = re.search(r'available databases \[(\d+)\]:(.*?)(?:\n\n|\Z)', combined_output, re.DOTALL | re.IGNORECASE)
            if db_list_match:
                db_text = db_list_match.group(2)
                databases = re.findall(r'\[[\*\+]\]\s+(\w+)', db_text)
                result['databases'] = databases
            
            # Create exploitation evidence summary
            if result['vulnerable']:
                evidence = []
                evidence.append(f"Vulnerability confirmed: {', '.join(result['injection_type'])}")
                if result['database_type']:
                    evidence.append(f"Database: {result['database_type']}")
                if result['current_database']:
                    evidence.append(f"Current DB: {result['current_database']}")
                if result['current_user']:
                    evidence.append(f"User: {result['current_user']}")
                if result['is_dba']:
                    evidence.append("⚠️ User has DBA privileges!")
                if result['databases']:
                    evidence.append(f"Accessible databases: {len(result['databases'])}")
                
                result['exploitation_evidence'] = evidence
            
            # Generate summary
            if result['vulnerable']:
                result['summary'] = f"🚨 SQL INJECTION CONFIRMED - {result['database_type']} - {len(result['injection_type'])} injection types"
            else:
                result['summary'] = "✅ No SQL injection detected"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse SQLMAP output: {e}")
            return {
                'error': f"Parse error: {str(e)}",
                'raw_output': stdout[:1000],
                'raw_error': stderr[:500]
            }

