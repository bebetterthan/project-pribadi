"""
Agent Communication Protocol
Layer 1.3: Standard message passing between agents and orchestrator

Message Types:
- STATUS: Agent status updates (started, progress, completed)
- DATA: Data sharing between agents (findings, results)
- REQUEST: Help requests (need approval, stuck, need resource)
- QUERY: Questions to other agents (do you have X? did you find Y?)
"""
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4

from app.utils.logger import logger


class MessageType(str, Enum):
    """Types of messages agents can send"""
    STATUS = "status"       # Status updates to orchestrator
    DATA = "data"          # Data sharing with other agents
    REQUEST = "request"    # Help/approval requests
    QUERY = "query"        # Questions to other agents


class MessagePriority(str, Enum):
    """Message priority levels"""
    URGENT = "urgent"      # Requires immediate attention
    NORMAL = "normal"      # Standard message
    LOW = "low"           # Can be processed later


@dataclass
class Message:
    """
    Standard message format for agent communication
    
    All messages follow this structure for consistency
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    from_agent: str = ""           # Sender agent name
    to_agent: str = "orchestrator"  # Recipient (default: orchestrator)
    type: MessageType = MessageType.STATUS
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            id=data.get("id", str(uuid4())),
            from_agent=data.get("from", ""),
            to_agent=data.get("to", "orchestrator"),
            type=MessageType(data.get("type", "status")),
            priority=MessagePriority(data.get("priority", "normal")),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            acknowledged=data.get("acknowledged", False)
        )


class MessageQueue:
    """
    Simple message queue for agent communication
    
    Thread-safe queue for routing messages between agents
    """
    
    def __init__(self):
        self._messages: list[Message] = []
        self._subscribers: Dict[str, list] = {}  # agent_name -> callback functions
    
    def publish(self, message: Message) -> None:
        """
        Publish message to queue
        
        Args:
            message: Message to publish
        """
        self._messages.append(message)
        logger.debug(
            f"[MESSAGE] {message.from_agent} → {message.to_agent}: "
            f"{message.type.value} [{message.priority.value}]"
        )
        
        # Notify subscribers
        self._route_message(message)
    
    def subscribe(self, agent_name: str, callback) -> None:
        """
        Subscribe agent to receive messages
        
        Args:
            agent_name: Name of agent subscribing
            callback: Function to call when message arrives
        """
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(callback)
        logger.debug(f"[MESSAGE] {agent_name} subscribed to messages")
    
    def unsubscribe(self, agent_name: str) -> None:
        """
        Unsubscribe agent from messages
        
        Args:
            agent_name: Name of agent to unsubscribe
        """
        if agent_name in self._subscribers:
            del self._subscribers[agent_name]
            logger.debug(f"[MESSAGE] {agent_name} unsubscribed")
    
    def get_messages_for(
        self,
        agent_name: str,
        unread_only: bool = True
    ) -> list[Message]:
        """
        Get messages for specific agent
        
        Args:
            agent_name: Name of agent
            unread_only: Only return unacknowledged messages
        
        Returns:
            List of messages for this agent
        """
        messages = [
            msg for msg in self._messages
            if msg.to_agent == agent_name
        ]
        
        if unread_only:
            messages = [msg for msg in messages if not msg.acknowledged]
        
        return messages
    
    def acknowledge(self, message_id: str) -> None:
        """
        Mark message as acknowledged
        
        Args:
            message_id: ID of message to acknowledge
        """
        for msg in self._messages:
            if msg.id == message_id:
                msg.acknowledged = True
                logger.debug(f"[MESSAGE] Message {message_id[:8]} acknowledged")
                break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message queue statistics"""
        total = len(self._messages)
        by_type = {}
        by_priority = {}
        unread = sum(1 for msg in self._messages if not msg.acknowledged)
        
        for msg in self._messages:
            by_type[msg.type.value] = by_type.get(msg.type.value, 0) + 1
            by_priority[msg.priority.value] = by_priority.get(msg.priority.value, 0) + 1
        
        return {
            "total_messages": total,
            "unread_messages": unread,
            "by_type": by_type,
            "by_priority": by_priority,
            "subscribers": list(self._subscribers.keys())
        }
    
    def clear(self) -> None:
        """Clear all messages (for testing)"""
        count = len(self._messages)
        self._messages.clear()
        logger.info(f"[MESSAGE] Queue cleared: {count} messages removed")
    
    def _route_message(self, message: Message) -> None:
        """
        Route message to subscriber callbacks
        
        Args:
            message: Message to route
        """
        recipient = message.to_agent
        
        # Route to specific agent
        if recipient in self._subscribers:
            for callback in self._subscribers[recipient]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"[MESSAGE] Callback error for {recipient}: {e}")
        
        # Also route to orchestrator if not already the recipient
        if recipient != "orchestrator" and "orchestrator" in self._subscribers:
            for callback in self._subscribers["orchestrator"]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"[MESSAGE] Orchestrator callback error: {e}")


# Global message queue instance
_message_queue: Optional[MessageQueue] = None


def get_message_queue() -> MessageQueue:
    """Get or create global message queue instance"""
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueue()
        logger.info("[MESSAGE] Message queue initialized")
    return _message_queue


# Convenience functions for common message types
def send_status_update(
    from_agent: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Send status update to orchestrator"""
    queue = get_message_queue()
    message = Message(
        from_agent=from_agent,
        to_agent="orchestrator",
        type=MessageType.STATUS,
        payload={
            "status": status,
            "details": details or {}
        }
    )
    queue.publish(message)


def send_data(
    from_agent: str,
    to_agent: str,
    data_type: str,
    data: Any
) -> None:
    """Send data to another agent"""
    queue = get_message_queue()
    message = Message(
        from_agent=from_agent,
        to_agent=to_agent,
        type=MessageType.DATA,
        payload={
            "data_type": data_type,
            "data": data
        }
    )
    queue.publish(message)


def send_request(
    from_agent: str,
    request_type: str,
    details: Dict[str, Any],
    urgent: bool = False
) -> None:
    """Send request to orchestrator"""
    queue = get_message_queue()
    message = Message(
        from_agent=from_agent,
        to_agent="orchestrator",
        type=MessageType.REQUEST,
        priority=MessagePriority.URGENT if urgent else MessagePriority.NORMAL,
        payload={
            "request_type": request_type,
            "details": details
        }
    )
    queue.publish(message)


def send_query(
    from_agent: str,
    to_agent: str,
    question: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Send query to another agent"""
    queue = get_message_queue()
    message = Message(
        from_agent=from_agent,
        to_agent=to_agent,
        type=MessageType.QUERY,
        payload={
            "question": question,
            "context": context or {}
        }
    )
    queue.publish(message)
