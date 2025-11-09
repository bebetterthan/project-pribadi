"""
Unit tests for Intelligence Router.

Tests cover:
- Routing decisions based on keywords
- Threshold-based decisions with different contexts
- Fallback behavior when provider unavailable
- Override functionality
- Logging of routing decisions
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from backend.app.services.intelligence_router import (
    IntelligenceRouter,
    RoutingDecision,
    RoutingContext
)
from backend.app.services.ollama_provider import OllamaResponse


@pytest.fixture
def mock_provider():
    """Create mock Ollama provider."""
    provider = Mock()
    provider.generate = AsyncMock()
    return provider


@pytest.fixture
def router(mock_provider):
    """Create router instance with mock provider."""
    return IntelligenceRouter(
        ollama_provider=mock_provider,
        subdomain_threshold=100,
        finding_threshold=20
    )


class TestIntelligenceRouter:
    """Test suite for IntelligenceRouter class."""
    
    def test_strategic_keywords_trigger_ai(self, router):
        """Test that strategic keywords route to AI."""
        strategic_queries = [
            "Plan comprehensive testing strategy",
            "Prioritize vulnerabilities by risk",
            "Analyze attack surface",
            "Provide strategic recommendations",
            "Evaluate business impact"
        ]
        
        for query in strategic_queries:
            decision = router.route(query)
            assert decision == RoutingDecision.USE_STRATEGIC, \
                f"Query should be strategic: {query}"
    
    def test_tactical_keywords_skip_ai(self, router):
        """Test that tactical keywords skip AI."""
        tactical_queries = [
            "What is the syntax for nmap?",
            "Which port should I scan?",
            "How do I set the timeout?",
            "What parameter for verbose mode?"
        ]
        
        for query in tactical_queries:
            decision = router.route(query)
            assert decision == RoutingDecision.USE_TACTICAL, \
                f"Query should be tactical: {query}"
    
    def test_short_queries_are_tactical(self, router):
        """Test that short queries default to tactical."""
        decision = router.route("Help")
        assert decision == RoutingDecision.USE_TACTICAL
        
        decision = router.route("Yes")
        assert decision == RoutingDecision.USE_TACTICAL
        
        decision = router.route("What port?")
        assert decision == RoutingDecision.USE_TACTICAL
    
    def test_subdomain_threshold_triggers_strategic(self, router):
        """Test subdomain count threshold triggers strategic."""
        context = RoutingContext(subdomain_count=150)
        
        decision = router.route("Scan target", context=context)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_below_subdomain_threshold_is_tactical(self, router):
        """Test below threshold stays tactical."""
        context = RoutingContext(subdomain_count=50)
        
        decision = router.route("Scan target", context=context)
        
        assert decision == RoutingDecision.USE_TACTICAL
    
    def test_finding_threshold_triggers_strategic(self, router):
        """Test finding count threshold triggers strategic."""
        context = RoutingContext(finding_count=25)
        
        decision = router.route("Process results", context=context)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_below_finding_threshold_is_tactical(self, router):
        """Test below threshold stays tactical."""
        context = RoutingContext(finding_count=10)
        
        decision = router.route("Process results", context=context)
        
        assert decision == RoutingDecision.USE_TACTICAL
    
    def test_report_phase_always_strategic(self, router):
        """Test report generation always uses strategic."""
        context = RoutingContext(scan_phase="report")
        
        decision = router.route("Generate report", context=context)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_high_complexity_triggers_strategic(self, router):
        """Test high complexity targets trigger strategic."""
        context = RoutingContext(target_complexity="high")
        
        decision = router.route("Test target", context=context)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_force_strategic_override(self, router):
        """Test force_strategic bypasses all logic."""
        # Even simple tactical query
        decision = router.route("What port?", force_strategic=True)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_user_preference_no_ai(self, router):
        """Test user can disable AI."""
        context = RoutingContext(
            subdomain_count=200,  # Would normally trigger AI
            user_preference="no-ai"
        )
        
        decision = router.route("Plan strategy", context=context)
        
        assert decision == RoutingDecision.USE_TACTICAL
    
    def test_user_preference_use_ai(self, router):
        """Test user can force AI usage."""
        context = RoutingContext(
            subdomain_count=10,  # Would normally be tactical
            user_preference="use-ai"
        )
        
        decision = router.route("Simple query", context=context)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    @pytest.mark.asyncio
    async def test_strategic_response_success(self, router, mock_provider):
        """Test successful strategic response."""
        mock_provider.generate.return_value = OllamaResponse(
            success=True,
            response="Strategic analysis result",
            duration_seconds=2.5,
            tokens=100
        )
        
        result = await router.get_strategic_response("Analyze this")
        
        assert result["success"] is True
        assert result["mode"] == "strategic"
        assert "Strategic analysis" in result["response"]
        assert result["duration"] == 2.5
        assert result["tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_strategic_response_provider_failure(self, router, mock_provider):
        """Test fallback when provider fails."""
        mock_provider.generate.return_value = OllamaResponse(
            success=False,
            response="",
            duration_seconds=1.0,
            error="Connection timeout"
        )
        
        result = await router.get_strategic_response("Analyze this")
        
        assert result["success"] is False
        assert result["mode"] == "fallback"
        assert "unavailable" in result["response"].lower()
        assert result["reason"] == "Connection timeout"
    
    @pytest.mark.asyncio
    async def test_strategic_response_no_provider(self, router):
        """Test fallback when no provider available."""
        router.provider = None
        
        result = await router.get_strategic_response("Analyze this")
        
        assert result["success"] is False
        assert result["mode"] == "fallback"
        assert "unavailable" in result["response"].lower()
    
    @pytest.mark.asyncio
    async def test_strategic_response_with_context(self, router, mock_provider):
        """Test strategic response includes context."""
        mock_provider.generate.return_value = OllamaResponse(
            success=True,
            response="Analysis with context",
            duration_seconds=1.5,
            tokens=80
        )
        
        context = RoutingContext(
            subdomain_count=150,
            finding_count=25,
            target_complexity="high"
        )
        
        result = await router.get_strategic_response(
            "Analyze", 
            context=context
        )
        
        # Verify context was passed
        call_args = mock_provider.generate.call_args
        assert call_args[1]["context"] is not None
        assert call_args[1]["context"]["subdomain_count"] == 150
        assert call_args[1]["context"]["finding_count"] == 25
    
    def test_statistics_tracking(self, router):
        """Test routing statistics are tracked."""
        # Make various routing decisions
        router.route("Plan strategy")  # Strategic
        router.route("What port?")  # Tactical
        router.route("What syntax?")  # Tactical
        router.route("Prioritize findings")  # Strategic
        
        stats = router.get_statistics()
        
        assert stats["strategic_count"] == 2
        assert stats["tactical_count"] == 2
        assert stats["total"] == 4
        assert stats["strategic_percent"] == 50.0
        assert stats["tactical_percent"] == 50.0
    
    def test_reset_statistics(self, router):
        """Test statistics can be reset."""
        router.route("Plan strategy")
        router.route("What port?")
        
        router.reset_statistics()
        
        stats = router.get_statistics()
        assert stats["strategic_count"] == 0
        assert stats["tactical_count"] == 0
        assert stats["total"] == 0
    
    def test_multiple_strategic_keywords(self, router):
        """Test multiple strategic keywords increase confidence."""
        query = "Plan comprehensive strategy and prioritize by risk"
        
        decision = router.route(query)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_mixed_keywords_strategic_wins(self, router):
        """Test strategic keywords override tactical."""
        query = "What is the best strategy to prioritize these findings?"
        
        decision = router.route(query)
        
        assert decision == RoutingDecision.USE_STRATEGIC
    
    def test_context_dict_building(self, router):
        """Test context conversion to dict."""
        context = RoutingContext(
            subdomain_count=100,
            finding_count=20,
            target_complexity="medium",
            scan_phase="enum"
        )
        
        context_dict = router._build_context_dict(context)
        
        assert context_dict["subdomain_count"] == 100
        assert context_dict["finding_count"] == 20
        assert context_dict["target_complexity"] == "medium"
        assert context_dict["scan_phase"] == "enum"
    
    def test_fallback_response_format(self, router):
        """Test fallback response is helpful."""
        context = RoutingContext(subdomain_count=50)
        
        fallback = router._get_fallback_response(
            "Analyze vulnerabilities",
            context
        )
        
        assert "unavailable" in fallback.lower()
        assert "try again" in fallback.lower()
        assert "Analyze vulnerabilities" in fallback
    
    def test_configuration_from_env(self):
        """Test threshold configuration from environment."""
        with patch.dict('os.environ', {
            'QWEN_TRIGGER_SUBDOMAIN_COUNT': '200',
            'QWEN_TRIGGER_FINDING_COUNT': '50'
        }):
            router = IntelligenceRouter(Mock())
            
            assert router.subdomain_threshold == 200
            assert router.finding_threshold == 50
    
    def test_configuration_defaults(self):
        """Test default threshold values."""
        with patch.dict('os.environ', {}, clear=True):
            router = IntelligenceRouter(Mock())
            
            assert router.subdomain_threshold == 100
            assert router.finding_threshold == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
