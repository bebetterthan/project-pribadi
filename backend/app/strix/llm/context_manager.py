"""
Context Window Management
Automatic pruning and token tracking
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .base import LLMMessage, ModelConfig


@dataclass
class ContextEntry:
    """Single context entry with metadata"""
    message: LLMMessage
    tokens: int
    importance: float = 1.0  # 0.0 to 1.0
    is_pinned: bool = False  # Pinned messages never pruned
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    Manage conversation context with automatic pruning
    
    Features:
    - Token counting and limit enforcement
    - Smart pruning (keep important/recent messages)
    - Pinned messages (system prompts, key info)
    - Context statistics
    """
    
    def __init__(
        self,
        model_config: ModelConfig,
        token_counter: Callable[[str], int],  # Callable type for function
        max_tokens: Optional[int] = None,
        reserve_tokens: int = 1000  # Reserve for completion
    ):
        """
        Initialize context manager
        
        Args:
            model_config: Model configuration
            token_counter: Function to count tokens (takes str, returns int)
            max_tokens: Max context tokens (defaults to model's limit)
            reserve_tokens: Tokens to reserve for completion
        """
        self.model_config = model_config
        self.token_counter = token_counter
        self.max_tokens = max_tokens or (model_config.context_window - reserve_tokens)
        self.reserve_tokens = reserve_tokens
        
        self.entries: List[ContextEntry] = []
        self.total_tokens = 0
        self.pruned_count = 0
    
    def add_message(
        self,
        message: LLMMessage,
        importance: float = 1.0,
        is_pinned: bool = False
    ) -> None:
        """
        Add message to context
        
        Args:
            message: Message to add
            importance: Importance score (0-1)
            is_pinned: Whether message should be pinned
        """
        tokens = self.token_counter(message.content)
        
        entry = ContextEntry(
            message=message,
            tokens=tokens,
            importance=importance,
            is_pinned=is_pinned
        )
        
        self.entries.append(entry)
        self.total_tokens += tokens
        
        # Auto-prune if over limit
        if self.total_tokens > self.max_tokens:
            self._prune()
    
    def add_messages(self, messages: List[LLMMessage]) -> None:
        """Add multiple messages"""
        for msg in messages:
            # System messages are pinned
            is_pinned = (msg.role == "system")
            self.add_message(msg, is_pinned=is_pinned)
    
    def get_messages(self) -> List[LLMMessage]:
        """Get all messages in context"""
        return [entry.message for entry in self.entries]
    
    def get_messages_for_request(self, additional_tokens: int = 0) -> List[LLMMessage]:
        """
        Get messages ensuring space for completion
        
        Args:
            additional_tokens: Expected tokens in next user message
            
        Returns:
            Pruned message list
        """
        # Check if we need to prune for additional tokens
        needed_space = additional_tokens + self.reserve_tokens
        if self.total_tokens + needed_space > self.max_tokens:
            self._prune(target_tokens=self.max_tokens - needed_space)
        
        return self.get_messages()
    
    def _prune(self, target_tokens: Optional[int] = None) -> None:
        """
        Prune context to fit within token limit
        
        Strategy:
        1. Keep all pinned messages
        2. Keep recent messages
        3. Remove lowest importance messages first
        
        Args:
            target_tokens: Target token count (defaults to max_tokens)
        """
        target = target_tokens or self.max_tokens
        
        if self.total_tokens <= target:
            return
        
        # Separate pinned and unpinned
        pinned = [e for e in self.entries if e.is_pinned]
        unpinned = [e for e in self.entries if not e.is_pinned]
        
        # Calculate pinned tokens
        pinned_tokens = sum(e.tokens for e in pinned)
        
        # Available space for unpinned
        available = target - pinned_tokens
        
        if available < 0:
            # Even pinned messages exceed limit - critical issue
            # Keep only system messages
            self.entries = [e for e in pinned if e.message.role == "system"]
            self.total_tokens = sum(e.tokens for e in self.entries)
            return
        
        # Sort unpinned by: recency (desc) then importance (desc)
        # This keeps recent important messages
        unpinned.sort(
            key=lambda e: (e.message.timestamp, e.importance),
            reverse=True
        )
        
        # Select messages to keep
        kept_unpinned = []
        current_tokens = 0
        
        for entry in unpinned:
            if current_tokens + entry.tokens <= available:
                kept_unpinned.append(entry)
                current_tokens += entry.tokens
            else:
                self.pruned_count += 1
        
        # Combine pinned and kept unpinned, restore chronological order
        self.entries = sorted(
            pinned + kept_unpinned,
            key=lambda e: e.message.timestamp
        )
        
        self.total_tokens = sum(e.tokens for e in self.entries)
    
    def pin_message(self, index: int) -> None:
        """Pin a message by index"""
        if 0 <= index < len(self.entries):
            self.entries[index].is_pinned = True
    
    def unpin_message(self, index: int) -> None:
        """Unpin a message by index"""
        if 0 <= index < len(self.entries):
            self.entries[index].is_pinned = False
    
    def clear(self, keep_pinned: bool = True) -> None:
        """
        Clear context
        
        Args:
            keep_pinned: Whether to keep pinned messages
        """
        if keep_pinned:
            self.entries = [e for e in self.entries if e.is_pinned]
        else:
            self.entries = []
        
        self.total_tokens = sum(e.tokens for e in self.entries)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        pinned_count = sum(1 for e in self.entries if e.is_pinned)
        
        return {
            "total_messages": len(self.entries),
            "pinned_messages": pinned_count,
            "unpinned_messages": len(self.entries) - pinned_count,
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": round(self.total_tokens / self.max_tokens * 100, 1),
            "available_tokens": max(0, self.max_tokens - self.total_tokens),
            "pruned_count": self.pruned_count
        }
    
    def export_context(self) -> Dict[str, Any]:
        """Export full context for analysis"""
        return {
            "model": self.model_config.model_name,
            "stats": self.get_stats(),
            "messages": [
                {
                    "role": e.message.role,
                    "content": e.message.content[:100] + "..." if len(e.message.content) > 100 else e.message.content,
                    "tokens": e.tokens,
                    "importance": e.importance,
                    "is_pinned": e.is_pinned,
                    "timestamp": e.message.timestamp.isoformat()
                }
                for e in self.entries
            ]
        }
