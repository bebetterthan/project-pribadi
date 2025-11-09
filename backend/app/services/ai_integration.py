"""
AI Integration Helpers - Clean integration points for Agent-P workflows.

This module provides helper functions that connect Agent-P scanning workflows
to the AI intelligence router. Each function represents a specific integration
point where AI can add value.

Integration Philosophy:
- Optional: Agent-P works without AI, better with it
- No tight coupling: Can remove AI without breaking Agent-P
- Clear fallback: Continue with default logic if AI unavailable
- Logged decisions: Track when and how AI used
"""

import logging
from typing import Dict, Any, Optional, List
from backend.app.services.ollama_provider import OllamaProvider
from backend.app.services.intelligence_router import (
    IntelligenceRouter,
    RoutingContext,
    RoutingDecision
)

logger = logging.getLogger(__name__)


class AIIntegrationHelper:
    """
    Helper class for AI integration in Agent-P workflows.
    
    Provides clean, optional AI integration at key decision points:
    1. Scan planning - Strategic test planning for complex targets
    2. Vulnerability prioritization - Risk-based finding triage
    3. Report generation - Executive summaries with business context
    
    All integrations are optional and fail gracefully.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        ollama_url: Optional[str] = None,
        ollama_model: Optional[str] = None
    ):
        """
        Initialize AI integration helper.
        
        Args:
            enabled: Whether AI integration is enabled
            ollama_url: Override Ollama URL
            ollama_model: Override model name
        """
        self.enabled = enabled
        self.provider = None
        self.router = None
        
        if enabled:
            try:
                self.provider = OllamaProvider(
                    url=ollama_url,
                    model=ollama_model
                )
                self.router = IntelligenceRouter(self.provider)
                logger.info("AI integration enabled")
            except Exception as e:
                logger.warning(f"AI integration disabled due to error: {e}")
                self.enabled = False
    
    async def get_scan_strategy(
        self,
        target: str,
        reconnaissance_data: Dict[str, Any],
        time_budget: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Integration Point 1: Get strategic scan plan.
        
        Called after initial reconnaissance to plan comprehensive testing
        strategy based on target complexity and discovered attack surface.
        
        Args:
            target: Target identifier (domain/IP)
            reconnaissance_data: Initial intelligence gathered
            time_budget: Available time for testing in seconds
            
        Returns:
            Dict with strategic plan or None if AI unavailable
            
        Example:
            recon_data = {
                "subdomain_count": 150,
                "technology_stack": ["nginx", "php", "mysql"],
                "open_ports": [80, 443, 8080],
                "complexity": "high"
            }
            plan = await helper.get_scan_strategy("example.com", recon_data)
            if plan:
                # Use AI-recommended phases and priorities
                execute_phases(plan["phases"])
        """
        if not self.enabled or not self.router:
            logger.debug("AI scan planning skipped (disabled)")
            return None
        
        try:
            # Build routing context
            context = RoutingContext(
                subdomain_count=reconnaissance_data.get("subdomain_count", 0),
                target_complexity=reconnaissance_data.get("complexity", "medium"),
                time_budget=time_budget,
                scan_phase="planning"
            )
            
            # Check if strategic planning warranted
            decision = self.router.route(
                "Plan comprehensive testing strategy for this target",
                context=context
            )
            
            if decision != RoutingDecision.USE_STRATEGIC:
                logger.info("Scan complexity below strategic threshold")
                return None
            
            # Build detailed prompt
            prompt = self._build_scan_planning_prompt(
                target, 
                reconnaissance_data,
                time_budget
            )
            
            # Get strategic response
            response = await self.router.get_strategic_response(
                query=prompt,
                context=context,
                system_prompt=(
                    "You are a penetration testing expert. Provide strategic "
                    "scan planning with clear phases, time allocation, and "
                    "prioritization. Be concise and actionable."
                )
            )
            
            if response["success"]:
                logger.info(
                    f"Strategic scan plan generated: "
                    f"{response.get('duration', 0):.2f}s"
                )
                return {
                    "strategy": response["response"],
                    "ai_duration": response.get("duration"),
                    "ai_tokens": response.get("tokens"),
                    "mode": response["mode"]
                }
            else:
                logger.warning(f"AI planning failed: {response.get('reason')}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI scan planning: {e}", exc_info=True)
            return None
    
    async def prioritize_findings(
        self,
        findings: List[Dict[str, Any]],
        target_context: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Integration Point 2: Prioritize vulnerabilities by business risk.
        
        Called after vulnerability scanning to intelligently prioritize findings
        based on severity, exploitability, and business context.
        
        Args:
            findings: List of vulnerabilities discovered
            target_context: Optional context about target (industry, criticality)
            
        Returns:
            Prioritized findings list or None if AI unavailable
            
        Example:
            findings = [
                {"vuln": "SQL Injection", "severity": "critical", "location": "login"},
                {"vuln": "XSS", "severity": "medium", "location": "search"},
                ...
            ]
            prioritized = await helper.prioritize_findings(
                findings,
                {"industry": "banking", "data_sensitivity": "high"}
            )
        """
        if not self.enabled or not self.router:
            logger.debug("AI prioritization skipped (disabled)")
            return None
        
        if not findings:
            return findings
        
        try:
            # Build routing context
            context = RoutingContext(
                finding_count=len(findings),
                target_complexity=target_context.get("complexity", "medium") if target_context else "medium",
                scan_phase="prioritization"
            )
            
            # Check if prioritization warranted
            decision = self.router.route(
                "Prioritize vulnerabilities by business risk",
                context=context
            )
            
            if decision != RoutingDecision.USE_STRATEGIC:
                logger.info(
                    f"Finding count ({len(findings)}) below prioritization threshold"
                )
                return None
            
            # Build prompt
            prompt = self._build_prioritization_prompt(findings, target_context)
            
            # Get strategic response
            response = await self.router.get_strategic_response(
                query=prompt,
                context=context,
                system_prompt=(
                    "You are a security analyst. Prioritize vulnerabilities by "
                    "business risk considering severity, exploitability, and "
                    "business impact. Provide clear prioritized list with rationale."
                )
            )
            
            if response["success"]:
                logger.info(
                    f"Findings prioritized by AI: {len(findings)} vulnerabilities, "
                    f"{response.get('duration', 0):.2f}s"
                )
                
                # Return original findings with AI analysis attached
                return [{
                    **finding,
                    "_ai_prioritization": response["response"]
                } for finding in findings]
            else:
                logger.warning(f"AI prioritization failed: {response.get('reason')}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI prioritization: {e}", exc_info=True)
            return None
    
    async def generate_executive_summary(
        self,
        scan_results: Dict[str, Any],
        target_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Integration Point 3: Generate executive summary for report.
        
        Called during report generation to create business-focused summary
        with risk analysis and recommendations for non-technical stakeholders.
        
        Args:
            scan_results: Complete scan results and findings
            target_info: Information about target and context
            
        Returns:
            Executive summary text or None if AI unavailable
            
        Example:
            results = {
                "total_findings": 15,
                "critical": 3,
                "high": 5,
                "medium": 7,
                "key_findings": [...]
            }
            summary = await helper.generate_executive_summary(results, target_info)
        """
        if not self.enabled or not self.router:
            logger.debug("AI report generation skipped (disabled)")
            return None
        
        try:
            # Build routing context
            context = RoutingContext(
                finding_count=scan_results.get("total_findings", 0),
                scan_phase="report"
            )
            
            # Report generation always strategic if AI enabled
            decision = self.router.route(
                "Generate executive summary of security assessment",
                context=context
            )
            
            if decision != RoutingDecision.USE_STRATEGIC:
                logger.info("Report generation using standard template")
                return None
            
            # Build prompt
            prompt = self._build_report_prompt(scan_results, target_info)
            
            # Get strategic response
            response = await self.router.get_strategic_response(
                query=prompt,
                context=context,
                system_prompt=(
                    "You are a CISO writing an executive summary. Focus on "
                    "business risk, potential impact, and clear recommendations. "
                    "Avoid technical jargon. Be concise and actionable."
                )
            )
            
            if response["success"]:
                logger.info(
                    f"Executive summary generated: "
                    f"{response.get('duration', 0):.2f}s"
                )
                return response["response"]
            else:
                logger.warning(f"AI report generation failed: {response.get('reason')}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI report generation: {e}", exc_info=True)
            return None
    
    def _build_scan_planning_prompt(
        self,
        target: str,
        recon_data: Dict[str, Any],
        time_budget: Optional[int]
    ) -> str:
        """Build prompt for scan planning."""
        prompt_parts = [
            f"Target: {target}",
            "",
            "Reconnaissance Results:",
            f"- Subdomains discovered: {recon_data.get('subdomain_count', 0)}",
            f"- Technology stack: {', '.join(recon_data.get('technology_stack', []))}",
            f"- Open ports: {recon_data.get('open_ports', [])}",
            f"- Target complexity: {recon_data.get('complexity', 'unknown')}",
            ""
        ]
        
        if time_budget:
            prompt_parts.append(f"Time budget: {time_budget} seconds")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Task: Plan comprehensive penetration testing strategy.",
            "",
            "Provide:",
            "1. Testing phases with priorities",
            "2. Recommended tools for each phase",
            "3. Time allocation suggestions",
            "4. Key areas to focus based on attack surface",
            "",
            "Be concise and actionable."
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_prioritization_prompt(
        self,
        findings: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for vulnerability prioritization."""
        prompt_parts = [
            f"Vulnerabilities Found: {len(findings)}",
            ""
        ]
        
        if context:
            prompt_parts.extend([
                "Target Context:",
                f"- Industry: {context.get('industry', 'unknown')}",
                f"- Data sensitivity: {context.get('data_sensitivity', 'unknown')}",
                f"- Criticality: {context.get('criticality', 'unknown')}",
                ""
            ])
        
        prompt_parts.append("Findings:")
        for idx, finding in enumerate(findings[:20], 1):  # Limit to 20 for prompt size
            prompt_parts.append(
                f"{idx}. {finding.get('title', 'Unknown')} "
                f"[{finding.get('severity', 'unknown')}] "
                f"- {finding.get('location', 'N/A')}"
            )
        
        if len(findings) > 20:
            prompt_parts.append(f"... and {len(findings) - 20} more")
        
        prompt_parts.extend([
            "",
            "Task: Prioritize by business risk considering:",
            "1. Severity and exploitability",
            "2. Business impact",
            "3. Data exposure risk",
            "4. Attack complexity",
            "",
            "Provide prioritized list with brief rationale for top priorities."
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_report_prompt(
        self,
        results: Dict[str, Any],
        target_info: Dict[str, Any]
    ) -> str:
        """Build prompt for executive summary."""
        prompt_parts = [
            f"Security Assessment: {target_info.get('name', 'Target')}",
            "",
            "Assessment Results:",
            f"- Total findings: {results.get('total_findings', 0)}",
            f"- Critical: {results.get('critical', 0)}",
            f"- High: {results.get('high', 0)}",
            f"- Medium: {results.get('medium', 0)}",
            f"- Low: {results.get('low', 0)}",
            "",
            "Key Findings:"
        ]
        
        for finding in results.get("key_findings", [])[:5]:
            prompt_parts.append(f"- {finding.get('title')}: {finding.get('description', 'N/A')[:100]}")
        
        prompt_parts.extend([
            "",
            "Task: Write executive summary for C-level stakeholders.",
            "",
            "Include:",
            "1. Overall security posture (2-3 sentences)",
            "2. Top 3 business risks",
            "3. Immediate action items",
            "4. Long-term recommendations",
            "",
            "Avoid technical jargon. Focus on business impact."
        ])
        
        return "\n".join(prompt_parts)
    
    async def close(self):
        """Clean up resources."""
        if self.provider:
            await self.provider.close()


# Global singleton instance (initialized on first use)
_ai_helper: Optional[AIIntegrationHelper] = None


def get_ai_helper(
    force_new: bool = False,
    enabled: bool = True
) -> AIIntegrationHelper:
    """
    Get or create AI integration helper singleton.
    
    Args:
        force_new: Force creation of new instance
        enabled: Whether AI should be enabled
        
    Returns:
        AIIntegrationHelper instance
    """
    global _ai_helper
    
    if force_new or _ai_helper is None:
        _ai_helper = AIIntegrationHelper(enabled=enabled)
    
    return _ai_helper
