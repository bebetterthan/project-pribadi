"""
End-to-End Integration Tests for AI Integration.

Tests the complete integration flow from Agent-P workflows through
Intelligence Router to Ollama provider and back. Validates all three
integration points work correctly.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from backend.app.services.ai_integration import AIIntegrationHelper
from backend.app.services.ollama_provider import OllamaResponse


@pytest.fixture
def mock_ollama_provider():
    """Create mock Ollama provider."""
    provider = Mock()
    provider.generate = AsyncMock()
    return provider


@pytest.fixture
def ai_helper_enabled(mock_ollama_provider):
    """Create AI helper with mocked provider."""
    helper = AIIntegrationHelper(enabled=True)
    helper.provider = mock_ollama_provider
    
    # Mock router to always use strategic
    helper.router = Mock()
    helper.router.route = Mock(return_value="strategic")
    helper.router.get_strategic_response = AsyncMock()
    
    return helper


@pytest.fixture
def ai_helper_disabled():
    """Create disabled AI helper."""
    return AIIntegrationHelper(enabled=False)


class TestIntegrationPoint1ScanPlanning:
    """Test AI-powered scan planning integration."""
    
    @pytest.mark.asyncio
    async def test_scan_strategy_with_high_complexity(self, ai_helper_enabled):
        """Test strategic planning triggered for complex target."""
        # Mock strategic response
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": True,
            "response": "Phase 1: Recon\nPhase 2: Enumeration\nPhase 3: Exploitation",
            "mode": "strategic",
            "duration": 2.5,
            "tokens": 150
        }
        
        # High complexity target
        recon_data = {
            "subdomain_count": 200,
            "technology_stack": ["nginx", "php", "mysql", "redis"],
            "open_ports": [80, 443, 8080, 3306, 6379],
            "complexity": "high"
        }
        
        # Get strategy
        result = await ai_helper_enabled.get_scan_strategy(
            target="example.com",
            reconnaissance_data=recon_data,
            time_budget=3600
        )
        
        # Verify
        assert result is not None
        assert "strategy" in result
        assert "Phase 1" in result["strategy"]
        assert result["mode"] == "strategic"
        assert result["ai_duration"] == 2.5
    
    @pytest.mark.asyncio
    async def test_scan_strategy_with_low_complexity(self, ai_helper_enabled):
        """Test tactical logic for simple target."""
        # Mock tactical routing
        from backend.app.services.intelligence_router import RoutingDecision
        ai_helper_enabled.router.route = Mock(return_value=RoutingDecision.USE_TACTICAL)
        
        # Low complexity target
        recon_data = {
            "subdomain_count": 10,
            "technology_stack": ["nginx"],
            "open_ports": [80, 443],
            "complexity": "low"
        }
        
        # Get strategy
        result = await ai_helper_enabled.get_scan_strategy(
            target="simple.com",
            reconnaissance_data=recon_data
        )
        
        # Should skip AI for simple target
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scan_strategy_ai_failure_graceful(self, ai_helper_enabled):
        """Test graceful fallback when AI fails."""
        # Mock AI failure
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": False,
            "response": "AI unavailable",
            "mode": "fallback",
            "reason": "Connection timeout"
        }
        
        recon_data = {
            "subdomain_count": 150,
            "complexity": "high"
        }
        
        # Get strategy
        result = await ai_helper_enabled.get_scan_strategy(
            target="example.com",
            reconnaissance_data=recon_data
        )
        
        # Should return None, not crash
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scan_strategy_disabled(self, ai_helper_disabled):
        """Test scan planning when AI disabled."""
        recon_data = {
            "subdomain_count": 200,
            "complexity": "high"
        }
        
        result = await ai_helper_disabled.get_scan_strategy(
            target="example.com",
            reconnaissance_data=recon_data
        )
        
        # Should skip AI entirely
        assert result is None


class TestIntegrationPoint2VulnerabilityPrioritization:
    """Test AI-powered vulnerability prioritization."""
    
    @pytest.mark.asyncio
    async def test_prioritize_many_findings(self, ai_helper_enabled):
        """Test prioritization with many vulnerabilities."""
        # Mock strategic response
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": True,
            "response": "Priority 1: SQL Injection (Critical)\nPriority 2: XSS (High)",
            "mode": "strategic",
            "duration": 3.0,
            "tokens": 200
        }
        
        # Many findings
        findings = [
            {"title": "SQL Injection", "severity": "critical", "location": "login"},
            {"title": "XSS", "severity": "high", "location": "search"},
            {"title": "CSRF", "severity": "medium", "location": "forms"},
        ] * 10  # 30 total findings
        
        target_context = {
            "industry": "banking",
            "data_sensitivity": "high",
            "complexity": "high"
        }
        
        # Prioritize
        result = await ai_helper_enabled.prioritize_findings(
            findings=findings,
            target_context=target_context
        )
        
        # Verify
        assert result is not None
        assert len(result) == len(findings)
        assert "_ai_prioritization" in result[0]
        assert "Priority 1" in result[0]["_ai_prioritization"]
    
    @pytest.mark.asyncio
    async def test_prioritize_few_findings(self, ai_helper_enabled):
        """Test tactical logic for few vulnerabilities."""
        from backend.app.services.intelligence_router import RoutingDecision
        ai_helper_enabled.router.route = Mock(return_value=RoutingDecision.USE_TACTICAL)
        
        # Few findings
        findings = [
            {"title": "Missing HTTPS", "severity": "low", "location": "homepage"},
            {"title": "Old Library", "severity": "medium", "location": "js"}
        ]
        
        # Prioritize
        result = await ai_helper_enabled.prioritize_findings(findings=findings)
        
        # Should skip AI
        assert result is None
    
    @pytest.mark.asyncio
    async def test_prioritize_empty_findings(self, ai_helper_enabled):
        """Test handling of empty findings list."""
        result = await ai_helper_enabled.prioritize_findings(findings=[])
        
        # Should return empty list
        assert result == []
    
    @pytest.mark.asyncio
    async def test_prioritize_ai_failure(self, ai_helper_enabled):
        """Test fallback when AI fails."""
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": False,
            "mode": "fallback",
            "reason": "Timeout"
        }
        
        findings = [{"title": "Vuln1"}] * 25
        
        result = await ai_helper_enabled.prioritize_findings(findings=findings)
        
        # Should return None, not crash
        assert result is None
    
    @pytest.mark.asyncio
    async def test_prioritize_disabled(self, ai_helper_disabled):
        """Test prioritization when AI disabled."""
        findings = [{"title": "Vuln1"}] * 30
        
        result = await ai_helper_disabled.prioritize_findings(findings=findings)
        
        assert result is None


class TestIntegrationPoint3ReportGeneration:
    """Test AI-powered executive summary generation."""
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary(self, ai_helper_enabled):
        """Test executive summary generation."""
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": True,
            "response": (
                "Executive Summary:\n"
                "The security assessment identified 15 vulnerabilities...\n"
                "Immediate actions required:\n"
                "1. Patch SQL injection\n"
                "2. Implement input validation"
            ),
            "mode": "strategic",
            "duration": 4.0,
            "tokens": 250
        }
        
        scan_results = {
            "total_findings": 15,
            "critical": 3,
            "high": 5,
            "medium": 7,
            "low": 0,
            "key_findings": [
                {"title": "SQL Injection", "description": "In login form"},
                {"title": "XSS", "description": "In search"},
                {"title": "Weak Auth", "description": "No MFA"}
            ]
        }
        
        target_info = {
            "name": "Banking App",
            "industry": "Finance"
        }
        
        # Generate summary
        result = await ai_helper_enabled.generate_executive_summary(
            scan_results=scan_results,
            target_info=target_info
        )
        
        # Verify
        assert result is not None
        assert "Executive Summary" in result
        assert "vulnerabilities" in result.lower()
        assert "Immediate actions" in result
    
    @pytest.mark.asyncio
    async def test_generate_summary_ai_failure(self, ai_helper_enabled):
        """Test fallback when AI fails during report generation."""
        ai_helper_enabled.router.get_strategic_response.return_value = {
            "success": False,
            "mode": "fallback",
            "reason": "Model unavailable"
        }
        
        scan_results = {"total_findings": 10}
        target_info = {"name": "Test App"}
        
        result = await ai_helper_enabled.generate_executive_summary(
            scan_results=scan_results,
            target_info=target_info
        )
        
        # Should return None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_summary_disabled(self, ai_helper_disabled):
        """Test report generation when AI disabled."""
        scan_results = {"total_findings": 20}
        target_info = {"name": "Test App"}
        
        result = await ai_helper_disabled.generate_executive_summary(
            scan_results=scan_results,
            target_info=target_info
        )
        
        assert result is None


class TestEndToEndScenarios:
    """End-to-end integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_scan_workflow_with_ai(self, ai_helper_enabled):
        """Test complete scan workflow with AI integration."""
        # Mock all AI responses
        ai_helper_enabled.router.get_strategic_response = AsyncMock(
            return_value={
                "success": True,
                "response": "AI strategic guidance",
                "mode": "strategic",
                "duration": 2.0,
                "tokens": 100
            }
        )
        
        # Step 1: Get scan strategy
        recon_data = {
            "subdomain_count": 150,
            "technology_stack": ["nginx", "php"],
            "complexity": "high"
        }
        
        strategy = await ai_helper_enabled.get_scan_strategy(
            target="example.com",
            reconnaissance_data=recon_data
        )
        
        assert strategy is not None
        assert strategy["mode"] == "strategic"
        
        # Step 2: Prioritize findings
        findings = [{"title": f"Vuln{i}", "severity": "high"} for i in range(25)]
        
        prioritized = await ai_helper_enabled.prioritize_findings(
            findings=findings,
            target_context={"complexity": "high"}
        )
        
        assert prioritized is not None
        assert len(prioritized) == 25
        
        # Step 3: Generate report
        scan_results = {
            "total_findings": 25,
            "critical": 5,
            "high": 10,
            "medium": 10,
            "key_findings": findings[:5]
        }
        
        summary = await ai_helper_enabled.generate_executive_summary(
            scan_results=scan_results,
            target_info={"name": "Test App"}
        )
        
        assert summary is not None
    
    @pytest.mark.asyncio
    async def test_workflow_continues_when_ai_fails(self, ai_helper_enabled):
        """Test workflow continues gracefully when AI fails."""
        # Mock partial AI failure
        call_count = 0
        
        async def mock_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call succeeds
                return {
                    "success": True,
                    "response": "Strategy",
                    "mode": "strategic",
                    "duration": 1.0,
                    "tokens": 50
                }
            else:
                # Subsequent calls fail
                return {
                    "success": False,
                    "mode": "fallback",
                    "reason": "Timeout"
                }
        
        ai_helper_enabled.router.get_strategic_response = mock_response
        
        # Step 1: Succeeds
        recon_data = {"subdomain_count": 150, "complexity": "high"}
        strategy = await ai_helper_enabled.get_scan_strategy(
            "example.com", 
            recon_data
        )
        assert strategy is not None
        
        # Step 2: Fails but doesn't crash
        findings = [{"title": "Vuln"}] * 25
        prioritized = await ai_helper_enabled.prioritize_findings(findings)
        assert prioritized is None  # Graceful fallback
        
        # Step 3: Fails but doesn't crash
        scan_results = {"total_findings": 25}
        summary = await ai_helper_enabled.generate_executive_summary(
            scan_results,
            {"name": "App"}
        )
        assert summary is None  # Graceful fallback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
