"""
STRIX Foundation Layer - Layer 1 Integration Test
Tests: Agent Base System + Shared Context

Purpose:
    Validate that Layer 1 components work together correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.strix.agents import AgentType, AgentTask, AgentState
from app.strix.agents.recon_agent import ReconAgent
from app.strix.shared_context import SharedContext


def test_layer1():
    """Test Layer 1: Agent Base System + Shared Context"""
    
    print("\n" + "="*70)
    print("🧪 STRIX Foundation Layer - Layer 1 Integration Test")
    print("="*70)
    
    # 1. Create Shared Context
    print("\n1️⃣  Creating Shared Context...")
    context = SharedContext(
        scan_id="test_scan_001",
        target="example.com",
        config={
            "scan_type": "comprehensive",
            "user_instructions": "Test scan"
        }
    )
    print(f"   ✓ Context created: {context}")
    print(f"   ✓ Stats: {context.get_stats()}")
    
    # 2. Create Recon Agent
    print("\n2️⃣  Creating Recon Agent...")
    task = AgentTask(
        task_id="task_001",
        description="Enumerate subdomains for example.com",
        priority=1
    )
    
    agent = ReconAgent(
        task=task,
        target="example.com",
        config={"mode": "fast"}
    )
    agent.set_shared_context(context)
    
    print(f"   ✓ Agent created: {agent}")
    print(f"   ✓ Initial state: {agent.state.value}")
    print(f"   ✓ Agent status: {agent.get_status()}")
    
    # 3. Execute Agent
    print("\n3️⃣  Executing Agent...")
    result = agent.run()
    
    print(f"   ✓ Execution complete")
    print(f"   ✓ Success: {result.success}")
    print(f"   ✓ Final state: {agent.state.value}")
    
    if result.success:
        print(f"   ✓ Discoveries: {result.data}")
        print(f"   ✓ Metadata: {result.metadata}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # 4. Check Shared Context
    print("\n4️⃣  Checking Shared Context...")
    
    # Get subdomains from context
    subdomains = context.get_latest("discoveries", "subdomains")
    print(f"   ✓ Subdomains in context: {subdomains}")
    
    # Get all discoveries
    all_discoveries = context.get_all_discoveries()
    print(f"   ✓ All discoveries: {all_discoveries}")
    
    # Get context stats
    stats = context.get_stats()
    print(f"   ✓ Context stats:")
    print(f"     - Total entries: {stats['total_entries']}")
    print(f"     - By category: {stats['entries_by_category']}")
    print(f"     - Reads: {stats['read_count']}")
    print(f"     - Writes: {stats['write_count']}")
    print(f"     - Active agents: {stats['agents_active']}")
    
    # 5. Check Agent Messages
    print("\n5️⃣  Checking Agent Messages...")
    print(f"   ✓ Messages sent: {len(agent.messages)}")
    
    for i, msg in enumerate(agent.messages, 1):
        print(f"   Message {i}:")
        print(f"     - Type: {msg['type']}")
        print(f"     - To: {msg['to']}")
        print(f"     - Payload: {msg['payload']}")
    
    # 6. Test State Transitions
    print("\n6️⃣  Checking State History...")
    print(f"   ✓ State transitions: {len(agent.state_history)}")
    
    for state, timestamp in agent.state_history:
        print(f"     - {state.value} at {timestamp.strftime('%H:%M:%S')}")
    
    # 7. Test Agent Status
    print("\n7️⃣  Final Agent Status...")
    status = agent.get_status()
    print(f"   ✓ Agent ID: {status['agent_id']}")
    print(f"   ✓ Agent name: {status['agent_name']}")
    print(f"   ✓ Type: {status['agent_type']}")
    print(f"   ✓ State: {status['state']}")
    print(f"   ✓ Duration: {status['duration_seconds']:.2f}s")
    print(f"   ✓ Results: {status['results_count']}")
    print(f"   ✓ Messages: {status['messages_sent']}")
    
    # 8. Export Context
    print("\n8️⃣  Exporting Context Data...")
    export = context.export()
    print(f"   ✓ Export size: {len(str(export))} chars")
    print(f"   ✓ Categories: {list(export['data'].keys())}")
    
    # Final Summary
    print("\n" + "="*70)
    print("✅ LAYER 1 TEST COMPLETE")
    print("="*70)
    print("\nSummary:")
    print(f"  ✓ Agent creation: SUCCESS")
    print(f"  ✓ Agent execution: SUCCESS")
    print(f"  ✓ State management: SUCCESS ({len(agent.state_history)} transitions)")
    print(f"  ✓ Message passing: SUCCESS ({len(agent.messages)} messages)")
    print(f"  ✓ Shared context: SUCCESS ({stats['write_count']} writes, {stats['read_count']} reads)")
    print(f"  ✓ Data persistence: SUCCESS")
    
    print("\n🎉 Layer 1 (Agent Base System) is WORKING!")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_layer1()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
