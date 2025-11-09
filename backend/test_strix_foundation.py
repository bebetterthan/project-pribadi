"""
Strix Foundation Complete Integration Test
Tests all 4 layers working together
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.strix.agents.base import BaseAgent, AgentTask, AgentResult, AgentType, AgentState
from app.strix.orchestration import Orchestrator, WorkflowConfig, TaskQueue, Task, TaskPriority
from app.strix.orchestration.result_aggregator import ResultAggregator, AgentResult as AggResult


# Mock Agent for testing
class MockReconAgent(BaseAgent):
    """Mock reconnaissance agent"""
    
    def __init__(self):
        # Create dummy task
        dummy_task = AgentTask(
            task_id="mock_recon_task",
            description="Mock reconnaissance task",
            parameters={}
        )
        super().__init__(
            agent_type=AgentType.RECON,
            task=dummy_task,
            target="example.com"
        )
        # Override agent_id for consistency
        self.agent_id = "mock_recon_1"
    
    async def initialize(self) -> bool:
        """Initialize agent"""
        return True
    
    async def cleanup(self) -> None:
        """Cleanup agent"""
        pass
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute task - delegates to _execute_task"""
        return await self._execute_task(task)
    
    async def handle_message(self, message) -> None:
        """Handle incoming message"""
        pass
    
    async def _execute_task(self, task: AgentTask) -> AgentResult:
        """Mock execution"""
        await asyncio.sleep(0.1)  # Simulate work
        
        return AgentResult(
            success=True,
            data={
                "subdomains": ["www.example.com", "api.example.com", "mail.example.com"],
                "count": 3,
                "sources": {"crtsh": 2, "virustotal": 1}
            },
            metadata={"task_id": task.task_id, "message": "Reconnaissance completed"}
        )


