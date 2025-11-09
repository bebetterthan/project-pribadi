"""
Flash Tactical Engine - Fast, Efficient Tactical Decision-Making

Uses Gemini Flash 2.5 for rapid tactical decisions during scanning:
- Tool selection and sequencing
- Pattern recognition and prioritization  
- Progress management
- Escalation detection

Optimized for speed (< 2 seconds per decision) and cost efficiency.
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from loguru import logger
import json
import re


class FlashTacticalEngine:
    """
    Flash Tactical Engine - Fast tactical decisions for security assessments.
    
    Uses Gemini Flash for:
    - Quick tool selection (< 2 seconds)
    - Pattern recognition (< 1 second)
    - Progress updates (< 0.5 seconds)
    - Escalation detection (< 1 second)
    """
    
    def __init__(self, api_key: str):
        """Initialize Flash tactical engine"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Use actual Flash 2.5 model for maximum speed
        # gemini-2.5-flash = Latest Flash 2.5 model
        self.model_name = 'gemini-2.5-flash'
        
        logger.info(f"⚡ FlashTacticalEngine initialized with FLASH 2.5 MODEL: {self.model_name}")
    
    async def select_next_tool(
        self,
        scan_phase: str,
        completed_tools: List[str],
        findings_summary: Dict[str, Any],
        target_type: str = "domain"
    ) -> Dict[str, Any]:
        """
        Select next tool to execute based on current scan state.
        
        Args:
            scan_phase: Current phase (reconnaissance, vulnerability_scan, exploitation)
            completed_tools: List of tools already executed
            findings_summary: Summary of findings so far
            target_type: Type of target (domain, ip, url)
        
        Returns:
            {
                'tool': 'tool_name',
                'reason': 'why this tool',
                'priority': 'high|medium|low',
                'estimated_time': '2-3 minutes'
            }
        """
        try:
            # Build prompt
            prompt = f"""You are a tactical security assessment assistant selecting the next tool to execute.

**CURRENT STATE**:
- Phase: {scan_phase}
- Completed: {', '.join(completed_tools) if completed_tools else 'none'}
- Target type: {target_type}

**FINDINGS SO FAR**:
{json.dumps(findings_summary, indent=2)}

**AVAILABLE TOOLS** (in typical execution order):
1. run_subfinder - Subdomain enumeration (if not done yet)
2. run_httpx - HTTP service validation (needs subdomains)
3. run_nmap - Port scanning & service detection (needs active hosts)
4. run_nuclei - Vulnerability scanning (needs services identified)
5. run_whatweb - Technology fingerprinting (needs web services)
6. run_wafw00f - WAF detection (needs web services)
7. run_ffuf - Content discovery (needs web services, optional)
8. run_sqlmap - SQL injection testing (needs strong indicators, escalate to Pro)

**STANDARD WORKFLOW**:
- Reconnaissance: subfinder → httpx → nmap → nuclei → whatweb/wafw00f
- Deep Assessment: ffuf (if interesting targets), sqlmap (only with Pro approval)

Select the NEXT logical tool to run. Consider:
- What data is already available
- What dependencies are satisfied
- What would provide most value now

Respond in JSON format:
{{
    "tool": "tool_name",
    "reason": "brief explanation",
    "priority": "high|medium|low",
    "estimated_time": "time estimate"
}}"""

            # Fast configuration for tool selection
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': 0.5,  # Balanced
                    'max_output_tokens': 512,  # Concise
                    'top_p': 0.9
                }
            )
            
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                logger.info(f"⚡ Flash selected: {result.get('tool')} - {result.get('reason')}")
                return result
            else:
                # Fallback to text parsing
                logger.warning("⚡ Flash response not in JSON, parsing text")
                return self._parse_tool_selection_text(text)
                
        except Exception as e:
            logger.error(f"⚡ Flash tool selection failed: {e}")
            # Fallback to safe default
            return {
                'tool': 'complete_assessment',
                'reason': 'Error in tool selection, completing scan',
                'priority': 'high',
                'estimated_time': 'immediate'
            }
    
    async def analyze_tool_output(
        self,
        tool_name: str,
        raw_output: str,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Quick analysis of tool output for categorization and prioritization.
        
        Args:
            tool_name: Name of tool executed
            raw_output: Raw output from tool
            execution_time: How long tool took
        
        Returns:
            {
                'status': 'success|partial|failed',
                'findings_count': int,
                'priority_items': [list of interesting findings],
                'issues_detected': [list of problems if any],
                'escalation_recommended': bool
            }
        """
        try:
            # Truncate output for speed (Flash doesn't need full output)
            truncated = raw_output[:2000] if len(raw_output) > 2000 else raw_output
            
            prompt = f"""Quick analysis of security tool output for tactical decision-making.

**TOOL**: {tool_name}
**EXECUTION TIME**: {execution_time:.1f}s

**OUTPUT** (truncated):
{truncated}

Provide quick assessment:
1. Success status (success/partial/failed)
2. Count of findings (estimate if unclear)
3. Any high-priority/interesting items
4. Any issues or errors
5. Should this escalate to Pro for deep analysis?

Respond in JSON:
{{
    "status": "success|partial|failed",
    "findings_count": number,
    "priority_items": ["item1", "item2"],
    "issues_detected": ["issue1"],
    "escalation_recommended": true|false,
    "escalation_reason": "reason if true"
}}"""

            # Very fast configuration for analysis
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': 0.3,  # Consistent
                    'max_output_tokens': 256,  # Short
                    'top_p': 0.8
                }
            )
            
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                logger.info(f"⚡ Flash analyzed {tool_name}: {result.get('status')} - {result.get('findings_count')} findings")
                return result
            else:
                # Fallback
                return self._parse_analysis_text(text, tool_name)
                
        except Exception as e:
            logger.error(f"⚡ Flash output analysis failed: {e}")
            return {
                'status': 'unknown',
                'findings_count': 0,
                'priority_items': [],
                'issues_detected': [str(e)],
                'escalation_recommended': False
            }
    
    async def should_escalate_to_pro(
        self,
        situation: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if current situation requires Pro-level analysis.
        
        Args:
            situation: Description of current situation
            context: Additional context data
        
        Returns:
            {
                'escalate': bool,
                'reason': 'why escalate or not',
                'severity': 'low|medium|high|critical',
                'urgency': 'low|medium|high'
            }
        """
        try:
            prompt = f"""Determine if this situation requires deep strategic analysis (Pro model) or can be handled tactically (Flash model).

**SITUATION**: {situation}

**CONTEXT**:
{json.dumps(context, indent=2)}

**ESCALATION TRIGGERS** (when to use Pro):
- Critical security findings (SQL injection, RCE, authentication bypass)
- Unusual patterns or anomalies (abnormally high findings count)
- Complex decisions (aggressive tool approval like SQLMAP)
- Phase transitions (moving to exploitation phase)
- User requested deep analysis

**FLASH CAN HANDLE** (no escalation):
- Routine tool execution
- Standard reconnaissance
- Normal finding counts
- Clear next steps
- Progress updates

Should this escalate to Pro? Respond in JSON:
{{
    "escalate": true|false,
    "reason": "brief explanation",
    "severity": "low|medium|high|critical",
    "urgency": "low|medium|high"
}}"""

            # Very fast configuration
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': 0.3,  # Consistent
                    'max_output_tokens': 256,  # Short
                    'top_p': 0.8
                }
            )
            
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                if result.get('escalate'):
                    logger.warning(f"⚡ Flash recommends ESCALATION: {result.get('reason')}")
                else:
                    logger.info(f"⚡ Flash handling tactically: {result.get('reason')}")
                
                return result
            else:
                # Fallback - be conservative
                return {
                    'escalate': True,
                    'reason': 'Unable to parse decision, escalating for safety',
                    'severity': 'medium',
                    'urgency': 'medium'
                }
                
        except Exception as e:
            logger.error(f"⚡ Flash escalation check failed: {e}")
            # On error, escalate to Pro for safety
            return {
                'escalate': True,
                'reason': f'Error in Flash decision: {str(e)}',
                'severity': 'high',
                'urgency': 'high'
            }
    
    async def generate_progress_update(
        self,
        current_activity: str,
        progress_percentage: int,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate user-friendly progress update message.
        
        Args:
            current_activity: What's happening now
            progress_percentage: 0-100
            context: Additional context
        
        Returns:
            User-friendly status message string
        """
        try:
            prompt = f"""Generate a brief, user-friendly progress update message.

**ACTIVITY**: {current_activity}
**PROGRESS**: {progress_percentage}%
**CONTEXT**: {json.dumps(context, indent=2)}

Create a single-line status message that:
- Is clear and informative
- Shows what's happening now
- Indicates progress if relevant
- Is professional but friendly

Example: "🔍 Scanning 47 subdomains with Nuclei (23% complete)..."

Your message (single line):"""

            # Ultra-fast configuration
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': 0.1,  # Very consistent
                    'max_output_tokens': 128,  # Very short
                    'top_p': 0.7
                }
            )
            
            response = await model.generate_content_async(prompt)
            message = response.text.strip()
            
            # Remove quotes if present
            message = message.strip('"\'')
            
            logger.debug(f"⚡ Flash generated progress: {message}")
            return message
            
        except Exception as e:
            logger.error(f"⚡ Flash progress generation failed: {e}")
            # Fallback to simple template
            return f"⚡ {current_activity} ({progress_percentage}% complete)"
    
    # ============= HELPER METHODS =============
    
    def _parse_tool_selection_text(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON tool selection response"""
        # Look for tool names
        tools = ['subfinder', 'httpx', 'nmap', 'nuclei', 'whatweb', 'wafw00f', 'ffuf', 'sqlmap']
        for tool in tools:
            if tool in text.lower():
                return {
                    'tool': f'run_{tool}',
                    'reason': 'Parsed from text response',
                    'priority': 'medium',
                    'estimated_time': 'unknown'
                }
        
        # Default to completion
        return {
            'tool': 'complete_assessment',
            'reason': 'No clear next tool identified',
            'priority': 'low',
            'estimated_time': 'immediate'
        }
    
    def _parse_analysis_text(self, text: str, tool_name: str) -> Dict[str, Any]:
        """Parse non-JSON analysis response"""
        # Simple keyword detection
        success = any(word in text.lower() for word in ['success', 'completed', 'found', 'discovered'])
        failed = any(word in text.lower() for word in ['failed', 'error', 'timeout'])
        
        # Try to find numbers
        numbers = re.findall(r'\d+', text)
        findings_count = int(numbers[0]) if numbers else 0
        
        return {
            'status': 'failed' if failed else ('success' if success else 'partial'),
            'findings_count': findings_count,
            'priority_items': [],
            'issues_detected': ['Failed to parse JSON'] if not success else [],
            'escalation_recommended': False
        }

