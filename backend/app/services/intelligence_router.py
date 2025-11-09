"""
Intelligence Router - Decides when to use strategic AI reasoning.

This module analyzes incoming requests and determines whether they need
deep strategic analysis from Qwen or can be handled with simpler logic.
The goal is to use AI when it adds value, not for every little decision.

Decision Philosophy:
- Use AI for complex strategic decisions
- Use AI for prioritization with many options  
- Use AI for comprehensive reports
- Skip AI for simple yes/no questions
- Skip AI for quick tool selections
- Always have a fallback when AI unavailable
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RoutingDecision(Enum):
    """
    Router decision outcomes.
    
    USE_STRATEGIC: Send to AI for deep analysis
    USE_TACTICAL: Handle with simple logic, skip AI
    USE_FALLBACK: AI unavailable, use degraded mode
    """
    USE_STRATEGIC = "strategic"
    USE_TACTICAL = "tactical"
    USE_FALLBACK = "fallback"


@dataclass
class RoutingContext:
    """
    Context information for routing decisions.
    
    Attributes:
        subdomain_count: Number of subdomains discovered
        finding_count: Number of vulnerabilities found
        target_complexity: Low/Medium/High complexity rating
        time_budget: Available time for analysis in seconds
        user_preference: User explicitly requested AI/no-AI
        scan_phase: Which phase of scan (recon/enum/vuln/report)
    """
    subdomain_count: int = 0
    finding_count: int = 0
    target_complexity: str = "medium"
    time_budget: Optional[int] = None
    user_preference: Optional[str] = None
    scan_phase: Optional[str] = None


class IntelligenceRouter:
    """
    Routes requests to appropriate decision-making strategy.
    
    Analyzes query and context to decide whether to use:
    - Strategic reasoning (Qwen AI)
    - Tactical logic (simple rules)
    - Fallback mode (AI unavailable)
    
    Configuration via environment variables:
        QWEN_TRIGGER_SUBDOMAIN_COUNT: Threshold for strategic analysis (default: 100)
        QWEN_TRIGGER_FINDING_COUNT: Threshold for prioritization (default: 20)
    
    Example usage:
        router = IntelligenceRouter(ollama_provider)
        decision = router.route(
            query="Plan testing strategy",
            context=RoutingContext(subdomain_count=150)
        )
        if decision == RoutingDecision.USE_STRATEGIC:
            response = await router.get_strategic_response(query, context)
    """
    
    # Strategic keywords that trigger AI reasoning
    STRATEGIC_KEYWORDS = {
        "plan", "strategy", "strategize", "prioritize", "comprehensive",
        "assessment", "analyze", "analysis", "recommend", "recommendations",
        "evaluate", "evaluation", "compare", "comparison", "decide",
        "decision", "risk", "impact", "business", "executive", "report"
    }
    
    # Tactical keywords that skip AI
    TACTICAL_KEYWORDS = {
        "which", "what", "how", "syntax", "command", "parameter",
        "value", "option", "flag", "setting", "config"
    }
    
    def __init__(
        self,
        ollama_provider,
        subdomain_threshold: Optional[int] = None,
        finding_threshold: Optional[int] = None
    ):
        """
        Initialize intelligence router.
        
        Args:
            ollama_provider: OllamaProvider instance for AI queries
            subdomain_threshold: Override subdomain count threshold
            finding_threshold: Override finding count threshold
        """
        import os
        
        self.provider = ollama_provider
        self.subdomain_threshold = subdomain_threshold or int(
            os.getenv("QWEN_TRIGGER_SUBDOMAIN_COUNT", "100")
        )
        self.finding_threshold = finding_threshold or int(
            os.getenv("QWEN_TRIGGER_FINDING_COUNT", "20")
        )
        
        # Track routing statistics
        self.stats = {
            "strategic_count": 0,
            "tactical_count": 0,
            "fallback_count": 0
        }
        
        logger.info(
            f"Intelligence router initialized: "
            f"subdomain_threshold={self.subdomain_threshold}, "
            f"finding_threshold={self.finding_threshold}"
        )
    
    def route(
        self,
        query: str,
        context: Optional[RoutingContext] = None,
        force_strategic: bool = False
    ) -> RoutingDecision:
        """
        Decide routing strategy for query.
        
        Args:
            query: The user's question or request
            context: Optional context about scan state
            force_strategic: Override logic, force AI usage
            
        Returns:
            RoutingDecision indicating which strategy to use
        """
        # Force strategic if override active
        if force_strategic:
            logger.info("Routing: STRATEGIC (forced)")
            self.stats["strategic_count"] += 1
            return RoutingDecision.USE_STRATEGIC
        
        # Check user preference first
        if context and context.user_preference:
            if context.user_preference.lower() == "no-ai":
                logger.info("Routing: TACTICAL (user preference)")
                self.stats["tactical_count"] += 1
                return RoutingDecision.USE_TACTICAL
            elif context.user_preference.lower() == "use-ai":
                logger.info("Routing: STRATEGIC (user preference)")
                self.stats["strategic_count"] += 1
                return RoutingDecision.USE_STRATEGIC
        
        # Check query characteristics
        decision = self._analyze_query(query, context)
        
        # Update stats
        if decision == RoutingDecision.USE_STRATEGIC:
            self.stats["strategic_count"] += 1
        elif decision == RoutingDecision.USE_TACTICAL:
            self.stats["tactical_count"] += 1
        
        return decision
    
    def _analyze_query(
        self,
        query: str,
        context: Optional[RoutingContext]
    ) -> RoutingDecision:
        """
        Analyze query to determine routing decision.
        
        Args:
            query: User query text
            context: Optional context information
            
        Returns:
            Routing decision based on analysis
        """
        query_lower = query.lower()
        
        # Very short queries are usually tactical
        if len(query) < 50 and not any(
            keyword in query_lower for keyword in self.STRATEGIC_KEYWORDS
        ):
            logger.debug("Routing: TACTICAL (short query)")
            return RoutingDecision.USE_TACTICAL
        
        # Check for explicit strategic keywords
        strategic_score = sum(
            1 for keyword in self.STRATEGIC_KEYWORDS
            if keyword in query_lower
        )
        
        # Check for tactical keywords
        tactical_score = sum(
            1 for keyword in self.TACTICAL_KEYWORDS
            if keyword in query_lower
        )
        
        # Strong strategic signal
        if strategic_score >= 2:
            logger.info(
                f"Routing: STRATEGIC (strategic_score={strategic_score})"
            )
            return RoutingDecision.USE_STRATEGIC
        
        # Strong tactical signal
        if tactical_score >= 2 and strategic_score == 0:
            logger.debug(
                f"Routing: TACTICAL (tactical_score={tactical_score})"
            )
            return RoutingDecision.USE_TACTICAL
        
        # Check context-based thresholds
        if context:
            # High subdomain count needs strategic planning
            if context.subdomain_count >= self.subdomain_threshold:
                logger.info(
                    f"Routing: STRATEGIC (subdomains={context.subdomain_count} "
                    f">= {self.subdomain_threshold})"
                )
                return RoutingDecision.USE_STRATEGIC
            
            # Many findings need AI prioritization
            if context.finding_count >= self.finding_threshold:
                logger.info(
                    f"Routing: STRATEGIC (findings={context.finding_count} "
                    f">= {self.finding_threshold})"
                )
                return RoutingDecision.USE_STRATEGIC
            
            # Report generation always strategic
            if context.scan_phase == "report":
                logger.info("Routing: STRATEGIC (report generation)")
                return RoutingDecision.USE_STRATEGIC
            
            # High complexity targets need strategic approach
            if context.target_complexity == "high":
                logger.info("Routing: STRATEGIC (high complexity)")
                return RoutingDecision.USE_STRATEGIC
        
        # Default to tactical for simple queries
        if strategic_score == 0:
            logger.debug("Routing: TACTICAL (no strategic signals)")
            return RoutingDecision.USE_TACTICAL
        
        # Weak strategic signal - use AI
        logger.info(f"Routing: STRATEGIC (strategic_score={strategic_score})")
        return RoutingDecision.USE_STRATEGIC
    
    async def get_strategic_response(
        self,
        query: str,
        context: Optional[RoutingContext] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get strategic AI response.
        
        Args:
            query: User query
            context: Optional context
            system_prompt: Optional system instructions
            
        Returns:
            Dict with response text and metadata
        """
        # Check if provider available
        if not self.provider:
            logger.warning("No Ollama provider available, using fallback")
            self.stats["fallback_count"] += 1
            return {
                "success": False,
                "response": self._get_fallback_response(query, context),
                "mode": "fallback",
                "reason": "AI provider unavailable"
            }
        
        # Build context dict for provider
        context_dict = self._build_context_dict(context) if context else None
        
        # Get AI response
        result = await self.provider.generate(
            prompt=query,
            context=context_dict,
            system_prompt=system_prompt
        )
        
        if result.success:
            logger.info(
                f"Strategic response: {result.duration_seconds:.2f}s, "
                f"{result.tokens} tokens"
            )
            return {
                "success": True,
                "response": result.response,
                "mode": "strategic",
                "duration": result.duration_seconds,
                "tokens": result.tokens
            }
        else:
            logger.warning(f"AI request failed: {result.error}")
            self.stats["fallback_count"] += 1
            return {
                "success": False,
                "response": self._get_fallback_response(query, context),
                "mode": "fallback",
                "reason": result.error
            }
    
    def _build_context_dict(self, context: RoutingContext) -> Dict[str, Any]:
        """
        Convert RoutingContext to dict for provider.
        
        Args:
            context: Routing context
            
        Returns:
            Dict representation
        """
        return {
            "subdomain_count": context.subdomain_count,
            "finding_count": context.finding_count,
            "target_complexity": context.target_complexity,
            "time_budget": context.time_budget,
            "scan_phase": context.scan_phase
        }
    
    def _get_fallback_response(
        self,
        query: str,
        context: Optional[RoutingContext]
    ) -> str:
        """
        Generate fallback response when AI unavailable.
        
        Args:
            query: Original query
            context: Optional context
            
        Returns:
            Fallback response text
        """
        return (
            "⚠️ Strategic AI analysis currently unavailable.\n\n"
            "The system will continue with standard tactical logic. "
            "For full strategic analysis, please try again later or "
            "check Ollama service status.\n\n"
            f"Your query: {query[:100]}..."
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Dict with routing counts and percentages
        """
        total = sum(self.stats.values())
        if total == 0:
            return {**self.stats, "total": 0}
        
        return {
            **self.stats,
            "total": total,
            "strategic_percent": (self.stats["strategic_count"] / total) * 100,
            "tactical_percent": (self.stats["tactical_count"] / total) * 100,
            "fallback_percent": (self.stats["fallback_count"] / total) * 100
        }
    
    def reset_statistics(self):
        """Reset routing statistics."""
        self.stats = {
            "strategic_count": 0,
            "tactical_count": 0,
            "fallback_count": 0
        }
        logger.debug("Router statistics reset")
