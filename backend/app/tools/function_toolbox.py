"""
Function Toolbox for Gemini Function Calling
Defines tools in format yang compatible dengan Google AI Function Calling API
"""
from typing import Dict, Any, List, Callable
import google.generativeai as genai
import google.ai.generativelanguage as glm
from app.utils.logger import logger


# ============================================================================
# TOOL DEFINITIONS (Protobuf Format for Python 3.13 Compatibility)
# ============================================================================

def create_security_tools() -> List[glm.Tool]:
    """
    Create SECURITY_TOOLS in protobuf format (glm.Schema) for Python 3.13 compatibility
    
    Returns:
        List of glm.Tool objects
    """
    tool_declarations = [
        glm.FunctionDeclaration(
            name="run_subfinder",
            description="Discover subdomains of a domain using passive information gathering (Certificate Transparency logs, DNS databases). Use this FIRST when target is a domain (not IP) to identify all accessible services for comprehensive security assessment coverage.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "domain_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_DOMAIN' as the value. Use root domain only (e.g., 'example.com', NOT 'www.example.com')."
                    ),
                    "timeout_seconds": glm.Schema(
                        type=glm.Type.INTEGER,
                        description="Discovery timeout in seconds: 60 (quick), 180 (standard), 300 (deep). Default: 180"
                    )
                },
                required=["domain_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_httpx",
            description="Quick HTTP probe to check if web services are alive and reachable. Use AFTER subfinder to filter dead/unreachable hosts before heavy scanning.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "targets_placeholder": glm.Schema(
                        type=glm.Type.ARRAY,
                        items=glm.Schema(type=glm.Type.STRING),
                        description="List of hosts to probe. Use 'DISCOVERED_HOSTS' for hosts from subfinder."
                    ),
                    "timeout": glm.Schema(
                        type=glm.Type.INTEGER,
                        description="Timeout per probe in seconds. Default: 5"
                    )
                },
                required=["targets_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_nmap",
            description="Execute network discovery scan to identify open ports, services, and OS fingerprinting on the target system. Use AFTER subfinder/httpx for reconnaissance.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_HOST' as the value. Never use actual target names or IPs."
                    ),
                    "scan_profile": glm.Schema(
                        type=glm.Type.STRING,
                        description="Scan intensity: 'quick' (top 100 ports, ~30s), 'normal' (top 1000 ports, ~2min), 'aggressive' (all ports + OS detection, ~10min)"
                    )
                },
                required=["target_placeholder", "scan_profile"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_nuclei",
            description="Execute vulnerability scanner with 10,000+ templates to detect security issues, CVEs, and misconfigurations. Use AFTER nmap to scan discovered web services.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_URL' for web targets. Never use actual URLs."
                    ),
                    "severity_filter": glm.Schema(
                        type=glm.Type.STRING,
                        description="Filter findings by severity. Options: 'critical', 'high', 'medium', 'low', 'info', 'all'. Use 'critical,high' for focused scan, 'all' for comprehensive scan."
                    ),
                    "template_category": glm.Schema(
                        type=glm.Type.STRING,
                        description="Category of templates to use. Options: 'cves', 'vulnerabilities', 'exposures', 'misconfigurations', 'all'. Default: 'all'"
                    )
                },
                required=["target_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_whatweb",
            description="Identify web technologies, CMS, frameworks, server versions, and JavaScript libraries. Use when web service is detected to understand tech stack.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_URL'. Never use actual URLs."
                    ),
                    "aggression_level": glm.Schema(
                        type=glm.Type.INTEGER,
                        description="Scan aggressiveness level (1-4): 1 (stealthy), 2 (balanced), 3 (aggressive), 4 (heavy)"
                    )
                },
                required=["target_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_ffuf",
            description="Comprehensive content discovery tool to identify hidden directories, files, and endpoints on web applications. Use AFTER service identification to ensure complete security assessment coverage and discover all publicly accessible resources that may have security implications.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_URL/FUZZ' where FUZZ is the placeholder. Never use actual URLs."
                    ),
                    "wordlist_size": glm.Schema(
                        type=glm.Type.STRING,
                        description="Wordlist size options: 'quick' (4k entries, 1-2min), 'standard' (20k, 3-5min), 'deep' (100k, 15-30min). Default: 'standard'"
                    ),
                    "extensions": glm.Schema(
                        type=glm.Type.STRING,
                        description="File extensions to test (comma-separated). Example: 'php,html,txt,zip,bak'. Leave empty for directories only."
                    )
                },
                required=["target_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_sslscan",
            description="Analyze SSL/TLS configuration, certificate details, cipher suites, and protocol versions. Use when HTTPS service is detected.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_HOST' as the value. Never use actual target names or IPs."
                    )
                },
                required=["target_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="run_sqlmap",
            description="⚠️ AUTHORIZED VERIFICATION TOOL - Controlled database security testing for authorized security assessments to verify and document SQL injection vulnerabilities for remediation purposes. Use ONLY when strong indicators exist (database error messages, preliminary vulnerability scanner detection). Performs safe, read-only database structure enumeration to assess vulnerability severity for client remediation planning. Requires Pro approval for safety validation before execution.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "target_url_placeholder": glm.Schema(
                        type=glm.Type.STRING,
                        description="ALWAYS use 'TARGET_URL' as the value. Must be a complete URL with query parameters."
                    ),
                    "parameter": glm.Schema(
                        type=glm.Type.STRING,
                        description="Specific GET/POST parameter to test (e.g., 'id', 'user', 'search'). Optional - if not specified, SQLMAP will test all."
                    ),
                    "level": glm.Schema(
                        type=glm.Type.INTEGER,
                        description="Detection level (1-5): 1 (default, basic tests), 2-3 (more tests), 4-5 (extensive, very slow). Recommend: 1-2"
                    ),
                    "risk": glm.Schema(
                        type=glm.Type.INTEGER,
                        description="Risk level (1-3): 1 (safe, default), 2 (medium risk), 3 (high risk, may cause damage). Recommend: 1"
                    )
                },
                required=["target_url_placeholder"]
            )
        ),
        glm.FunctionDeclaration(
            name="complete_assessment",
            description="Call this function when the security assessment objective has been fully met and no further scanning is needed. Provide a brief summary of what was accomplished.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "summary": glm.Schema(
                        type=glm.Type.STRING,
                        description="Brief summary of assessment completed and key findings"
                    ),
                    "confidence": glm.Schema(
                        type=glm.Type.NUMBER,
                        description="Confidence level (0.0-1.0) that objective was met"
                    )
                },
                required=["summary", "confidence"]
            )
        )
    ]
    
    return [glm.Tool(function_declarations=tool_declarations)]

