"""
Google Gemini Provider Implementation
"""

import os
import json
from typing import AsyncIterator, List, Dict, Any, Optional
import google.generativeai as genai  # type: ignore
from google.generativeai.types import GenerationConfig  # type: ignore

from .base import LLMProvider, LLMRequest, LLMResponse, LLMMessage, ModelConfig, ModelCapability


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM Provider
    
    Supports:
    - gemini-2.0-flash-exp (fast, cost-effective)
    - gemini-1.5-pro (high capability)
    - gemini-1.5-flash (balanced)
    """
    
    def __init__(self, config: ModelConfig, api_key: Optional[str] = None):
        """
        Initialize Gemini provider
        
        Args:
            config: Model configuration
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        super().__init__(config)
        
        # Configure API
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        
        genai.configure(api_key=api_key)  # type: ignore
        
        # Initialize model
        self.model = genai.GenerativeModel(  # type: ignore
            model_name=config.model_name,
            generation_config=self._build_generation_config(config)
        )
    
    def _build_generation_config(self, config: ModelConfig) -> GenerationConfig:
        """Build Gemini generation config"""
        return GenerationConfig(
            max_output_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k
        )
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """
        Convert LLMMessage to Gemini format
        
        Gemini format:
        [{"role": "user", "parts": ["text"]}, {"role": "model", "parts": ["text"]}]
        """
        gemini_messages = []
        
        for msg in messages:
            # Map roles
            role = "model" if msg.role == "assistant" else msg.role
            
            # Skip system messages (Gemini doesn't support system role in chat)
            if role == "system":
                continue
            
            gemini_messages.append({
                "role": role,
                "parts": [msg.content]
            })
        
        return gemini_messages
    
    def _extract_system_prompt(self, messages: List[LLMMessage]) -> str:
        """Extract system message as instruction"""
        for msg in messages:
            if msg.role == "system":
                return msg.content
        return ""
    
    async def _generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate non-streaming response
        """
        import time
        start_time = time.time()
        
        try:
            # Extract system prompt
            system_prompt = self._extract_system_prompt(request.messages)
            
            # Convert messages
            gemini_messages = self._convert_messages(request.messages)
            
            # Handle function calling
            tools = None
            if request.functions:
                tools = self._convert_functions_to_tools(request.functions)
            
            # Start chat or single generation
            if len(gemini_messages) > 1:
                # Multi-turn chat
                chat = self.model.start_chat(history=gemini_messages[:-1])  # type: ignore
                response = chat.send_message(
                    gemini_messages[-1]["parts"][0],
                    tools=tools
                )
            else:
                # Single generation
                prompt = gemini_messages[0]["parts"][0] if gemini_messages else ""
                if system_prompt:
                    prompt = f"{system_prompt}\n\n{prompt}"
                
                response = self.model.generate_content(
                    prompt,
                    tools=tools
                )
            
            # Extract response
            content = response.text if response.text else ""
            
            # Check for function call
            function_call = None
            finish_reason = "stop"
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = {
                            "name": part.function_call.name,
                            "arguments": dict(part.function_call.args)
                        }
                        finish_reason = "function_call"
                        break
            
            # Token counts (approximate for Gemini)
            prompt_tokens = self._count_tokens(
                " ".join([m.content for m in request.messages])
            )
            completion_tokens = self._count_tokens(content)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=content,
                model=self.config.model_name,
                finish_reason=finish_reason,
                function_call=function_call,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model_name,
                finish_reason="error",
                metadata={"error": str(e)}
            )
    
    async def _generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Generate streaming response
        """
        try:
            # Extract system prompt
            system_prompt = self._extract_system_prompt(request.messages)
            
            # Convert messages
            gemini_messages = self._convert_messages(request.messages)
            
            # Prepare prompt
            if len(gemini_messages) > 1:
                chat = self.model.start_chat(history=gemini_messages[:-1])  # type: ignore
                prompt = gemini_messages[-1]["parts"][0]
            else:
                prompt = gemini_messages[0]["parts"][0] if gemini_messages else ""
                if system_prompt:
                    prompt = f"{system_prompt}\n\n{prompt}"
                chat = None
            
            # Stream response
            if chat:
                response_stream = chat.send_message(prompt, stream=True)
            else:
                response_stream = self.model.generate_content(prompt, stream=True)
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"[Error: {str(e)}]"
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens (approximate)
        
        Gemini uses SentencePiece tokenizer.
        Rough estimate: ~4 chars per token for English
        """
        # Try using Gemini's count_tokens method
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except:
            # Fallback to approximation
            return len(text) // 4
    
    def _convert_functions_to_tools(self, functions: List[Dict[str, Any]]) -> List:
        """
        Convert function definitions to Gemini tools format
        
        OpenAI format:
        {
            "name": "get_weather",
            "description": "Get weather",
            "parameters": {
                "type": "object",
                "properties": {...}
            }
        }
        
        Gemini format requires google.ai.generativelanguage types
        """
        from google.ai.generativelanguage_v1beta.types import FunctionDeclaration, Tool, Schema
        
        tool_declarations = []
        
        for func in functions:
            # Convert parameters schema
            params = func.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])
            
            # Build Schema
            function_schema = Schema(
                type="OBJECT",
                properties={
                    name: Schema(
                        type=prop.get("type", "STRING").upper(),
                        description=prop.get("description", "")
                    )
                    for name, prop in properties.items()
                },
                required=required
            )
            
            # Create FunctionDeclaration
            function_decl = FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters=function_schema
            )
            
            tool_declarations.append(function_decl)
        
        # Return as Tool
        return [Tool(function_declarations=tool_declarations)]


def create_gemini_flash() -> GeminiProvider:
    """Create Gemini Flash (fast, balanced) provider"""
    config = ModelConfig(
        model_name="gemini-2.0-flash-exp",
        provider="google",
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STREAMING,
            ModelCapability.CODE_GENERATION
        ],
        cost_per_1k_input=0.0,  # Free tier
        cost_per_1k_output=0.0,
        context_window=1000000  # 1M tokens
    )
    return GeminiProvider(config)


def create_gemini_pro() -> GeminiProvider:
    """Create Gemini Pro (high capability) provider"""
    config = ModelConfig(
        model_name="gemini-1.5-pro",
        provider="google",
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.CODE_GENERATION
        ],
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        context_window=2000000  # 2M tokens
    )
    return GeminiProvider(config)
