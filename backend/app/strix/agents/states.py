"""
Agent State Definitions
All possible states an agent can be in during its lifecycle
"""
from enum import Enum


class AgentState(str, Enum):
    """
    Agent lifecycle states
    
    State Transitions:
    IDLE → RUNNING (task assigned)
    RUNNING → WAITING (needs something)
    WAITING → RUNNING (dependency resolved)
    RUNNING → COMPLETED (task done)
    RUNNING → ERROR (problem occurred)
    ERROR → RUNNING (retry after fix)
    """
    
    IDLE = "idle"
    """Agent created but not started yet, waiting for task assignment"""
    
    RUNNING = "running"
    """Agent actively executing task, may be waiting for tool/AI/processing"""
    
    WAITING = "waiting"
    """Agent paused, waiting for dependency/resource/input"""
    
    COMPLETED = "completed"
    """Agent finished successfully, results stored, ready for termination"""
    
    ERROR = "error"
    """Agent encountered problem, error logged, escalated to orchestrator"""


class AgentType(str, Enum):
    """
    Types of specialized agents in the system
    Each type has specific responsibilities and capabilities
    """
    
    RECON = "recon"
    """Reconnaissance agent - discovers attack surface, enumerates targets"""
    
    VALIDATION = "validation"
    """Validation agent - tests discovered assets, filters active vs inactive"""
    
    VULNERABILITY = "vulnerability"
    """Vulnerability agent - tests for security issues, exploits weaknesses"""
    
    EVIDENCE = "evidence"
    """Evidence agent - generates proof-of-concept, captures evidence"""
    
    REPORT = "report"
    """Report agent - aggregates findings, generates reports"""
    
    COORDINATOR = "coordinator"
    """Coordinator agent - manages workflow, orchestrates other agents"""


class TaskPriority(str, Enum):
    """
    Priority levels for task execution
    Determines queue processing order
    """
    
    HIGH = "high"
    """Critical findings validation, time-sensitive tests, user-requested"""
    
    NORMAL = "normal"
    """Standard workflow tasks, routine scanning"""
    
    LOW = "low"
    """Nice-to-have tests, non-essential enumeration"""
