"""
Ollama Provider - Clean wrapper for Qwen 2.5 14B communication.

This module provides a simple, reliable interface to the Ollama API running
on GitHub Codespaces. It handles all HTTP complexity, error handling, retries,
and timeout management so the rest of Agent-P doesn't need to worry about it.

Design Philosophy:
- Never crash the application - always return a result (success or failure)
- Retry once automatically with 2-second delay
- Log everything at appropriate detail level
- Configuration through environment variables
- Clear error messages that help troubleshooting
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class OllamaResponse:
    """
    Standardized response format from Ollama API.
    
    Attributes:
        success: Whether the request completed successfully
        response: The actual text response from the model
        duration_seconds: How long the request took
        error: Error message if request failed
        model: Which model was used
        tokens: Number of tokens in response (if available)
    """
    success: bool
    response: str
    duration_seconds: float
    error: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[int] = None


class OllamaProvider:
    """
    Provider wrapper for Ollama API communication.
    
    This class handles all interaction with the Ollama service running on
    Codespaces. It manages HTTP requests, timeouts, retries, and error handling
    so the rest of Agent-P can just call generate() and get a response.
    
    Configuration via environment variables:
        OLLAMA_URL: Base URL for Ollama API (default: Codespaces public URL)
        OLLAMA_MODEL: Model identifier (default: qwen2.5:14b)
        OLLAMA_TIMEOUT: Request timeout in seconds (default: 30)
        ENABLE_RESPONSE_CACHE: Whether to cache responses (default: true)
    
    Example usage:
        provider = OllamaProvider()
        response = await provider.generate(
            prompt="Analyze this vulnerability",
            context={"severity": "high", "target": "banking app"}
        )
        if response.success:
            print(response.response)
        else:
            logger.error(f"AI unavailable: {response.error}")
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Ollama provider with configuration.
        
        Args:
            url: Override default Ollama URL
            model: Override default model name
            timeout: Override default timeout in seconds
        """
        # Load configuration with sensible defaults
        self.url = url or os.getenv(
            "OLLAMA_URL",
            "https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev"
        )
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        self.timeout = timeout or int(os.getenv("OLLAMA_TIMEOUT", "30"))
        
        # Validate configuration
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid OLLAMA_URL: {self.url}")
        
        if self.timeout < 10 or self.timeout > 120:
            logger.warning(
                f"Timeout {self.timeout}s outside recommended range 10-120s"
            )
        
        # Initialize HTTP client with proper timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            follow_redirects=True
        )
        
        # Response cache (simple in-memory dict)
        self.cache_enabled = os.getenv("ENABLE_RESPONSE_CACHE", "true").lower() == "true"
        self._cache: Dict[str, OllamaResponse] = {}
        
        logger.info(
            f"Ollama provider initialized: model={self.model}, "
            f"timeout={self.timeout}s, cache={self.cache_enabled}"
        )
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        force_no_cache: bool = False
    ) -> OllamaResponse:
        """
        Generate AI response for given prompt.
        
        This is the main method other parts of Agent-P should use. It handles
        all complexity of calling Ollama, including retries, timeouts, and
        error handling. Always returns a response - never throws exceptions.
        
        Args:
            prompt: The question or instruction for the AI
            context: Optional metadata about the scan/request
            system_prompt: Optional system instructions to guide behavior
            force_no_cache: Skip cache even if enabled
            
        Returns:
            OllamaResponse with success status and either response text or error
        """
        # Check cache first
        cache_key = f"{prompt}:{system_prompt}"
        if self.cache_enabled and not force_no_cache and cache_key in self._cache:
            logger.debug("Returning cached response")
            return self._cache[cache_key]
        
        start_time = time.time()
        
        try:
            # Build request payload
            payload = {
                "model": self.model,
                "prompt": self._build_full_prompt(prompt, context, system_prompt),
                "stream": False
            }
            
            logger.debug(f"Sending request to Ollama: {len(prompt)} chars")
            
            # Make request with retry logic
            response = await self._make_request_with_retry(payload)
            
            duration = time.time() - start_time
            
            # Parse successful response
            result = OllamaResponse(
                success=True,
                response=response.get("response", ""),
                duration_seconds=duration,
                model=self.model,
                tokens=response.get("eval_count")
            )
            
            # Cache if enabled
            if self.cache_enabled:
                self._cache[cache_key] = result
            
            logger.info(
                f"Ollama response received: {duration:.2f}s, "
                f"{result.tokens or 0} tokens"
            )
            
            return result
            
        except httpx.TimeoutException:
            duration = time.time() - start_time
            error_msg = f"Request timed out after {duration:.1f}s"
            logger.warning(error_msg)
            return OllamaResponse(
                success=False,
                response="",
                duration_seconds=duration,
                error=error_msg
            )
            
        except httpx.ConnectError as e:
            duration = time.time() - start_time
            error_msg = f"Cannot connect to Ollama at {self.url}: {str(e)}"
            logger.error(error_msg)
            return OllamaResponse(
                success=False,
                response="",
                duration_seconds=duration,
                error=error_msg
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.exception("Ollama provider error")
            return OllamaResponse(
                success=False,
                response="",
                duration_seconds=duration,
                error=error_msg
            )
    
    async def _make_request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request with single retry on failure.
        
        Args:
            payload: Request body to send
            
        Returns:
            Parsed JSON response
            
        Raises:
            httpx exceptions on failure after retry
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(2):  # Try once, retry once
            try:
                response = await self.client.post(
                    f"{self.url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                last_exception = e
                if attempt == 0:  # First attempt failed
                    logger.warning(f"Request failed, retrying in 2s: {str(e)}")
                    await asyncio.sleep(2)
                    continue
                else:  # Second attempt failed
                    raise last_exception
        
        # Should never reach here, but satisfy type checker
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")
    
    def _build_full_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        system_prompt: Optional[str]
    ) -> str:
        """
        Build complete prompt with context and system instructions.
        
        Args:
            prompt: Main user prompt
            context: Optional context metadata
            system_prompt: Optional system instructions
            
        Returns:
            Formatted prompt string
        """
        parts = []
        
        # Add system prompt if provided
        if system_prompt:
            parts.append(f"SYSTEM: {system_prompt}\n")
        
        # Add context if provided
        if context:
            parts.append("CONTEXT:")
            for key, value in context.items():
                parts.append(f"  {key}: {value}")
            parts.append("")
        
        # Add main prompt
        parts.append(prompt)
        
        return "\n".join(parts)
    
    async def health_check(self) -> bool:
        """
        Check if Ollama service is healthy and responding.
        
        Returns:
            True if service healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.url}/api/version", timeout=5.0)
            response.raise_for_status()
            logger.info("Ollama health check: OK")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def test_inference(self) -> tuple[bool, float]:
        """
        Test model inference with simple prompt.
        
        Returns:
            Tuple of (success, response_time_seconds)
        """
        result = await self.generate("Respond with OK", force_no_cache=True)
        return result.success, result.duration_seconds
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
        logger.info("Ollama provider closed")
    
    def clear_cache(self):
        """Clear response cache."""
        self._cache.clear()
        logger.debug("Response cache cleared")