# Create the tools once at module level
SECURITY_TOOLS = create_security_tools()

# For debugging: Count of tools loaded
logger.info(f"[OK] Loaded {len(SECURITY_TOOLS[0].function_declarations)} security tools in protobuf format")


# ============================================================================
# TOOL EXECUTOR REGISTRY
# ============================================================================

class ToolExecutor:
    """
    Maps function names to actual Python execution logic
    """
    
    def __init__(self, real_target: str, scan_id: str, db_session, tool_results: Dict[str, Any] = None, event_callback=None):
        """
        Initialize with real target (hidden from AI)
        
        Args:
            real_target: The actual target (e.g., "unair.ac.id")
            scan_id: Scan ID for logging
            db_session: Database session for saving results
            tool_results: Dictionary of tool execution results (for DISCOVERED_HOSTS)
            event_callback: Async callback for real-time streaming events
        """
        self.real_target = real_target
        self.scan_id = scan_id
        self.db = db_session
        self.execution_log = []
        # CRITICAL: Use 'if tool_results is not None' to preserve reference to empty dict
        # Using 'or {}' creates NEW dict because empty dict is falsy!
        self.tool_results = tool_results if tool_results is not None else {}  # Store tool results for placeholder substitution
        self.event_callback = event_callback  # For real-time streaming
        
        logger.info(f"🔧 ToolExecutor initialized for scan {scan_id}")
        logger.info(f"🎯 Real target: {real_target} (hidden from AI)")
        logger.info(f"📡 Real-time streaming: {'ENABLED' if event_callback else 'DISABLED'}")
    
    def substitute_placeholder(self, placeholder_value: Any) -> Any:
        """
        Replace placeholder with real target
        
        AI sends: 'TARGET_HOST', 'TARGET_URL', 'TARGET_DOMAIN', or 'DISCOVERED_HOSTS'
        We return: Real values
        
        OPTIMIZATION: This is critical for tool chaining - must work perfectly!
        """
        # Handle array placeholders (for httpx) - CHECK THIS FIRST
        if isinstance(placeholder_value, list):
            logger.debug(f"🔍 Placeholder list: length={len(placeholder_value)}, contents={placeholder_value[:3]}...")
            
            # If array contains single 'DISCOVERED_HOSTS' string, handle specially
            if len(placeholder_value) == 1 and placeholder_value[0] == 'DISCOVERED_HOSTS':
                logger.info("🎯 DISCOVERED_HOSTS detected - retrieving subfinder results")
                
                discovered_hosts = []
                
                # Check if subfinder has run and has results
                logger.debug(f"🔍 Checking tool_results keys: {list(self.tool_results.keys())}")
                if 'subfinder' in self.tool_results:
                    subfinder_data = self.tool_results['subfinder']
                    logger.debug(f"📊 Subfinder data keys: {subfinder_data.keys() if isinstance(subfinder_data, dict) else 'not a dict'}")
                    
                    # Extract subdomains from subfinder results
                    if isinstance(subfinder_data, dict):
                        # OPTIMIZATION: Prefer DNS-validated subdomains
                        if 'valid_subdomains' in subfinder_data and subfinder_data['valid_subdomains']:
                            discovered_hosts = subfinder_data['valid_subdomains'][:500]
                            logger.info(f"✅ Using {len(discovered_hosts)} DNS-validated subdomains (optimized!)")
                        # Fallback to all subdomains if validation not yet done
                        elif 'subdomains' in subfinder_data:
                            subdomains = subfinder_data['subdomains']
                            logger.info(f"✅ Found {len(subdomains) if isinstance(subdomains, list) else 'unknown'} subdomains (unvalidated)")
                            if isinstance(subdomains, list):
                                discovered_hosts = subdomains[:500]
                        
                        # Fallback: Check for 'interesting_findings' 
                        elif 'interesting_findings' in subfinder_data:
                            findings = subfinder_data['interesting_findings']
                            if isinstance(findings, list):
                                for finding in findings:
                                    # Extract subdomain from "subdomain.com (keyword - description)" format
                                    if isinstance(finding, str) and ' (' in finding:
                                        subdomain = finding.split(' (')[0]
                                        discovered_hosts.append(subdomain)
                                    else:
                                        discovered_hosts.append(str(finding))
                
                if discovered_hosts:
                    logger.info(f"🔍 Substituted DISCOVERED_HOSTS with {len(discovered_hosts)} hosts from subfinder")
                    return discovered_hosts
                else:
                    logger.warning("⚠️ No discovered hosts available in tool_results, checking keys:")
                    logger.warning(f"   tool_results keys: {list(self.tool_results.keys())}")
                    if 'subfinder' in self.tool_results:
                        logger.warning(f"   subfinder data structure: {type(self.tool_results['subfinder'])}")
                        if isinstance(self.tool_results['subfinder'], dict):
                            logger.warning(f"   subfinder keys: {list(self.tool_results['subfinder'].keys())}")
                    logger.warning("   → Falling back to main target only")
                    return [self.real_target]  # Fallback to main target
            else:
                # Regular array processing
                return [self.substitute_placeholder(item) for item in placeholder_value]
        
        # Handle string placeholders
        elif isinstance(placeholder_value, str):
            if placeholder_value == 'TARGET_HOST':
                return self.real_target
            elif placeholder_value == 'TARGET_URL':
                # Determine if target is HTTP or HTTPS (default to http)
                if not self.real_target.startswith('http'):
                    return f'http://{self.real_target}'
                return self.real_target
            elif placeholder_value == 'TARGET_DOMAIN':
                # Extract domain from target (strip protocol if present)
                target = self.real_target.replace('http://', '').replace('https://', '').split('/')[0]
                return target
            elif placeholder_value == 'TARGET_URL/FUZZ':
                # For ffuf fuzzing
                base_url = f'http://{self.real_target}' if not self.real_target.startswith('http') else self.real_target
                return f"{base_url}/FUZZ"
            elif placeholder_value == 'DISCOVERED_HOSTS':
                # Single string DISCOVERED_HOSTS (shouldn't happen but handle it)
                logger.warning("⚠️ DISCOVERED_HOSTS received as single string, expected array")
                return self.substitute_placeholder(['DISCOVERED_HOSTS'])  # Recursively handle as array
            else:
                logger.warning(f"⚠️ Unexpected placeholder: {placeholder_value}, using as-is")
                return placeholder_value
        
        else:
            return placeholder_value
    
    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the requested function with target substitution
        
        Args:
            function_name: Name of function (e.g., 'run_nmap')
            arguments: Arguments from AI (contains placeholders)
        
        Returns:
            Dict with execution results
        """
        logger.info(f"⚡ Executing function: {function_name}")
        logger.info(f"📥 AI Arguments: {arguments}")
        
        # Substitute placeholders with real target
        if 'target_placeholder' in arguments:
            real_target_value = self.substitute_placeholder(arguments['target_placeholder'])
            logger.info(f"🔄 Substituted '{arguments['target_placeholder']}' → '{real_target_value}'")
            arguments['target'] = real_target_value
            del arguments['target_placeholder']
        
        # Handle domain_placeholder (for subfinder)
        if 'domain_placeholder' in arguments:
            real_domain_value = self.substitute_placeholder(arguments['domain_placeholder'])
            logger.info(f"🔄 Substituted '{arguments['domain_placeholder']}' → '{real_domain_value}'")
            arguments['domain'] = real_domain_value
            del arguments['domain_placeholder']
        
        # Handle targets_placeholder (for httpx)
        if 'targets_placeholder' in arguments:
            logger.debug(f"📋 BEFORE substitute: targets_placeholder value = {arguments['targets_placeholder']}")
            logger.debug(f"📋 BEFORE substitute: type = {type(arguments['targets_placeholder'])}")
            logger.debug(f"📋 tool_results keys available: {list(self.tool_results.keys())}")
            
            real_targets_value = self.substitute_placeholder(arguments['targets_placeholder'])
            
            logger.info(f"🔄 Substituted targets_placeholder → {len(real_targets_value)} hosts")
            logger.debug(f"📋 AFTER substitute: result = {real_targets_value[:5] if len(real_targets_value) > 5 else real_targets_value}")
            
            arguments['targets'] = real_targets_value
            del arguments['targets_placeholder']
        
        # Handle target_url_placeholder (for sqlmap)
        if 'target_url_placeholder' in arguments:
            real_url_value = self.substitute_placeholder(arguments['target_url_placeholder'])
            logger.info(f"🔄 Substituted '{arguments['target_url_placeholder']}' → '{real_url_value}'")
            arguments['target_url'] = real_url_value
            del arguments['target_url_placeholder']
        
        # Route to appropriate executor
        if function_name == 'run_subfinder':
            return await self._exec_subfinder(**arguments)
        elif function_name == 'run_httpx':
            return await self._exec_httpx(**arguments)
        elif function_name == 'run_nmap':
            return await self._exec_nmap(**arguments)
        elif function_name == 'run_nuclei':
            return await self._exec_nuclei(**arguments)
        elif function_name == 'run_whatweb':
            return await self._exec_whatweb(**arguments)
        elif function_name == 'run_ffuf':
            return await self._exec_ffuf(**arguments)
        elif function_name == 'run_sqlmap':
            return await self._exec_sqlmap(**arguments)
        elif function_name == 'run_sslscan':
            return await self._exec_sslscan(**arguments)
        elif function_name == 'complete_assessment':
            return await self._exec_complete(**arguments)
        else:
            logger.error(f"❌ Unknown function: {function_name}")
            return {
                "status": "error",
                "message": f"Unknown function: {function_name}"
            }
    
    async def _exec_nmap(self, target: str, scan_profile: str = "normal") -> Dict[str, Any]:
        """Execute nmap scan with real-time streaming"""
        from app.tools.factory import ToolFactory
        from app.tools.streaming_executor import StreamingToolExecutor
        import asyncio
        import time
        
        logger.info(f"🔍 Running nmap: target={target}, profile={scan_profile} (streaming enabled)")
        
        try:
            tool = ToolFactory.get_tool('nmap')
            
            # Build command
            cmd = tool.build_command(target, scan_profile)
            
            # EMIT COMMAND
            if hasattr(self, 'event_callback') and self.event_callback:
                profile_desc = {
                    'quick': 'Fast scan (top 100 ports)',
                    'normal': 'Standard scan with version detection',
                    'aggressive': 'Comprehensive scan with OS detection'
                }
                await self.event_callback({
                    "type": "command",
                    "tool": "nmap",
                    "command": " ".join(cmd),
                    "explanation": profile_desc.get(scan_profile, 'Port scanning'),
                    "estimated_time": "60-180s depending on profile"
                })
            
            # Execute with streaming
            start_time = time.time()
            streaming_executor = StreamingToolExecutor("nmap", cmd, 300)
            
            output_lines = []
            async for event in streaming_executor.execute_streaming():
                if hasattr(self, 'event_callback') and self.event_callback:
                    await self.event_callback(event)
                if event.get('type') == 'tool_output':
                    output_lines.append(event.get('content', ''))
            
            execution_time = time.time() - start_time
            stdout = '\n'.join(output_lines)
            
            # Parse output
            parsed_data = tool.parse_output(stdout)
            
            from app.tools.base import ToolResult
            result = ToolResult(
                tool_name='nmap',
                exit_code=0,
                stdout=stdout,
                stderr='',
                execution_time=execution_time,
                parsed_data=parsed_data
            )
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='nmap',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            # Note: Commit happens at end of function to batch DB operations
            
            # Return sanitized summary for AI
            summary = self._sanitize_nmap_output(result.parsed_data)
            ports_count = summary.get('open_ports_count', 0)
            
            logger.info(f"✅ Nmap completed: {ports_count} open ports found")
            
            # Batch commit
            self.db.commit()
            
            # STANDARDIZED OUTPUT FORMAT
            return {
                "status": "success",
                "tool": "nmap",
                "execution_time": execution_time,
                "findings_count": ports_count,
                "findings_summary": f"{ports_count} open ports detected" if ports_count > 0 else "No open ports found",
                "summary": summary,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
            logger.error(f"❌ Nmap execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "tool": "nmap",
                "message": str(e)
            }
    
    async def _exec_nuclei(self, target: str, severity_filter: str = "all", template_category: str = "all") -> Dict[str, Any]:
        """Execute nuclei scan with real-time streaming"""
        from app.tools.factory import ToolFactory
        from app.tools.streaming_executor import StreamingToolExecutor
        import asyncio
        import time
        
        logger.info(f"🎯 Running nuclei: target={target}, severity={severity_filter} (streaming enabled)")
        
        try:
            tool = ToolFactory.get_tool('nuclei')
            
            # Build command
            cmd = tool.build_command(target, "normal")
            
            # EMIT COMMAND
            if hasattr(self, 'event_callback') and self.event_callback:
                await self.event_callback({
                    "type": "command",
                    "tool": "nuclei",
                    "command": " ".join(cmd),
                    "explanation": f"Vulnerability scanning with {severity_filter} severity",
                    "estimated_time": "120-900s"
                })
            
            # Execute with streaming
            start_time = time.time()
            streaming_executor = StreamingToolExecutor("nuclei", cmd, 900)
            
            output_lines = []
            async for event in streaming_executor.execute_streaming():
                if hasattr(self, 'event_callback') and self.event_callback:
                    await self.event_callback(event)
                if event.get('type') == 'tool_output':
                    output_lines.append(event.get('content', ''))
            
            execution_time = time.time() - start_time
            stdout = '\n'.join(output_lines)
            
            # Parse output
            parsed_data = tool.parse_output(stdout)
            
            from app.tools.base import ToolResult
            result = ToolResult(
                tool_name='nuclei',
                exit_code=0,
                stdout=stdout,
                stderr='',
                execution_time=execution_time,
                parsed_data=parsed_data
            )
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='nuclei',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            # Batch commit at end
            
            # Return sanitized summary
            summary = self._sanitize_nuclei_output(result.parsed_data)
            findings_count = summary.get('findings_count', 0)
            
            logger.info(f"✅ Nuclei completed: {findings_count} vulnerabilities found")
            
            # Batch commit
            self.db.commit()
            
            # STANDARDIZED OUTPUT FORMAT
            return {
                "status": "success",
                "tool": "nuclei",
                "execution_time": execution_time,
                "findings_count": findings_count,
                "findings_summary": f"{findings_count} vulnerabilities detected" if findings_count > 0 else "No vulnerabilities found",
                "summary": summary,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
            logger.error(f"❌ Nuclei execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "tool": "nuclei",
                "message": str(e)
            }
    
    async def _exec_whatweb(self, target: str, aggression_level: int = 2) -> Dict[str, Any]:
        """Execute whatweb scan"""
        from app.tools.factory import ToolFactory
        import asyncio
        import time
        
        logger.info(f"🌐 Running whatweb: target={target}")
        
        try:
            start_time = time.time()
            tool = ToolFactory.get_tool('whatweb')
            result = await asyncio.to_thread(tool.execute, target, "normal")
            execution_time = time.time() - start_time
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='whatweb',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            # Batch commit at end
            
            summary = self._sanitize_whatweb_output(result.parsed_data)
            tech_count = len(summary.get('technologies', [])) if 'technologies' in summary else 0
            
            logger.info(f"✅ Whatweb completed: {tech_count} technologies detected")
            
            # Batch commit
            self.db.commit()
            
            # STANDARDIZED OUTPUT FORMAT
            return {
                "status": "success",
                "tool": "whatweb",
                "execution_time": execution_time,
                "findings_count": tech_count,
                "findings_summary": f"{tech_count} technologies identified" if tech_count > 0 else "No technologies detected",
                "summary": summary,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
            logger.error(f"❌ Whatweb execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "tool": "whatweb",
                "message": str(e)
            }
    
    async def _exec_sslscan(self, target: str = None, **kwargs) -> Dict[str, Any]:
        """Execute sslscan"""
        from app.tools.factory import ToolFactory
        import asyncio
        import time
        
        logger.info(f"🔐 Running sslscan: target={target}")
        
        try:
            start_time = time.time()
            tool = ToolFactory.get_tool('sslscan')
            result = await asyncio.to_thread(tool.execute, target, "normal")
            execution_time = time.time() - start_time
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='sslscan',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            # Batch commit at end
            
            summary = result.parsed_data or {"message": "SSL scan completed"}
            
            logger.info(f"✅ SSLScan completed")
            
            # Batch commit
            self.db.commit()
            
            return {
                "status": "success",
                "tool": "sslscan",
                "summary": summary,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
            logger.error(f"❌ SSLScan execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "tool": "sslscan",
                "message": str(e)
            }
    
    async def _exec_subfinder(self, domain: str, timeout_seconds: int = 180) -> Dict[str, Any]:
        """Execute Subfinder subdomain enumeration with real-time streaming"""
        from app.tools.subfinder_tool import SubfinderTool
        from app.tools.streaming_executor import StreamingToolExecutor
        import asyncio
        import time
        
        logger.info(f"🔍 Running Subfinder: domain={domain}, timeout={timeout_seconds}s")
        performance_monitor.start_tool("subfinder", domain)
        
        try:
            tool = SubfinderTool()
            if not tool.is_installed():
                return {"status": "error", "message": "Subfinder not installed"}
            
            # Map timeout to profile
            profile = 'quick' if timeout_seconds <= 60 else 'deep' if timeout_seconds >= 300 else 'normal'
            
            # Build command
            cmd = tool.build_command(domain, profile)
            
            # EMIT COMMAND BEFORE EXECUTION
            if hasattr(self, 'event_callback') and self.event_callback:
                await self.event_callback({
                    "type": "command",
                    "tool": "subfinder",
                    "command": " ".join(cmd),
                    "explanation": f"Discovering subdomains for {domain} using all available sources",
                    "estimated_time": f"{timeout_seconds}s max"
                })
            
            # Execute with streaming
            start_time = time.time()
            streaming_executor = StreamingToolExecutor("subfinder", cmd, timeout_seconds)
            
            output_lines = []
            async for event in streaming_executor.execute_streaming():
                # Forward streaming events to frontend
                if hasattr(self, 'event_callback') and self.event_callback:
                    await self.event_callback(event)
                
                # Collect output
                if event.get('type') == 'tool_output':
                    output_lines.append(event.get('content', ''))
            
            execution_time = time.time() - start_time
            stdout = '\n'.join(output_lines)
            
            # Parse output using tool's parser
            parsed_data = tool.parse_output(stdout)
            
            # Create ToolResult object
            from app.tools.base import ToolResult
            result = ToolResult(
                tool_name='subfinder',
                exit_code=0,
                stdout=stdout,
                stderr='',
                execution_time=execution_time,
                parsed_data=parsed_data
            )
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='subfinder',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            self.db.commit()
            
            # Return sanitized summary WITH FULL SUBDOMAIN LIST for tool chaining
            if result.parsed_data and 'total_subdomains' in result.parsed_data:
                # Extract full subdomain list from parsed_data
                # SubfinderTool returns: [{'subdomain': 'x', 'source': 'y'}, ...]
                # We need: ['x', 'y', ...]
                all_subdomains = []
                if 'subdomains' in result.parsed_data:
                    raw_subdomains = result.parsed_data['subdomains']
                    if isinstance(raw_subdomains, list):
                        for item in raw_subdomains:
                            if isinstance(item, dict):
                                # Extract 'subdomain' key from dict
                                subdomain = item.get('subdomain', '')
                                if subdomain:
                                    all_subdomains.append(subdomain)
                            elif isinstance(item, str):
                                # Already a string
                                all_subdomains.append(item)
                elif 'findings' in result.parsed_data:
                    # Extract from findings if available
                    all_subdomains = [f.get('subdomain', f) if isinstance(f, dict) else f 
                                     for f in result.parsed_data['findings']]
                
                # Limit to prevent massive data transfer but keep enough for chaining
                max_subdomains = 500  # Keep top 500 for performance
                subdomain_list = all_subdomains[:max_subdomains] if len(all_subdomains) > max_subdomains else all_subdomains
                
                logger.info(f"🔍 Extracted {len(subdomain_list)} subdomains from subfinder results for tool chaining")
                logger.debug(f"   First 5 subdomains: {subdomain_list[:5]}")
                
                summary = {
                    'status': 'success',
                    'tool': 'subfinder',
                    'execution_time': execution_time,
                    'findings_count': result.parsed_data['total_subdomains'],
                    'findings_summary': f"{result.parsed_data['total_subdomains']} subdomains discovered",
                    'total_subdomains': result.parsed_data['total_subdomains'],
                    'subdomains': subdomain_list,  # CRITICAL: Flat list of strings for DISCOVERED_HOSTS
                    'interesting_findings': result.parsed_data.get('interesting_findings', [])[:50],  # Top 50 interesting
                    'note': f'Use DISCOVERED_HOSTS placeholder to scan these {len(subdomain_list)} subdomains'
                }
                logger.info(f"✅ Subfinder completed: {len(subdomain_list)} subdomains available for tool chaining")
                
                # DNS VALIDATION PHASE
                if subdomain_list:
                    logger.info(f"🔍 Starting DNS validation for {len(subdomain_list)} subdomains...")
                    
                    # Emit validation start event
                    if hasattr(self, 'event_callback') and self.event_callback:
                        await self.event_callback({
                            "type": "validation_start",
                            "tool": "dns_validator",
                            "message": f"Validating {len(subdomain_list)} discovered subdomains...",
                            "total": len(subdomain_list)
                        })
                    
                    # Run DNS validation
                    from app.tools.dns_validator import DNSValidator
                    validator = DNSValidator(timeout=5.0)
                    validation_results = await validator.validate_bulk(subdomain_list)
                    
                    # Emit validation results
                    if hasattr(self, 'event_callback') and self.event_callback:
                        await self.event_callback({
                            "type": "validation_complete",
                            "tool": "dns_validator",
                            "results": validation_results,
                            "message": f"✅ {validation_results['valid_count']}/{validation_results['total_tested']} subdomains valid"
                        })
                    
                    # Update summary with validation data
                    summary['validation'] = validation_results
                    summary['valid_subdomains'] = [item['subdomain'] for item in validation_results['valid_subdomains']]
                    summary['invalid_subdomains'] = [item['subdomain'] for item in validation_results['invalid_subdomains']]
                    
                    # Override subdomains list with ONLY valid ones for tool chaining
                    summary['subdomains'] = summary['valid_subdomains'][:500]
                    
                    logger.info(f"🎯 Filtered to {len(summary['subdomains'])} valid subdomains for scanning")
                
            else:
                summary = {'status': 'error', 'message': 'Failed to enumerate subdomains'}
            
            logger.info(f"✅ Subfinder completed: {summary.get('total_subdomains', 0)} subdomains found")
            performance_monitor.end_tool("subfinder", domain)
            return summary
            
        except Exception as e:
            logger.error(f"❌ Subfinder execution failed: {e}")
            performance_monitor.end_tool("subfinder", domain)
            return {"status": "error", "message": str(e)}
    
    async def _exec_httpx(self, targets: List[str], timeout: int = 5) -> Dict[str, Any]:
        """Execute httpx HTTP probe with real-time streaming"""
        from app.tools.httpx_tool import HttpxTool
        from app.tools.streaming_executor import StreamingToolExecutor
        import asyncio
        import time
        
        logger.info(f"🔍 Running httpx: {len(targets)} targets, timeout={timeout}s")
        
        try:
            tool = HttpxTool()
            if not tool.is_installed():
                return {"status": "error", "message": "httpx not installed"}
            
            # Build command
            cmd = tool.build_command(targets, 'normal')
            
            # EMIT COMMAND
            if hasattr(self, 'event_callback') and self.event_callback:
                await self.event_callback({
                    "type": "command",
                    "tool": "httpx",
                    "command": " ".join(cmd),
                    "explanation": f"Probing {len(targets)} targets for HTTP/HTTPS accessibility",
                    "estimated_time": f"{timeout * len(targets)}s max"
                })
            
            # Execute with streaming
            start_time = time.time()
            streaming_executor = StreamingToolExecutor("httpx", cmd, timeout * len(targets))
            
            output_lines = []
            async for event in streaming_executor.execute_streaming():
                if hasattr(self, 'event_callback') and self.event_callback:
                    await self.event_callback(event)
                if event.get('type') == 'tool_output':
                    output_lines.append(event.get('content', ''))
            
            execution_time = time.time() - start_time
            stdout = '\n'.join(output_lines)
            
            # Parse output
            parsed_data = tool.parse_output(stdout)
            
            from app.tools.base import ToolResult
            result = ToolResult(
                tool_name='httpx',
                exit_code=0,
                stdout=stdout,
                stderr='',
                execution_time=execution_time,
                parsed_data=parsed_data
            )
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='httpx',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            self.db.commit()
            
            # Return standardized summary
            if result.parsed_data and 'alive' in result.parsed_data:
                alive_count = result.parsed_data['alive']
                total_probed = result.parsed_data['total_probed']
                
                summary = {
                    'status': 'success',
                    'tool': 'httpx',
                    'execution_time': execution_time,
                    'findings_count': alive_count,
                    'findings_summary': f"{alive_count}/{total_probed} hosts alive" if alive_count > 0 else f"0/{total_probed} hosts alive",
                    'total_probed': total_probed,
                    'alive': alive_count,
                    'dead': result.parsed_data['dead'],
                    'alive_hosts': result.parsed_data['alive_hosts']
                }
            else:
                summary = {
                    'status': 'error',
                    'tool': 'httpx',
                    'message': 'Failed to probe hosts',
                    'findings_count': 0
                }
            
            logger.info(f"✅ httpx completed: {summary.get('alive', 0)}/{summary.get('total_probed', 0)} hosts alive")
            return summary
            
        except Exception as e:
            logger.error(f"❌ httpx execution failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _exec_ffuf(self, target: str, wordlist_size: str = 'standard', extensions: str = '') -> Dict[str, Any]:
        """Execute ffuf content discovery"""
        from app.tools.ffuf_tool import FfufTool
        import asyncio
        import time
        
        logger.info(f"🔍 Running ffuf: target={target}, wordlist={wordlist_size}")
        
        try:
            tool = FfufTool()
            if not tool.is_installed():
                return {"status": "error", "message": "ffuf not installed"}
            
            # Map wordlist_size to profile
            profile_map = {'quick': 'quick', 'standard': 'normal', 'deep': 'aggressive'}
            profile = profile_map.get(wordlist_size, 'normal')
            
            start_time = time.time()
            result = await asyncio.to_thread(tool.execute, target, profile)
            execution_time = time.time() - start_time
            
            # Save to DB with execution_time
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='ffuf',
                raw_output=result.stdout or "",
                parsed_output=result.parsed_data,
                exit_code=result.exit_code or 0,
                execution_time=execution_time,
                error_message=result.stderr if result.exit_code != 0 else None
            )
            self.db.add(scan_result)
            self.db.commit()
            
            # Return sanitized summary with better error handling
            if result.parsed_data:
                total_found = result.parsed_data.get('total_found', 0)
                summary = {
                    'status': 'success' if total_found >= 0 else 'error',
                    'tool': 'ffuf',
                    'total_found': total_found,
                    'interesting_findings': result.parsed_data.get('interesting_findings', []),
                    'discovered_paths': result.parsed_data.get('discovered_paths', [])[:10],  # Top 10 only
                    'execution_time': execution_time
                }
            else:
                # Ffuf might legitimately find nothing or tool not installed
                summary = {
                    'status': 'success',
                    'tool': 'ffuf',
                    'total_found': 0,
                    'message': 'No paths discovered or tool not available',
                    'execution_time': execution_time
                }
            
            logger.info(f"✅ ffuf completed: {summary.get('total_found', 0)} paths discovered")
            return summary
            
        except Exception as e:
            logger.error(f"❌ ffuf execution failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _exec_complete(self, summary: str, confidence: float) -> Dict[str, Any]:
        """Mark assessment as complete"""
        logger.info(f"✅ Assessment completed: {summary}")
        logger.info(f"📊 Confidence: {confidence:.0%}")
        
        return {
            "status": "completed",
            "summary": summary,
            "confidence": confidence
        }
    
    # ========================================================================
    # OUTPUT SANITIZERS (Remove real target from outputs sent back to AI)
    # ========================================================================
    
    def _sanitize_nmap_output(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize nmap output - replace real target with TARGET_HOST"""
        if not parsed_data:
            return {}
        
        # Replace target mentions
        sanitized = self._replace_target(parsed_data, self.real_target, 'TARGET_HOST')
        
        # Return summary
        open_ports = sanitized.get('open_ports', [])
        return {
            "open_ports_count": len(open_ports),
            "open_ports": open_ports[:10],  # Top 10 ports
            "os_detection": sanitized.get('os_detection'),
            "host_status": sanitized.get('host_status', 'unknown')
        }
    
    def _sanitize_nuclei_output(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize nuclei output"""
        if not parsed_data:
            return {}
        
        sanitized = self._replace_target(parsed_data, self.real_target, 'TARGET_HOST')
        
        findings = sanitized.get('findings', [])
        return {
            "findings_count": len(findings),
            "findings": findings[:20],  # Top 20 findings
            "severity_breakdown": self._count_severities(findings)
        }
    
    def _sanitize_whatweb_output(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize whatweb output"""
        if not parsed_data:
            return {}
        
        sanitized = self._replace_target(parsed_data, self.real_target, 'TARGET_HOST')
        return sanitized
    
    def _replace_target(self, data: Any, real_target: str, placeholder: str) -> Any:
        """Recursively replace real target with placeholder"""
        if isinstance(data, dict):
            return {k: self._replace_target(v, real_target, placeholder) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_target(item, real_target, placeholder) for item in data]
        elif isinstance(data, str):
            return data.replace(real_target, placeholder)
        else:
            return data
    
    def _count_severities(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {}
        for finding in findings:
            sev = finding.get('severity', 'unknown')
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    async def _exec_sqlmap(
        self,
        target_url: str,
        parameter: str = None,
        level: int = 1,
        risk: int = 1,
        technique: str = 'BEUSTQ',
        database_enum_only: bool = True
    ) -> Dict[str, Any]:
        """
        Execute SQLMAP for SQL injection testing
        
        ⚠️ CRITICAL: This is an AGGRESSIVE exploitation tool!
        - Requires Pro approval before execution
        - Must have explicit authorization
        - Database enumeration only (no data exfiltration)
        - Full logging for transparency
        
        Args:
            target_url: Target URL to test for SQLi
            parameter: Specific parameter to test (optional)
            level: Detection level (1-5, higher = more tests)
            risk: Risk level (1-3, higher = more aggressive)
            technique: SQLi techniques (B=Boolean, E=Error, U=Union, S=Stacked, T=Time, Q=Query)
            database_enum_only: Only enumerate database structure (default: True)
        """
        from app.tools.sqlmap_tool import SqlmapTool
        from app.tools.streaming_executor import StreamingToolExecutor
        import time
        
        logger.info(f"🎯 Running SQLMAP verification: {target_url}")
        logger.info("⚠️ SQLMAP verification tool - authorized assessment with safety constraints")
        performance_monitor.start_tool("sqlmap", target_url)
        
        try:
            tool = SqlmapTool()
            if not tool.is_installed():
                return {"status": "error", "message": "SQLMAP not installed"}
            
            # Build command with safety constraints
            cmd = tool.build_command(
                target_url=target_url,
                parameter=parameter,
                level=level,
                risk=risk,
                technique=technique,
                threads=1,  # Conservative threading
                batch=True,  # Never ask for user input
                database_enum_only=database_enum_only  # NO DATA EXTRACTION
            )
            
            # EMIT COMMAND BEFORE EXECUTION
            if hasattr(self, 'event_callback') and self.event_callback:
                await self.event_callback({
                    "type": "command",
                    "tool": "sqlmap",
                    "command": " ".join(cmd),
                    "explanation": f"Verifying database security on {target_url} using controlled testing (safety level={level}, conservative risk={risk})",
                    "estimated_time": "10-15 minutes",
                    "warning": "⚠️ VERIFICATION TOOL - Authorized assessment with safety monitoring"
                })
            
            # Execute with streaming
            start_time = time.time()
            streaming_executor = StreamingToolExecutor("sqlmap", cmd, tool.timeout)
            
            output_lines = []
            stderr_lines = []
            async for event in streaming_executor.execute_streaming():
                # Forward streaming events to frontend
                if hasattr(self, 'event_callback') and self.event_callback:
                    await self.event_callback(event)
                
                # Collect output
                if event.get('type') == 'tool_output':
                    output_lines.append(event.get('content', ''))
                elif event.get('type') == 'tool_complete':
                    stderr_text = event.get('stderr', '')
                    if stderr_text:
                        stderr_lines.append(stderr_text)
            
            execution_time = time.time() - start_time
            stdout = "\n".join(output_lines)
            stderr = "\n".join(stderr_lines)
            
            # Parse output
            parsed_data = tool.parse_output(stdout, stderr)
            
            # Save to database
            from app.models.result import ScanResult
            scan_result = ScanResult(
                scan_id=self.scan_id,
                tool_name='sqlmap',
                raw_output=stdout,
                parsed_output=parsed_data,
                exit_code=0 if parsed_data.get('vulnerable') else 1,
                execution_time=execution_time,
                error_message=stderr if stderr else None
            )
            self.db.add(scan_result)
            self.db.commit()
            
            # Build summary
            if parsed_data.get('vulnerable'):
                summary = {
                    'status': 'success',
                    'tool': 'sqlmap',
                    'vulnerable': True,
                    'severity': 'critical',
                    'injection_types': parsed_data.get('injection_type', []),
                    'database_type': parsed_data.get('database_type'),
                    'current_database': parsed_data.get('current_database'),
                    'current_user': parsed_data.get('current_user'),
                    'is_dba': parsed_data.get('is_dba', False),
                    'exploitation_evidence': parsed_data.get('exploitation_evidence', []),
                    'execution_time': execution_time,
                    'findings_count': len(parsed_data.get('exploitation_evidence', [])),
                    'findings_summary': f"🚨 SQL INJECTION CONFIRMED - {len(parsed_data.get('injection_type', []))} types"
                }
                
                logger.warning(f"🚨 CRITICAL: SQL injection confirmed on {target_url}!")
                logger.warning(f"   Database: {parsed_data.get('database_type')}")
                logger.warning(f"   Injection types: {', '.join(parsed_data.get('injection_type', []))}")
            else:
                summary = {
                    'status': 'success',
                    'tool': 'sqlmap',
                    'vulnerable': False,
                    'execution_time': execution_time,
                    'findings_count': 0,
                    'findings_summary': "✅ No SQL injection detected"
                }
                logger.info(f"✅ SQLMAP: No SQL injection found on {target_url}")
            
            performance_monitor.end_tool("sqlmap", target_url)
            return summary
            
        except Exception as e:
            logger.error(f"❌ SQLMAP execution failed: {e}")
            performance_monitor.end_tool("sqlmap", target_url)
            return {"status": "error", "tool": "sqlmap", "message": str(e)}

