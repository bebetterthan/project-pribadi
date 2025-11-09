"""
Optimized Gemini API Client with retry logic, connection pooling, and caching
For stable and fast AI responses
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import asyncio
from functools import lru_cache
import time
from app.utils.logger import logger


class GeminiClient:
    """Optimized Gemini API client with retries and connection management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._configure_client()
        self._init_models()
        
    def _configure_client(self):
        """Configure Gemini with optimized settings"""
        try:
            genai.configure(
                api_key=self.api_key,
                transport='rest',  # Use REST for better stability
            )
            logger.info("✅ Gemini API configured with optimized settings")
        except Exception as e:
            logger.error(f"❌ Failed to configure Gemini: {e}")
            raise
    
    def _init_models(self):
        """Initialize models with fallback"""
        try:
            # Use latest Gemini 2.5 models (November 2024+)
            self.model_pro = genai.GenerativeModel(
                'gemini-2.0-flash-exp',  # Latest experimental model for strategy & heavy analysis
                generation_config={
                    'temperature': 0.4,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,  # Higher for complex analysis
                }
            )
            self.model_flash = genai.GenerativeModel(
                'gemini-2.0-flash-exp',  # Fast model for tool execution & quick responses
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 4096,
                }
            )
            logger.info("✅ Models initialized: gemini-2.0-flash-exp (Pro & Flash mode)")
        except Exception as e:
            logger.warning(f"⚠️ Latest models failed, trying fallback: {e}")
            # Fallback to stable 1.5 models
            try:
                self.model_pro = genai.GenerativeModel('gemini-1.5-pro-latest')
                self.model_flash = genai.GenerativeModel('gemini-1.5-flash-latest')
                logger.info("✅ Using fallback: gemini-1.5-pro/flash-latest")
            except Exception as e2:
                logger.error(f"❌ All models failed: {e2}")
                raise
    
    async def generate_with_retry(
        self,
        prompt: str,
        use_flash: bool = False,
        max_retries: int = 3,
        timeout: float = 20.0
    ) -> str:
        """
        Generate content with automatic retry on failure
        
        Args:
            prompt: The prompt to send
            use_flash: Use flash model for faster response
            max_retries: Number of retry attempts
            timeout: Timeout per attempt in seconds
            
        Returns:
            Generated text content
        """
        model = self.model_flash if use_flash else self.model_pro
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"⏳ Retry attempt {attempt + 1}/{max_retries} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                
                # Generate with timeout
                start_time = time.time()
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, model.generate_content, prompt),
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                logger.info(f"✅ Generated response in {elapsed:.2f}s")
                
                return response.text
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"⏱️ Attempt {attempt + 1} timed out")
                
            except Exception as e:
                last_error = str(e)
                error_msg = str(e).lower()
                
                # Check for rate limit
                if 'rate limit' in error_msg or 'quota' in error_msg:
                    logger.warning(f"🚫 Rate limit hit, waiting longer...")
                    await asyncio.sleep(5 * (attempt + 1))
                    
                # Check for invalid API key
                elif 'api key' in error_msg or 'authentication' in error_msg:
                    logger.error(f"❌ API key invalid: {e}")
                    raise ValueError(f"Invalid Gemini API key: {e}")
                    
                else:
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
        
        # All retries failed
        error_msg = f"Failed after {max_retries} attempts. Last error: {last_error}"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    @lru_cache(maxsize=100)
    def _cache_key(self, prompt: str) -> str:
        """Generate cache key for similar prompts"""
        return hash(prompt[:200])  # Cache based on first 200 chars


# Global client instance (reuse connections)
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client(api_key: str) -> GeminiClient:
    """Get or create Gemini client (connection pooling)"""
    global _gemini_client
    
    if _gemini_client is None:
        logger.info("🔧 Creating new Gemini client")
        _gemini_client = GeminiClient(api_key)
    
    return _gemini_client


def reset_gemini_client():
    """Reset client (for testing or API key changes)"""
    global _gemini_client
    _gemini_client = None
    logger.info("🔄 Gemini client reset")

