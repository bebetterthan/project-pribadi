"""
STRIX Foundation Layer - Agent Base System
Layer 1.1: Agent Base Class

Purpose:
    Abstract foundation that all specialized agents inherit from.
    Provides core functionality: initialization, execution, communication, lifecycle.

Philosophy:
    Simple, testable, maintainable. No over-engineering.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from dataclasses import dataclass, field


class AgentType(Enum):
    """Types of specialized agents"""
    RECON = "recon"              # Reconnaissance agent
    VULN = "vulnerability"        # Vulnerability testing agent
    EVIDENCE = "evidence"         # Evidence collection agent
    REPORT = "report"             # Report generation agent
    COORDINATOR = "coordinator"   # Orchestrator agent


class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"                 # Created but not started
    RUNNING = "running"           # Actively executing
    WAITING = "waiting"           # Paused, waiting for dependency
    COMPLETED = "completed"       # Finished successfully
    ERROR = "error"              # Encountered unrecoverable error


@dataclass
class AgentTask:
    """Task assigned to an agent"""
    task_id: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1=highest, 10=lowest
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResult:
    """Result produced by an agent"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """
    Abstract base class for all Strix agents.
    
    All specialized agents must inherit from this class.
    
    Lifecycle:
        1. __init__: Agent created
        2. initialize(): Setup working environment
        3. execute(): Perform task
        4. cleanup(): Clean up resources
    """
    
    def __init__(
        self, 
        agent_type: AgentType,
        task: AgentTask,
        target: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent.
        
        Args:
            agent_type: Type of agent (RECON, VULN, etc)
            task: Task assigned to this agent
            target: Scan target (domain, IP, URL)
            config: Agent configuration
        """
        # Identity
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.agent_name = f"{agent_type.value}_{self.agent_id[:8]}"
        
        # Task
        self.task = task
        self.target = target
        self.config = config or {}
        
        # State
        self.state = AgentState.IDLE
        self.state_history: List[tuple[AgentState, datetime]] = [
            (AgentState.IDLE, datetime.utcnow())
        ]
        
        # Results
        self.results: List[AgentResult] = []
        self.errors: List[str] = []
        
        # Timing
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Communication
        self.messages: List[Dict[str, Any]] = []
        
        # Shared context (set by orchestrator)
        self.shared_context: Optional[Any] = None
    
    def set_shared_context(self, context: Any) -> None:
        """Set reference to shared context for data access"""
        self.shared_context = context
    
    def transition_state(self, new_state: AgentState, reason: Optional[str] = None) -> None:
        """
        Transition agent to new state.
        
        Args:
            new_state: Target state
            reason: Optional reason for transition
        """
        old_state = self.state
        self.state = new_state
        self.state_history.append((new_state, datetime.utcnow()))
        
        # Log transition
        self._log(f"State transition: {old_state.value} → {new_state.value}" + 
                 (f" ({reason})" if reason else ""))
        
        # Send status update
        self.send_message(
            msg_type="status_update",
            payload={
                "old_state": old_state.value,
                "new_state": new_state.value,
                "reason": reason
            }
        )
    
    def send_message(
        self, 
        msg_type: str, 
        payload: Any,
        to: Optional[str] = None,
        priority: int = 5
    ) -> None:
        """
        Send message to orchestrator or other agents.
        
        Args:
            msg_type: Message type (status_update, data_share, request, query)
            payload: Message content
            to: Recipient (None = orchestrator)
            priority: Message priority (1=urgent, 10=low)
        """
        message = {
            "from": self.agent_id,
            "from_name": self.agent_name,
            "to": to or "orchestrator",
            "type": msg_type,
            "payload": payload,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.messages.append(message)
        self._log(f"Sent message: {msg_type} → {message['to']}")
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive message from orchestrator or other agents.
        
        Args:
            message: Message to process
        """
        self._log(f"Received message: {message['type']} from {message.get('from_name', 'unknown')}")
        self.handle_message(message)
    
    @abstractmethod
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received message. Must be implemented by subclass.
        
        Args:
            message: Message to handle
        """
        pass
    
    def run(self) -> AgentResult:
        """
        Main execution flow.
        
        Returns:
            AgentResult with execution outcome
        """
        try:
            # 1. Initialize
            self.transition_state(AgentState.RUNNING, "Starting execution")
            self.started_at = datetime.utcnow()
            
            self._log(f"Initializing agent for task: {self.task.description}")
            self.initialize()
            
            # 2. Execute main task
            self._log(f"Executing task: {self.task.description}")
            result = self.execute()
            
            # 3. Store result
            self.results.append(result)
            
            # 4. Cleanup
            self._log("Cleaning up")
            self.cleanup()
            
            # 5. Mark complete
            self.completed_at = datetime.utcnow()
            self.transition_state(AgentState.COMPLETED, "Task completed successfully")
            
            # 6. Send completion notification
            self.send_message(
                msg_type="task_completed",
                payload={
                    "task_id": self.task.task_id,
                    "success": result.success,
                    "summary": self._get_result_summary(result)
                },
                priority=3
            )
            
            return result
            
        except Exception as e:
            # Error handling
            error_msg = f"Agent execution failed: {str(e)}"
            self.errors.append(error_msg)
            self._log(error_msg, level="ERROR")
            
            self.completed_at = datetime.utcnow()
            self.transition_state(AgentState.ERROR, str(e))
            
            # Send error notification
            self.send_message(
                msg_type="task_failed",
                payload={
                    "task_id": self.task.task_id,
                    "error": str(e)
                },
                priority=1  # High priority
            )
            
            return AgentResult(
                success=False,
                error=error_msg
            )
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize agent working environment.
        Must be implemented by subclass.
        """
        pass
    
    @abstractmethod
    def execute(self) -> AgentResult:
        """
        Execute main agent task.
        Must be implemented by subclass.
        
        Returns:
            AgentResult with execution outcome
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up agent resources.
        Must be implemented by subclass.
        """
        pass
    
    def _get_result_summary(self, result: AgentResult) -> str:
        """Generate human-readable summary of result"""
        if result.success:
            return f"Task completed successfully"
        else:
            return f"Task failed: {result.error}"
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log agent activity.
        
        Args:
            message: Log message
            level: Log level (INFO, ERROR, DEBUG)
        """
        from app.utils.logger import logger
        
        log_msg = f"[{self.agent_name}] {message}"
        
        if level == "ERROR":
            logger.error(log_msg)
        elif level == "DEBUG":
            logger.debug(log_msg)
        else:
            logger.info(log_msg)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dict with agent status information
        """
        duration = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            duration = (end_time - self.started_at).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type.value,
            "state": self.state.value,
            "task": {
                "id": self.task.task_id,
                "description": self.task.description,
                "priority": self.task.priority
            },
            "target": self.target,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "results_count": len(self.results),
            "errors_count": len(self.errors),
            "messages_sent": len(self.messages)
        }
    
    def __repr__(self) -> str:
        return f"<{self.agent_name} state={self.state.value} task={self.task.description[:50]}>"
