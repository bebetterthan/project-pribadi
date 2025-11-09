"""
AI Reasoning Engine - Phase 2, Day 4
Adds intelligent decision-making where AI analyzes findings and determines optimal next steps
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
import google.generativeai as genai
from app.core.scan_context_manager import ScanContextManager
from app.models.scan_context import FindingType
from app.utils.logger import logger


class ReasoningTrigger(str, Enum):
    """When AI reasoning should be triggered"""
    SCAN_INITIALIZATION = "scan_initialization"
    TOOL_COMPLETED = "tool_completed"
    CRITICAL_FINDING = "critical_finding"
    STRATEGY_ADJUSTMENT = "strategy_adjustment"
    SCAN_COMPLETION = "scan_completion"
    ERROR_RECOVERY = "error_recovery"


class AIReasoningManager:
    """
    Manages AI reasoning at strategic decision points during scans.
    Provides intelligent analysis and recommendations.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash-002"):
        """
        Initialize AI reasoning manager.
        
        Args:
            api_key: Gemini API key
            model_name: Gemini model to use for reasoning
        """
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"AIReasoningManager initialized with model: {model_name}")
    
    def get_initial_strategy(
        self,
        target: str,
        user_prompt: Optional[str] = None,
        available_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate initial scan strategy based on target analysis.
        
        Args:
            target: Target domain/IP
            user_prompt: User's objective/instructions
            available_tools: List of available tools
            
        Returns:
            Dictionary with:
            - analysis: AI's analysis of target
            - recommended_tools: List of tools to use
            - execution_order: Suggested order
            - reasoning: Why this strategy
            - priority_targets: What to focus on
        """
        try:
            # Detect target type
            target_type = self._detect_target_type(target)
            
            # Build prompt
            prompt = self._build_initial_strategy_prompt(
                target, target_type, user_prompt, available_tools
            )
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse response
            strategy = self._parse_strategy_response(response.text)
            
            logger.info(f"Generated initial strategy for {target}: {len(strategy.get('recommended_tools', []))} tools")
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to generate initial strategy: {e}", exc_info=True)
            # Fallback strategy
            return {
                'analysis': f"Error generating strategy: {str(e)}",
                'recommended_tools': available_tools or ['subfinder', 'nmap', 'httpx'],
                'execution_order': [['subfinder', 'nmap'], ['httpx'], ['nuclei']],
                'reasoning': 'Using default fallback strategy due to AI error',
                'priority_targets': []
            }
    
    def analyze_tool_results(
        self,
        tool_name: str,
        tool_results: Dict[str, Any],
        scan_context_manager: ScanContextManager,
        scan_id: str
    ) -> Dict[str, Any]:
        """
        Analyze results from a completed tool and suggest next actions.
        
        Args:
            tool_name: Name of completed tool
            tool_results: Results from the tool
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            
        Returns:
            Dictionary with:
            - interpretation: AI's interpretation of findings
            - significance: How significant these findings are
            - next_actions: Recommended next steps
            - reasoning: Why these actions
            - warnings: Any concerns or warnings
        """
        try:
            # Get scan statistics
            stats = scan_context_manager.get_scan_statistics(scan_id)
            
            # Build prompt
            prompt = self._build_tool_analysis_prompt(
                tool_name, tool_results, stats
            )
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse response
            analysis = self._parse_analysis_response(response.text)
            
            logger.info(f"Analyzed {tool_name} results: {analysis.get('significance', 'unknown')} significance")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze tool results: {e}", exc_info=True)
            return {
                'interpretation': f"Tool {tool_name} completed",
                'significance': 'unknown',
                'next_actions': ['continue with next tool'],
                'reasoning': f'Analysis error: {str(e)}',
                'warnings': []
            }
    
    def suggest_next_tool(
        self,
        completed_tools: List[str],
        available_tools: List[str],
        scan_context_manager: ScanContextManager,
        scan_id: str
    ) -> Dict[str, Any]:
        """
        Suggest which tool to execute next based on current findings.
        
        Args:
            completed_tools: Tools already executed
            available_tools: Tools available to run
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            
        Returns:
            Dictionary with:
            - next_tool: Tool name to execute next (or None)
            - reasoning: Why this tool
            - parameters_hint: Suggested parameters
            - skip_tools: Tools to skip with reasons
            - complete: Whether scan is complete
        """
        try:
            # Get current scan state
            stats = scan_context_manager.get_scan_statistics(scan_id)
            
            # Build prompt
            prompt = self._build_next_tool_prompt(
                completed_tools, available_tools, stats
            )
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse response
            suggestion = self._parse_next_tool_response(response.text)
            
            logger.info(f"Next tool suggestion: {suggestion.get('next_tool', 'none')}")
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to suggest next tool: {e}", exc_info=True)
            # Simple fallback: return first available tool
            remaining = [t for t in available_tools if t not in completed_tools]
            return {
                'next_tool': remaining[0] if remaining else None,
                'reasoning': f'Fallback selection due to error: {str(e)}',
                'parameters_hint': {},
                'skip_tools': [],
                'complete': len(remaining) == 0
            }
    
    def respond_to_critical_finding(
        self,
        finding: Dict[str, Any],
        scan_context_manager: ScanContextManager,
        scan_id: str
    ) -> Dict[str, Any]:
        """
        Provide immediate guidance on critical finding.
        
        Args:
            finding: Critical finding details
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            
        Returns:
            Dictionary with:
            - impact_assessment: Severity and potential impact
            - exploitation_guidance: How to verify/exploit
            - remediation: How to fix
            - related_findings: Other relevant findings
            - priority: How urgent this is
        """
        try:
            # Build prompt
            prompt = self._build_critical_finding_prompt(finding)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse response
            guidance = self._parse_critical_response(response.text)
            
            logger.warning(f"Critical finding response: {guidance.get('priority', 'unknown')} priority")
            return guidance
            
        except Exception as e:
            logger.error(f"Failed to respond to critical finding: {e}", exc_info=True)
            return {
                'impact_assessment': 'Critical vulnerability detected',
                'exploitation_guidance': 'Manual verification recommended',
                'remediation': 'Apply security patch immediately',
                'related_findings': [],
                'priority': 'high'
            }
    
    def generate_final_assessment(
        self,
        scan_context_manager: ScanContextManager,
        scan_id: str,
        target: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive final assessment of scan.
        
        Args:
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            target: Target that was scanned
            
        Returns:
            Dictionary with:
            - executive_summary: High-level overview
            - key_findings: Most important discoveries
            - risk_assessment: Overall risk level
            - recommendations: Prioritized actions
            - attack_surface: Summary of exposure
        """
        try:
            # Get comprehensive statistics
            stats = scan_context_manager.get_scan_statistics(scan_id)
            
            # Get critical vulnerabilities
            critical_vulns = scan_context_manager.get_vulnerabilities(scan_id, 'critical')
            high_vulns = scan_context_manager.get_vulnerabilities(scan_id, 'high')
            
            # Build prompt
            prompt = self._build_final_assessment_prompt(
                target, stats, critical_vulns, high_vulns
            )
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse response
            assessment = self._parse_assessment_response(response.text)
            
            logger.info(f"Generated final assessment for {target}")
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate final assessment: {e}", exc_info=True)
            return {
                'executive_summary': f'Scan completed for {target}',
                'key_findings': [],
                'risk_assessment': 'Unable to assess',
                'recommendations': ['Review scan results manually'],
                'attack_surface': 'Analysis incomplete'
            }
    
    # =========================================================================
    # PROMPT BUILDERS - Craft detailed prompts for each reasoning scenario
    # =========================================================================
    
    def _build_initial_strategy_prompt(
        self,
        target: str,
        target_type: str,
        user_prompt: Optional[str],
        available_tools: List[str]
    ) -> str:
        """Build prompt for initial strategy generation"""
        tools_list = ', '.join(available_tools) if available_tools else 'subfinder, httpx, nmap, nuclei, whatweb, ffuf'
        
        prompt = f"""You are a senior penetration tester planning a security assessment.

TARGET ANALYSIS:
Target: {target}
Type: {target_type}
User Objective: {user_prompt or 'Comprehensive security reconnaissance'}

AVAILABLE TOOLS:
{tools_list}

TOOL CAPABILITIES:
- subfinder: Discover subdomains via passive reconnaissance
- httpx: Probe HTTP services, detect active URLs
- nmap: Port scanning and service detection
- nuclei: Vulnerability scanning with templates
- whatweb: Technology fingerprinting
- ffuf: Directory/file fuzzing
- wafw00f: WAF detection

YOUR TASK:
Analyze the target and create an optimal scan strategy.

OUTPUT FORMAT (JSON):
{{
  "analysis": "Your detailed analysis of the target type, expected security posture, and scan approach",
  "recommended_tools": ["tool1", "tool2", "tool3"],
  "execution_order": [["parallel_tool1", "parallel_tool2"], ["dependent_tool"]],
  "reasoning": "Why this strategy is optimal for this target",
  "priority_targets": ["What specific aspects to focus on"]
}}

RULES:
1. Consider target type (corporate, educational, government, etc.)
2. Recommend 4-7 tools maximum
3. Group tools that can run in parallel
4. Explain your reasoning clearly
5. Output ONLY valid JSON, no additional text
"""
        return prompt
    
    def _build_tool_analysis_prompt(
        self,
        tool_name: str,
        tool_results: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> str:
        """Build prompt for tool result analysis"""
        
        # Extract key metrics from results
        findings_summary = self._summarize_findings(tool_results)
        
        prompt = f"""You are a penetration testing expert analyzing scan results.

TOOL: {tool_name}
FINDINGS SUMMARY:
{findings_summary}

SCAN STATISTICS:
- Total subdomains: {stats.get('total_subdomains', 0)}
- Active URLs: {stats.get('total_active_urls', 0)}
- Open ports: {stats.get('total_open_ports', 0)}
- Vulnerabilities: {stats.get('total_vulnerabilities', 0)}
- Critical: {stats.get('critical_vulnerabilities', 0)}
- High: {stats.get('high_vulnerabilities', 0)}

YOUR TASK:
Analyze these results and provide strategic guidance.

OUTPUT FORMAT (JSON):
{{
  "interpretation": "What these findings mean in security context",
  "significance": "low|medium|high|critical",
  "next_actions": ["Specific next steps based on findings"],
  "reasoning": "Why these actions are recommended",
  "warnings": ["Any concerns or red flags"]
}}

RULES:
1. Be specific and actionable
2. Consider pentesting workflow
3. Highlight interesting patterns
4. Output ONLY valid JSON
"""
        return prompt
    
    def _build_next_tool_prompt(
        self,
        completed_tools: List[str],
        available_tools: List[str],
        stats: Dict[str, Any]
    ) -> str:
        """Build prompt for next tool suggestion"""
        
        remaining_tools = [t for t in available_tools if t not in completed_tools]
        
        prompt = f"""You are coordinating a penetration test workflow.

COMPLETED TOOLS:
{', '.join(completed_tools)}

REMAINING TOOLS:
{', '.join(remaining_tools)}

CURRENT FINDINGS:
- Subdomains: {stats.get('total_subdomains', 0)}
- Active URLs: {stats.get('total_active_urls', 0)}
- Open ports: {stats.get('total_open_ports', 0)}
- Vulnerabilities: {stats.get('total_vulnerabilities', 0)}

YOUR TASK:
Decide the next tool to execute or if scan is complete.

OUTPUT FORMAT (JSON):
{{
  "next_tool": "tool_name or null",
  "reasoning": "Why this tool or why complete",
  "parameters_hint": {{"key": "value"}},
  "skip_tools": [{{"tool": "name", "reason": "why skip"}}],
  "complete": false
}}

RULES:
1. Consider data dependencies (e.g., nuclei needs URLs from httpx)
2. If insufficient data for remaining tools, mark complete=true
3. Skip tools that won't be productive
4. Output ONLY valid JSON
"""
        return prompt
    
    def _build_critical_finding_prompt(self, finding: Dict[str, Any]) -> str:
        """Build prompt for critical finding response"""
        
        prompt = f"""CRITICAL FINDING DETECTED!

FINDING DETAILS:
{json.dumps(finding, indent=2)}

YOUR TASK (URGENT):
Provide immediate guidance on this critical security issue.

OUTPUT FORMAT (JSON):
{{
  "impact_assessment": "Detailed analysis of severity and potential damage",
  "exploitation_guidance": "How to verify this vulnerability is exploitable",
  "remediation": "Immediate steps to fix this issue",
  "related_findings": ["Other findings that might be connected"],
  "priority": "critical|high|medium"
}}

RULES:
1. Be urgent but clear
2. Provide actionable guidance
3. Consider business impact
4. Output ONLY valid JSON
"""
        return prompt
    
    def _build_final_assessment_prompt(
        self,
        target: str,
        stats: Dict[str, Any],
        critical_vulns: List[Dict[str, Any]],
        high_vulns: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for final assessment"""
        
        prompt = f"""SCAN COMPLETION - FINAL ASSESSMENT

TARGET: {target}

SCAN RESULTS:
- Total subdomains discovered: {stats.get('total_subdomains', 0)}
- Active HTTP services: {stats.get('total_active_urls', 0)}
- Open ports found: {stats.get('total_open_ports', 0)}
- Total vulnerabilities: {stats.get('total_vulnerabilities', 0)}
- Critical vulnerabilities: {len(critical_vulns)}
- High vulnerabilities: {len(high_vulns)}

CRITICAL VULNERABILITIES:
{json.dumps(critical_vulns[:3], indent=2) if critical_vulns else "None"}

YOUR TASK:
Provide a comprehensive executive assessment.

OUTPUT FORMAT (JSON):
{{
  "executive_summary": "3-4 sentence overview for management",
  "key_findings": ["Most important discoveries"],
  "risk_assessment": "overall|high|medium|low with justification",
  "recommendations": [
    {{"action": "what to do", "priority": "immediate|urgent|soon", "effort": "low|medium|high"}}
  ],
  "attack_surface": "Summary of target's exposure"
}}

RULES:
1. Executive summary should be non-technical
2. Prioritize recommendations by risk
3. Be actionable and specific
4. Output ONLY valid JSON
"""
        return prompt
    
    # =========================================================================
    # RESPONSE PARSERS - Extract structured data from AI responses
    # =========================================================================
    
    def _parse_strategy_response(self, response_text: str) -> Dict[str, Any]:
        """Parse initial strategy response"""
        try:
            # Try to extract JSON from response
            json_str = self._extract_json(response_text)
            strategy = json.loads(json_str)
            
            # Validate required fields
            if 'recommended_tools' not in strategy:
                raise ValueError("Missing recommended_tools")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to parse strategy response: {e}")
            logger.debug(f"Raw response: {response_text}")
            raise
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse tool analysis response"""
        try:
            json_str = self._extract_json(response_text)
            analysis = json.loads(json_str)
            return analysis
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            raise
    
    def _parse_next_tool_response(self, response_text: str) -> Dict[str, Any]:
        """Parse next tool suggestion response"""
        try:
            json_str = self._extract_json(response_text)
            suggestion = json.loads(json_str)
            return suggestion
        except Exception as e:
            logger.error(f"Failed to parse next tool response: {e}")
            raise
    
    def _parse_critical_response(self, response_text: str) -> Dict[str, Any]:
        """Parse critical finding response"""
        try:
            json_str = self._extract_json(response_text)
            guidance = json.loads(json_str)
            return guidance
        except Exception as e:
            logger.error(f"Failed to parse critical response: {e}")
            raise
    
    def _parse_assessment_response(self, response_text: str) -> Dict[str, Any]:
        """Parse final assessment response"""
        try:
            json_str = self._extract_json(response_text)
            assessment = json.loads(json_str)
            return assessment
        except Exception as e:
            logger.error(f"Failed to parse assessment response: {e}")
            raise
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _detect_target_type(self, target: str) -> str:
        """Detect type of target (educational, corporate, government, etc.)"""
        target_lower = target.lower()
        
        if any(edu in target_lower for edu in ['.edu', '.ac.', 'univ', 'college', 'school']):
            return "educational institution"
        elif any(gov in target_lower for gov in ['.gov', '.mil', 'government']):
            return "government/military"
        elif any(tech in target_lower for tech in ['tech', 'software', 'dev', 'cloud']):
            return "technology company"
        elif 'bank' in target_lower or 'financial' in target_lower:
            return "financial institution"
        else:
            return "corporate/business"
    
    def _summarize_findings(self, tool_results: Dict[str, Any]) -> str:
        """Create human-readable summary of findings"""
        summary_lines = []
        
        if 'total_subdomains' in tool_results:
            summary_lines.append(f"- Subdomains: {tool_results['total_subdomains']}")
        
        if 'alive' in tool_results:
            summary_lines.append(f"- Active hosts: {tool_results['alive']}")
        
        if 'open_ports' in tool_results:
            if isinstance(tool_results['open_ports'], list):
                summary_lines.append(f"- Open ports: {len(tool_results['open_ports'])}")
        
        if 'findings' in tool_results:
            if isinstance(tool_results['findings'], list):
                summary_lines.append(f"- Findings: {len(tool_results['findings'])}")
        
        if 'status' in tool_results:
            summary_lines.append(f"- Status: {tool_results['status']}")
        
        return '\n'.join(summary_lines) if summary_lines else "No specific metrics available"
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain markdown or other formatting"""
        # Remove markdown code blocks
        text = text.strip()
        
        # Try to find JSON between ```json and ``` or ``` and ```
        if '```' in text:
            parts = text.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{') and part.endswith('}'):
                    return part
        
        # Try to find JSON directly
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            return text[start:end+1]
        
        raise ValueError("No JSON found in response")

