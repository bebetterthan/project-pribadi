"""
Main Orchestrator
Coordinates multiple agents for security testing workflow
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid

from app.strix.agents.base import BaseAgent, AgentTask, AgentResult, AgentState, AgentType
from app.strix.communication import get_message_queue, Message, MessageType
from app.strix.shared_context import get_shared_context
from .task_queue import TaskQueue, Task, TaskPriority, TaskStatus
from .result_aggregator import ResultAggregator, AgentResult as AggregatedResult


@dataclass
class WorkflowConfig:
    """Configuration for security testing workflow"""
    target: str
    workflow_type: str = "full_scan"  # full_scan, quick_scan, custom
    enabled_phases: List[str] = field(default_factory=lambda: [
        "reconnaissance",
        "enumeration",
        "vulnerability_scan"
    ])
    max_concurrent_agents: int = 3
    timeout_seconds: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """
    Main orchestrator for multi-agent security testing
    
    Responsibilities:
    - Create and manage agents
    - Distribute tasks via queue
    - Collect and aggregate results
    - Monitor overall workflow progress
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize orchestrator
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        self.workflow_id = str(uuid.uuid4())
        
        # Components
        self.task_queue = TaskQueue()
        self.result_aggregator = ResultAggregator()
        self.message_queue = get_message_queue()
        self.shared_context = get_shared_context()
        
        # Agent management
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_states: Dict[str, AgentState] = {}
        
        # Workflow state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Callbacks
        self.on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_complete: Optional[Callable[[Dict[str, Any]], None]] = None
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register agent with orchestrator
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        self.agent_states[agent.agent_id] = agent.state
    
    def create_workflow_tasks(self) -> List[Task]:
        """
        Create tasks based on workflow configuration
        
        Returns:
            List of tasks to execute
        """
        tasks = []
        
        # Phase 1: Reconnaissance
        if "reconnaissance" in self.config.enabled_phases:
            recon_task = Task(
                task_id=f"{self.workflow_id}_recon_1",
                task_type="reconnaissance",
                target=self.config.target,
                parameters={"tools": ["subfinder"]},
                priority=TaskPriority.HIGH
            )
            tasks.append(recon_task)
        
        # Phase 2: Enumeration (depends on reconnaissance)
        if "enumeration" in self.config.enabled_phases:
            enum_task = Task(
                task_id=f"{self.workflow_id}_enum_1",
                task_type="enumeration",
                target=self.config.target,
                parameters={"tools": ["nmap"]},
                priority=TaskPriority.NORMAL,
                depends_on=[f"{self.workflow_id}_recon_1"] if "reconnaissance" in self.config.enabled_phases else []
            )
            tasks.append(enum_task)
        
        # Phase 3: Vulnerability Scanning (depends on enumeration)
        if "vulnerability_scan" in self.config.enabled_phases:
            vuln_task = Task(
                task_id=f"{self.workflow_id}_vuln_1",
                task_type="vulnerability_scan",
                target=self.config.target,
                parameters={"tools": ["nuclei"]},
                priority=TaskPriority.HIGH,
                depends_on=[f"{self.workflow_id}_enum_1"] if "enumeration" in self.config.enabled_phases else []
            )
            tasks.append(vuln_task)
        
        return tasks
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute complete security testing workflow
        
        Returns:
            Workflow results
        """
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        try:
            # Create and queue tasks
            tasks = self.create_workflow_tasks()
            for task in tasks:
                self.task_queue.add_task(task)
            
            print(f"[ORCHESTRATOR] Created {len(tasks)} tasks for workflow {self.workflow_id}")
            
            # Process tasks
            await self._process_tasks()
            
            # Generate final report
            report = self.result_aggregator.generate_report()
            
            # Add workflow metadata
            report["workflow"] = {
                "workflow_id": self.workflow_id,
                "target": self.config.target,
                "workflow_type": self.config.workflow_type,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (
                    (self.end_time - self.start_time).total_seconds()
                    if self.end_time else None
                )
            }
            
            # Callback
            if self.on_complete:
                self.on_complete(report)
            
            return report
            
        finally:
            self.is_running = False
            self.end_time = datetime.utcnow()
    
    async def _process_tasks(self) -> None:
        """Process all tasks in queue"""
        active_tasks = []
        
        while True:
            # Check if all tasks done
            queue_stats = self.task_queue.get_stats()
            if (queue_stats["pending"] == 0 and 
                len(active_tasks) == 0 and
                queue_stats["completed"] == queue_stats["total_tasks"]):
                break
            
            # Get next task if we have capacity
            if len(active_tasks) < self.config.max_concurrent_agents:
                task = self.task_queue.get_next_task()
                
                if task:
                    # Find suitable agent
                    agent = self._find_agent_for_task(task)
                    
                    if agent:
                        # Start task execution
                        task_future = asyncio.create_task(
                            self._execute_task(agent, task)
                        )
                        active_tasks.append((task, task_future))
                        
                        print(f"[ORCHESTRATOR] Started task {task.task_id} on agent {agent.agent_id}")
            
            # Check completed tasks
            completed = []
            for task, future in active_tasks:
                if future.done():
                    completed.append((task, future))
            
            # Remove completed
            for task, future in completed:
                active_tasks.remove((task, future))
                
                # Get result
                try:
                    result = await future
                    print(f"[ORCHESTRATOR] Task {task.task_id} completed")
                except Exception as e:
                    print(f"[ORCHESTRATOR] Task {task.task_id} failed: {str(e)}")
            
            # Progress callback
            if self.on_progress:
                self.on_progress({
                    "workflow_id": self.workflow_id,
                    "queue_stats": queue_stats,
                    "active_tasks": len(active_tasks)
                })
            
            # Small delay
            await asyncio.sleep(0.5)
    
    async def _execute_task(self, agent: BaseAgent, task: Task) -> None:
        """
        Execute single task with agent
        
        Args:
            agent: Agent to execute task
            task: Task to execute
        """
        self.task_queue.mark_task_running(task.task_id, agent.agent_id)
        
        try:
            # Convert orchestrator Task to AgentTask and update agent
            agent_task = AgentTask(
                task_id=task.task_id,
                description=task.parameters.get("description", "Orchestrator task"),
                parameters=task.parameters
            )
            agent.task = agent_task
            
            # Execute (agent uses its internal task)
            start_time = datetime.utcnow()
            result = agent.execute()  # Synchronous - returns AgentResult directly
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Mark complete
            self.task_queue.mark_task_completed(task.task_id, result.data)
            
            # Add to aggregator
            agg_result = AggregatedResult(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type.value,
                task_id=task.task_id,
                data=result.data,
                execution_time_ms=execution_time
            )
            self.result_aggregator.add_result(agg_result)
            
        except Exception as e:
            self.task_queue.mark_task_failed(task.task_id, str(e))
            raise
    
    def _find_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """
        Find suitable agent for task
        
        Args:
            task: Task to match
            
        Returns:
            Matching agent or None
        """
        # Map task types to agent types
        task_to_agent = {
            "reconnaissance": AgentType.RECON,
            "enumeration": AgentType.VULN,  # Use VULN instead of VALIDATION
            "vulnerability_scan": AgentType.VULN  # Use VULN instead of VULNERABILITY
        }
        
        required_type = task_to_agent.get(task.task_type)
        if not required_type:
            return None
        
        # Find available agent of right type
        for agent in self.agents.values():
            if (agent.agent_type == required_type and 
                agent.state == AgentState.IDLE):
                return agent
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "workflow_id": self.workflow_id,
            "target": self.config.target,
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "agents": {
                agent_id: {
                    "type": agent.agent_type.value,
                    "state": agent.state.value
                }
                for agent_id, agent in self.agents.items()
            },
            "queue": self.task_queue.get_stats(),
            "results": self.result_aggregator.get_stats()
        }
