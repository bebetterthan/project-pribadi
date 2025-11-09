"""
Gemini API wrapper with retry, circuit breaker, and error handling
"""
import asyncio
import time
from typing import Any, Callable
from app.utils.retry import RetryConfig, retry_async
from app.utils.circuit_breaker import GEMINI_CIRCUIT_BREAKER
from app.utils.logger import logger
from app.utils.context import get_context
from app.core.exceptions import AIServiceError, AIQuotaExceededError, AIContentFilterError
from app.api.v1.endpoints.metrics import record_api_call, record_error


# Configure retry for Gemini API
GEMINI_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)


def translate_gemini_error(error: Exception) -> Exception:
    """
    Translate Gemini API errors to user-friendly exceptions
    
    Args:
        error: Original exception from Gemini API
        
    Returns:
        Translated exception with user-friendly message
    """
    error_str = str(error).lower()
    
    # Quota exceeded
    if "quota" in error_str or "429" in error_str:
        return AIQuotaExceededError()
    
    # Content filtered
    if "safety" in error_str or "blocked" in error_str or "filter" in error_str:
        return AIContentFilterError()
    
    # Rate limit
    if "rate limit" in error_str:
        return AIServiceError("Rate limit exceeded", technical_detail=str(error))
    
    # Authentication
    if "401" in error_str or "unauthorized" in error_str or "api key" in error_str:
        return AIServiceError("API authentication failed", technical_detail=str(error))
    
    # Network/timeout
    if "timeout" in error_str or "connection" in error_str:
        return AIServiceError("Network error", technical_detail=str(error))
    
    # Generic
    return AIServiceError("AI service unavailable", technical_detail=str(error))


async def call_gemini_with_protection(
    func: Callable,
    model_type: str = "FLASH",
    *args,
    **kwargs
) -> Any:
    """
    Call Gemini API with retry, circuit breaker, and error handling
    
    Args:
        func: Async function to call
        model_type: "FLASH" or "PRO" for metrics
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Response from Gemini API
        
    Raises:
        AIServiceError: Wrapped user-friendly error
    """
    context = get_context()
    
    # Define wrapped function with retry
    @retry_async(GEMINI_RETRY_CONFIG)
    @GEMINI_CIRCUIT_BREAKER.call_async
    async def _protected_call():
        try:
            start_time = time.time()
            
            # Make API call
            response = await func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Record metrics
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                record_api_call(
                    model=model_type.lower(),
                    input_tokens=getattr(usage, 'prompt_token_count', 0),
                    output_tokens=getattr(usage, 'candidates_token_count', 0),
                    duration_seconds=duration
                )
            
            # Log success
            logger.debug(
                f"Gemini API call successful ({model_type})",
                extra={
                    **context,
                    "model": model_type,
                    "duration_ms": int(duration * 1000)
                }
            )
            
            return response
            
        except Exception as e:
            # Translate error
            translated_error = translate_gemini_error(e)
            
            # Record error
            record_error(
                error_type=translated_error.error_code,
                component="gemini_api"
            )
            
            # Log error
            logger.error(
                f"Gemini API call failed: {translated_error.technical_detail}",
                extra={
                    **context,
                    "model": model_type,
                    "error_type": translated_error.error_code
                },
                exc_info=True
            )
            
            raise translated_error
    
    try:
        return await _protected_call()
    except Exception as e:
        # If it's already a translated error, re-raise it
        if isinstance(e, (AIServiceError, AIQuotaExceededError, AIContentFilterError)):
            raise
        # Otherwise, translate it
        raise translate_gemini_error(e)

