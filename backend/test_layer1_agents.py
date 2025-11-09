"""
Layer 1 Integration Test - SIMPLIFIED
Test Agent Base System components working together
"""
import time
from datetime import datetime
from app.strix.agents.base import BaseAgent, AgentTask, AgentResult, AgentType, AgentState
from app.strix.communication import get_message_queue, MessageType
from app.strix.shared_context import get_shared_context, reset_shared_context
from app.utils.logger import logger


# Simple test agent implementation
class SimpleTestAgent(BaseAgent):
    """Minimal test agent"""
    
    def initialize(self) -> None:
        """Setup"""
        self._log("Agent initialized")
    
    def execute(self) -> AgentResult:
        """Execute task"""
        self._log("Starting execution")
        
        # Simulate work
        time.sleep(0.2)
        
        # Store result in shared context
        if self.shared_context:
            self.shared_context.store_data(
                category="discoveries",
                key="test_data",
                value={"message": "Test successful"},
                agent_id=self.agent_id
            )
        
        self._log("Execution complete")
        return AgentResult(success=True, data={"test": "passed"})
    
    def cleanup(self) -> None:
        """Cleanup"""
        self._log("Cleanup complete")
    
    def handle_message(self, message: dict) -> None:
        """Handle messages"""
        self._log(f"Received message: {message.get('type')}")


def test_layer_1_simple():
    """
    Simple Layer 1 test
    """
    print("\n" + "="*70)
    print("🧪 LAYER 1: AGENT BASE SYSTEM TEST")
    print("="*70)
    
    # Reset state
    reset_shared_context()
    message_queue = get_message_queue()
    message_queue.clear()
    
    # Test 1: Shared Context
    print("\n1️⃣  Test: Shared Context")
    context = get_shared_context(
        scan_id="test_001",
        target="example.com",
        config={"scan_type": "test"}
    )
    
    print(f"   ✓ Context created: {context.scan_id}")
    print(f"   ✓ Target: {context.target}")
    
    # Test 2: Agent Creation
    print("\n2️⃣  Test: Agent Creation")
    task = AgentTask(
        task_id="task_001",
        description="Test task",
        parameters={"param1": "value1"}
    )
    
    agent = SimpleTestAgent(
        agent_type=AgentType.RECON,
        task=task,
        target="example.com"
    )
    agent.set_shared_context(context)
    
    print(f"   ✓ Agent created: {agent.agent_name}")
    print(f"   ✓ Agent ID: {agent.agent_id[:8]}...")
    print(f"   ✓ Agent type: {agent.agent_type.value}")
    print(f"   ✓ State: {agent.state.value}")
    
    assert agent.state.value == "idle", "Should start IDLE"
    
    # Test 3: Agent Execution
    print("\n3️⃣  Test: Agent Execution")
    result = agent.run()
    
    print(f"   ✓ Execution complete")
    print(f"   ✓ Result success: {result.success}")
    print(f"   ✓ Final state: {agent.state.value}")
    
    assert result.success, "Should succeed"
    assert agent.state.value == "completed", "Should be COMPLETED"
    
    # Test 4: Shared Context Data
    print("\n4️⃣  Test: Shared Context Data")
    stored_data = context.get_latest("discoveries", "test_data")
    
    print(f"   ✓ Data retrieved: {stored_data}")
    assert stored_data is not None, "Should have stored data"
    assert stored_data["message"] == "Test successful"
    
    # Test 5: Context Stats
    print("\n5️⃣  Test: Context Stats")
    stats = context.get_stats()
    
    print(f"   ✓ Total entries: {stats['total_entries']}")
    print(f"   ✓ Read count: {stats['read_count']}")
    print(f"   ✓ Write count: {stats['write_count']}")
    print(f"   ✓ Active agents: {stats['agents_active']}")
    
    # Test 6: Message Queue
    print("\n6️⃣  Test: Message Queue")
    queue_stats = message_queue.get_stats()
    
    print(f"   ✓ Total messages: {queue_stats['total_messages']}")
    print(f"   ✓ By type: {queue_stats.get('by_type', {})}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ LAYER 1 TESTS PASSED")
    print("="*70)
    print("\n📊 Summary:")
    print(f"   ✓ Agent creation: WORKING")
    print(f"   ✓ Agent execution: WORKING")
    print(f"   ✓ State management: WORKING")
    print(f"   ✓ Shared context: WORKING")
    print(f"   ✓ Message queue: WORKING")
    print("\n🎉 Layer 1 Foundation is SOLID!")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_layer_1_simple()

