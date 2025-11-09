"""
Chat Logger - Helper to save SSE messages to database
Enables chat history replay
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat_message import ChatMessage
from app.utils.logger import logger
import json


class ChatLogger:
    """
    Logs SSE messages to database for later replay
    Thread-safe and async-compatible
    """
    
    def __init__(self, scan_id: str, db: Session):
        self.scan_id = scan_id
        self.db = db
        self.message_counter = 0
    
    def log_message(
        self,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Log a single SSE message to database
        
        Args:
            message_type: Type of message (system, thought, plan, tool, output, analysis, decision)
            content: The message content
            metadata: Optional metadata dict
        
        Returns:
            ChatMessage instance
        """
        self.message_counter += 1
        
        # Create message
        message = ChatMessage(
            scan_id=self.scan_id,
            message_type=message_type,
            content=content,
            sequence=self.message_counter,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        
        try:
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            logger.debug(f"💬 Chat logged [{message_type}] #{self.message_counter}: {content[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"❌ Failed to log chat message: {e}")
            self.db.rollback()
            raise
    
    def log_system(self, content: str, **metadata) -> ChatMessage:
        """Log system message"""
        return self.log_message('system', content, metadata)
    
    def log_thought(self, content: str, **metadata) -> ChatMessage:
        """Log AI thought/reasoning"""
        return self.log_message('thought', content, metadata)
    
    def log_plan(self, content: str, **metadata) -> ChatMessage:
        """Log AI planning decision"""
        return self.log_message('plan', content, metadata)
    
    def log_tool(self, content: str, **metadata) -> ChatMessage:
        """Log tool execution start"""
        return self.log_message('tool', content, metadata)
    
    def log_output(self, content: str, **metadata) -> ChatMessage:
        """Log tool output/results"""
        return self.log_message('output', content, metadata)
    
    def log_analysis(self, content: str, **metadata) -> ChatMessage:
        """Log AI analysis"""
        return self.log_message('analysis', content, metadata)
    
    def log_decision(self, content: str, **metadata) -> ChatMessage:
        """Log AI decision"""
        return self.log_message('decision', content, metadata)
    
    @staticmethod
    def get_chat_history(scan_id: str, db: Session) -> list:
        """
        Retrieve complete chat history for a scan
        
        Args:
            scan_id: Scan ID
            db: Database session
        
        Returns:
            List of chat messages ordered by sequence
        """
        messages = db.query(ChatMessage).filter(
            ChatMessage.scan_id == scan_id
        ).order_by(
            ChatMessage.sequence.asc()
        ).all()
        
        return [msg.to_dict() for msg in messages]
    
    @staticmethod
    def get_latest_messages(scan_id: str, db: Session, limit: int = 50) -> list:
        """Get latest N messages"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.scan_id == scan_id
        ).order_by(
            ChatMessage.sequence.desc()
        ).limit(limit).all()
        
        # Reverse to chronological order
        messages.reverse()
        
        return [msg.to_dict() for msg in messages]

