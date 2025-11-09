"""
Unit tests for Ollama Provider.

Tests cover:
- Successful response handling
- Timeout handling
- Retry logic with intermittent failures
- Error parsing with malformed JSON
- Configuration loading with various values
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx
from backend.app.services.ollama_provider import OllamaProvider, OllamaResponse


@pytest.fixture
def provider():
    """Create provider instance for testing."""
    return OllamaProvider(
        url="http://localhost:11434",
        model="qwen2.5:14b",
        timeout=30
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing."""
    with patch('backend.app.services.ollama_provider.httpx.AsyncClient') as mock:
        yield mock


class TestOllamaProvider:
    """Test suite for OllamaProvider class."""
    
    @pytest.mark.asyncio
    async def test_successful_response(self, provider):
        """Test successful API response handling."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "This is a test response",
            "eval_count": 50,
            "model": "qwen2.5:14b"
        }
        mock_response.raise_for_status = Mock()
        
        provider.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await provider.generate("Test prompt")
        
        # Verify
        assert result.success is True
        assert result.response == "This is a test response"
        assert result.tokens == 50
        assert result.duration_seconds > 0
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, provider):
        """Test timeout handling with delayed response."""
        # Mock timeout
        provider.client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        
        # Execute
        result = await provider.generate("Test prompt")
        
        # Verify
        assert result.success is False
        assert "timed out" in result.error.lower()
        assert result.response == ""
        assert result.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_retry_logic_intermittent_failure(self, provider):
        """Test retry logic with intermittent failures."""
        # Mock first call fails, second succeeds
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Success after retry",
            "eval_count": 25
        }
        mock_response.raise_for_status = Mock()
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection failed")
            return mock_response
        
        provider.client.post = mock_post
        
        # Execute
        result = await provider.generate("Test prompt")
        
        # Verify
        assert result.success is True
        assert result.response == "Success after retry"
        assert call_count == 2  # Retried once
    
    @pytest.mark.asyncio
    async def test_error_parsing_malformed_json(self, provider):
        """Test error handling with malformed JSON response."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        
        provider.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await provider.generate("Test prompt")
        
        # Verify
        assert result.success is False
        assert "error" in result.error.lower() or "invalid" in result.error.lower()
        assert result.response == ""
    
    @pytest.mark.asyncio
    async def test_connection_error(self, provider):
        """Test handling of connection errors."""
        # Mock connection error
        provider.client.post = AsyncMock(
            side_effect=httpx.ConnectError("Cannot connect")
        )
        
        # Execute  
        result = await provider.generate("Test prompt")
        
        # Verify
        assert result.success is False
        assert "connect" in result.error.lower()
        assert result.response == ""
    
    def test_configuration_from_env(self):
        """Test configuration loading from environment variables."""
        with patch.dict('os.environ', {
            'OLLAMA_URL': 'https://custom-url.com',
            'OLLAMA_MODEL': 'custom-model:7b',
            'OLLAMA_TIMEOUT': '60'
        }):
            provider = OllamaProvider()
            
            assert provider.url == 'https://custom-url.com'
            assert provider.model == 'custom-model:7b'
            assert provider.timeout == 60
    
    def test_configuration_defaults(self):
        """Test default configuration values."""
        with patch.dict('os.environ', {}, clear=True):
            provider = OllamaProvider()
            
            assert "zany-acorn" in provider.url  # Default Codespaces URL
            assert provider.model == "qwen2.5:14b"
            assert provider.timeout == 30
    
    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid OLLAMA_URL"):
            OllamaProvider(url="not-a-valid-url")
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, provider):
        """Test response caching."""
        # Enable cache
        provider.cache_enabled = True
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Cached response",
            "eval_count": 30
        }
        mock_response.raise_for_status = Mock()
        
        provider.client.post = AsyncMock(return_value=mock_response)
        
        # First call
        result1 = await provider.generate("Test prompt")
        assert result1.success is True
        
        # Second call should use cache
        result2 = await provider.generate("Test prompt")
        assert result2.success is True
        assert result2.response == result1.response
        
        # Verify only called once (cached second time)
        assert provider.client.post.call_count == 1
    
    @pytest.mark.asyncio
    async def test_force_no_cache(self, provider):
        """Test bypassing cache with force_no_cache flag."""
        provider.cache_enabled = True
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Fresh response",
            "eval_count": 20
        }
        mock_response.raise_for_status = Mock()
        
        provider.client.post = AsyncMock(return_value=mock_response)
        
        # Two calls with force_no_cache
        await provider.generate("Test prompt", force_no_cache=True)
        await provider.generate("Test prompt", force_no_cache=True)
        
        # Verify called twice (cache bypassed)
        assert provider.client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_build_full_prompt_with_context(self, provider):
        """Test prompt building with context."""
        prompt = "Analyze vulnerability"
        context = {"severity": "high", "target": "web app"}
        system_prompt = "You are a security expert"
        
        full_prompt = provider._build_full_prompt(prompt, context, system_prompt)
        
        assert "SYSTEM: You are a security expert" in full_prompt
        assert "CONTEXT:" in full_prompt
        assert "severity: high" in full_prompt
        assert "target: web app" in full_prompt
        assert "Analyze vulnerability" in full_prompt
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        
        provider.client.get = AsyncMock(return_value=mock_response)
        
        result = await provider.health_check()
        
        assert result is True
        provider.client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """Test failed health check."""
        provider.client.get = AsyncMock(
            side_effect=httpx.ConnectError("Service down")
        )
        
        result = await provider.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_test_inference(self, provider):
        """Test inference testing method."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "OK",
            "eval_count": 1
        }
        mock_response.raise_for_status = Mock()
        
        provider.client.post = AsyncMock(return_value=mock_response)
        
        success, duration = await provider.test_inference()
        
        assert success is True
        assert duration > 0
    
    @pytest.mark.asyncio
    async def test_close_cleanup(self, provider):
        """Test resource cleanup."""
        provider.client.aclose = AsyncMock()
        
        await provider.close()
        
        provider.client.aclose.assert_called_once()
    
    def test_clear_cache(self, provider):
        """Test cache clearing."""
        provider._cache = {"key1": "value1", "key2": "value2"}
        
        provider.clear_cache()
        
        assert len(provider._cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
