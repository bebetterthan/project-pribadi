"""
Task Queue System
Intelligent task distribution and priority management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from queue import PriorityQueue
import threading


class TaskPriority(int, Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    Executable task
    """
    task_id: str
    task_type: str  # reconnaissance, enumeration, vulnerability_scan, etc.
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Status tracking
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Task IDs that must complete first
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "target": self.target,
            "parameters": self.parameters,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "has_result": self.result is not None,
            "has_error": self.error is not None
        }


class TaskQueue:
    """
    Priority-based task queue with dependency resolution
    """
    
    def __init__(self):
        """Initialize task queue"""
        self.pending_queue = PriorityQueue()
        self.tasks: Dict[str, Task] = {}  # All tasks by ID
        self.completed_tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
    
    def add_task(self, task: Task) -> None:
        """
        Add task to queue
        
        Args:
            task: Task to add
        """
        with self.lock:
            self.tasks[task.task_id] = task
            
            # Check if dependencies are met
            if self._dependencies_met(task):
                self.pending_queue.put(task)
            # else: task will be queued when dependencies complete
    
    def get_next_task(
        self,
        agent_capabilities: Optional[List[str]] = None
    ) -> Optional[Task]:
        """
        Get next task for execution
        
        Args:
            agent_capabilities: List of task types agent can handle
            
        Returns:
            Next task or None
        """
        with self.lock:
            # Try to find suitable task
            temp_tasks = []
            result_task = None
            
            while not self.pending_queue.empty():
                task = self.pending_queue.get()
                
                # Check if agent can handle this task
                if agent_capabilities is None or task.task_type in agent_capabilities:
                    # Check dependencies again (in case something changed)
                    if self._dependencies_met(task):
                        result_task = task
                        break
                
                # Put back if not suitable
                temp_tasks.append(task)
            
            # Put back unsuitable tasks
            for t in temp_tasks:
                self.pending_queue.put(t)
            
            # Mark task as assigned
            if result_task:
                result_task.status = TaskStatus.ASSIGNED
            
            return result_task
    
    def mark_task_running(self, task_id: str, agent_id: str) -> None:
        """Mark task as running"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.assigned_agent = agent_id
                task.started_at = datetime.utcnow()
    
    def mark_task_completed(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Mark task as completed
        
        Args:
            task_id: Task ID
            result: Task result
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                
                # Move to completed
                self.completed_tasks[task_id] = task
                
                # Check if this unblocks other tasks
                self._check_blocked_tasks(task_id)
    
    def mark_task_failed(self, task_id: str, error: str) -> None:
        """
        Mark task as failed
        
        Args:
            task_id: Task ID
            error: Error message
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error = error
    
    def _dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are met"""
        for dep_id in task.depends_on:
            if dep_id not in self.completed_tasks:
                return False
        return True
    
    def _check_blocked_tasks(self, completed_task_id: str) -> None:
        """Check and queue tasks that were blocked by this task"""
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and
                completed_task_id in task.depends_on and
                self._dependencies_met(task)):
                self.pending_queue.put(task)
    
    def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return self.pending_queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            status_counts = {}
            for task in self.tasks.values():
                status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            
            return {
                "total_tasks": len(self.tasks),
                "pending": self.pending_queue.qsize(),
                "completed": len(self.completed_tasks),
                "by_status": status_counts
            }