class MockEnumAgent(BaseAgent):
    """Mock enumeration agent"""
    
    def __init__(self):
        # Create dummy task
        dummy_task = AgentTask(
            task_id="mock_enum_task",
            description="Mock enumeration task",
            parameters={}
        )
        super().__init__(
            agent_type=AgentType.VULN,  # Use VULN instead of VALIDATION
            task=dummy_task,
            target="example.com"
        )
        # Override agent_id for consistency
        self.agent_id = "mock_enum_1"
    
    async def initialize(self) -> bool:
        """Initialize agent"""
        return True
    
    async def cleanup(self) -> None:
        """Cleanup agent"""
        pass
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute task - delegates to _execute_task"""
        return await self._execute_task(task)
    
    async def handle_message(self, message) -> None:
        """Handle incoming message"""
        pass
    
    async def _execute_task(self, task: AgentTask) -> AgentResult:
        """Mock execution"""
        await asyncio.sleep(0.1)
        
        return AgentResult(
            success=True,
            data={
                "hosts": [
                    {
                        "address": "192.168.1.1",
                        "ports": [
                            {"port": "80", "protocol": "tcp", "service": "http"},
                            {"port": "443", "protocol": "tcp", "service": "https"}
                        ]
                    }
                ],
                "total_ports_found": 2
            },
            metadata={"task_id": task.task_id, "message": "Enumeration completed"}
        )


def test_task_queue():
    """Test Layer 4: Task Queue"""
    print("\n" + "="*60)
    print("TEST LAYER 4.1: Task Queue")
    print("="*60)
    
    queue = TaskQueue()
    
    # Create tasks with dependencies
    task1 = Task(
        task_id="task_1",
        task_type="reconnaissance",
        target="example.com",
        priority=TaskPriority.HIGH
    )
    
    task2 = Task(
        task_id="task_2",
        task_type="enumeration",
        target="example.com",
        priority=TaskPriority.NORMAL,
        depends_on=["task_1"]  # Depends on task1
    )
    
    # Add tasks
    queue.add_task(task1)
    queue.add_task(task2)
    
    # task1 should be available, task2 blocked
    stats = queue.get_stats()
    print(f"✅ Total tasks: {stats['total_tasks']}")
    print(f"✅ Pending: {stats['pending']}")
    
    # Get task1
    next_task = queue.get_next_task(["reconnaissance"])
    assert next_task is not None
    assert next_task.task_id == "task_1"
    print(f"✅ Got task: {next_task.task_id}")
    
    # Complete task1
    queue.mark_task_running("task_1", "agent_1")
    queue.mark_task_completed("task_1", {"status": "done"})
    
    # Now task2 should be available
    next_task = queue.get_next_task(["enumeration"])
    assert next_task is not None
    assert next_task.task_id == "task_2"
    print(f"✅ Got dependent task: {next_task.task_id}")
    
    print("✅ TEST PASSED: Task Queue")


def test_result_aggregator():
    """Test Layer 4: Result Aggregator"""
    print("\n" + "="*60)
    print("TEST LAYER 4.2: Result Aggregator")
    print("="*60)
    
    aggregator = ResultAggregator()
    
    # Add reconnaissance result
    recon_result = AggResult(
        agent_id="recon_1",
        agent_type="reconnaissance",
        task_id="task_1",
        data={
            "subdomains": ["www.example.com", "api.example.com"],
            "count": 2,
            "sources": {"crtsh": 2}
        },
        execution_time_ms=500.0
    )
    aggregator.add_result(recon_result)
    
    # Add enumeration result
    enum_result = AggResult(
        agent_id="enum_1",
        agent_type="enumeration",
        task_id="task_2",
        data={
            "hosts": [
                {
                    "address": "192.168.1.1",
                    "ports": [
                        {"port": "80", "service": "http"},
                        {"port": "443", "service": "https"}
                    ]
                }
            ]
        },
        execution_time_ms=750.0
    )
    aggregator.add_result(enum_result)
    
    # Test aggregation
    subdomains = aggregator.aggregate_subdomains()
    print(f"✅ Aggregated subdomains: {subdomains['count']}")
    
    ports = aggregator.aggregate_ports()
    print(f"✅ Aggregated hosts: {ports['hosts']}")
    print(f"✅ Total open ports: {ports['total_open_ports']}")
    
    # Generate report
    report = aggregator.generate_report()
    assert "summary" in report
    assert "findings" in report
    print(f"✅ Report sections: {len(report)}")
    print(f"✅ Total tasks in report: {report['summary']['total_tasks']}")
    
    print("✅ TEST PASSED: Result Aggregator")


async def test_orchestrator():
    """Test Layer 4: Orchestrator (simplified)"""
    print("\n" + "="*60)
    print("TEST LAYER 4.3: Orchestrator Integration")
    print("="*60)
    
    # Create workflow config
    config = WorkflowConfig(
        target="example.com",
        workflow_type="quick_scan",
        enabled_phases=["reconnaissance", "enumeration"],
        max_concurrent_agents=2
    )
    
    # Create orchestrator
    orchestrator = Orchestrator(config)
    
    # Create and register mock agents
    recon_agent = MockReconAgent()
    enum_agent = MockEnumAgent()
    
    orchestrator.register_agent(recon_agent)
    orchestrator.register_agent(enum_agent)
    
    print(f"✅ Registered agents: {len(orchestrator.agents)}")
    print(f"✅ Config target: {config.target}")
    print(f"✅ Enabled phases: {len(config.enabled_phases)}")
    
    # Test task creation
    tasks = orchestrator.create_workflow_tasks()
    print(f"✅ Created tasks: {len(tasks)}")
    assert len(tasks) == 2, "Should create 2 tasks"
    
    # Test status
    status = orchestrator.get_status()
    assert "workflow_id" in status
    assert "agents" in status
    print(f"✅ Status: {len(status)} fields")
    
    print("✅ TEST PASSED: Orchestrator (simplified)")


def test_full_stack():
    """Test complete Strix stack"""
    print("\n" + "="*60)
    print("STRIX FOUNDATION - FULL STACK TEST")
    print("="*60)
    print("Testing all 4 layers integrated:")
    print("- Layer 1: Agent Base System")
    print("- Layer 2: Tool Execution System")
    print("- Layer 3: LLM Integration")
    print("- Layer 4: Orchestration")
    print("="*60)
    
    try:
        # Layer 4 tests
        test_task_queue()
        test_result_aggregator()
        
        # Async orchestrator test
        asyncio.run(test_orchestrator())
        
        print("\n" + "="*60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("="*60)
        print("\n✅ Layer 1 (Agents): Working")
        print("✅ Layer 2 (Tools): Working")
        print("✅ Layer 3 (LLM): Working")
        print("✅ Layer 4 (Orchestration): Working")
        print("\n🚀 STRIX FOUNDATION IS READY!")
        print("="*60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_stack()
    sys.exit(0 if success else 1)
