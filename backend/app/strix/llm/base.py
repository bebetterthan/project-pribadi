"""
LLM Provider Base Classes
Abstract interface for AI model integration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, AsyncIterator
from datetime import datetime
from enum import Enum


class ModelCapability(str, Enum):
    """LLM Capabilities"""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_GENERATION = "code_generation"
    STREAMING = "streaming"


@dataclass
class ModelConfig:
    """
    Configuration for LLM model
    """
    model_name: str
    provider: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    capabilities: List[ModelCapability] = field(default_factory=list)
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    context_window: int = 32000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """Single message in conversation"""
    role: str  # system, user, assistant, function
    content: str
    name: Optional[str] = None  # For function calls
    function_call: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LLMRequest:
    """
    Request to LLM provider
    """
    messages: List[LLMMessage]
    model_config: ModelConfig
    functions: Optional[List[Dict[str, Any]]] = None  # Function definitions
    function_call: Optional[str] = None  # "auto", "none", or {"name": "function_name"}
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """
    Response from LLM provider
    """
    content: str
    model: str
    finish_reason: str  # stop, length, function_call, error
    function_call: Optional[Dict[str, Any]] = None
    
    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Metadata
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "function_call": self.function_call,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens
            },
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "created_at": self.created_at.isoformat()
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers
    
    Subclasses must implement:
    - _generate(): Core text generation
    - _generate_stream(): Streaming generation
    - _count_tokens(): Token counting
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize LLM provider
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    @abstractmethod
    async def _generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from LLM (non-streaming)
        
        Args:
            request: LLM request
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    async def _generate_stream(
        self, 
        request: LLMRequest
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from LLM
        
        Args:
            request: LLM request
            
        Yields:
            Content chunks
        """
        pass
    
    @abstractmethod
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Input text
            
        Returns:
            Token count
        """
        pass
    
    async def generate(
        self,
        request: LLMRequest,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> LLMResponse:
        """
        Generate response with automatic streaming support
        
        Args:
            request: LLM request
            on_chunk: Optional callback for streaming chunks
            
        Returns:
            Complete LLM response
        """
        start_time = datetime.utcnow()
        
        try:
            if request.stream and on_chunk:
                # Streaming mode
                full_content = ""
                async for chunk in await self._generate_stream(request):  # type: ignore
                    full_content += chunk
                    on_chunk(chunk)
                
                # Create response from accumulated content
                response = LLMResponse(
                    content=full_content,
                    model=self.config.model_name,
                    finish_reason="stop",
                    prompt_tokens=self._count_tokens(
                        " ".join([m.content for m in request.messages])
                    ),
                    completion_tokens=self._count_tokens(full_content),
                    latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            else:
                # Non-streaming mode
                response = await self._generate(request)
            
            # Calculate total tokens and cost
            response.total_tokens = response.prompt_tokens + response.completion_tokens
            response.cost_usd = self._calculate_cost(
                response.prompt_tokens,
                response.completion_tokens
            )
            
            # Update statistics
            self.request_count += 1
            self.total_tokens += response.total_tokens
            self.total_cost += response.cost_usd
            
            return response
            
        except Exception as e:
            # Return error response
            return LLMResponse(
                content="",
                model=self.config.model_name,
                finish_reason="error",
                metadata={"error": str(e)},
                latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost of request
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output
        return input_cost + output_cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        return {
            "provider": self.config.provider,
            "model": self.config.model_name,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_tokens_per_request": (
                self.total_tokens // self.request_count 
                if self.request_count > 0 else 0
            )
        }
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
