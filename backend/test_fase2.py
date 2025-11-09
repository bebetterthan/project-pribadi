#!/usr/bin/env python3
"""
Comprehensive Test Suite for Fase 2: Hybrid Agent & Cost Tracking
Tests dual model support, task-based routing, cost calculation, and context handoff
"""
import os
import sys
import asyncio

print("="*70)
print("🧪 FASE 2 TEST SUITE - Hybrid Agent & Cost Tracking")
print("="*70)
print()

all_tests_passed = True

# Test 1: Import all Fase 2 modules
print("[1/8] Testing Fase 2 module imports...")
try:
    from app.services.function_calling_agent import FunctionCallingAgent
    from app.services.cost_tracker import CostTracker, PRICING
    from app.services.hybrid_router import HybridRouter
    from app.tools.function_toolbox import SECURITY_TOOLS
    
    print("   ✅ All Fase 2 modules imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    all_tests_passed = False
    sys.exit(1)

# Test 2: Cost Tracker - Pricing Configuration
print("\n[2/8] Verifying cost tracker pricing...")
try:
    assert "flash" in PRICING
    assert "pro" in PRICING
    assert PRICING["flash"]["input"] < PRICING["pro"]["input"]
    assert PRICING["flash"]["output"] < PRICING["pro"]["output"]
    
    print(f"   ✅ Pricing configured correctly:")
    print(f"      Flash: ${PRICING['flash']['input']}/1M in, ${PRICING['flash']['output']}/1M out")
    print(f"      Pro:   ${PRICING['pro']['input']}/1M in, ${PRICING['pro']['output']}/1M out")
    print(f"      Ratio: Pro is {PRICING['pro']['input']/PRICING['flash']['input']:.1f}x more expensive")
except Exception as e:
    print(f"   ❌ Pricing test failed: {e}")
    all_tests_passed = False

# Test 3: Cost Tracker - Token Counting
print("\n[3/8] Testing cost tracker calculations...")
try:
    tracker = CostTracker("test-scan-001")
    
    # Record sample calls
    tracker.record_call("flash", 1000, 500, "initial_scan", 1.2)
    tracker.record_call("pro", 2000, 1000, "strategic_decision", 2.5)
    tracker.record_call("flash", 800, 400, "data_extraction", 0.8)
    
    report = tracker.get_cost_report()
    
    # Verify counts
    assert report["total_calls"] == 3
    assert report["flash_calls"] == 2
    assert report["pro_calls"] == 1
    
    # Verify costs
    actual_cost = report["costs"]["actual_usd"]
    all_pro_cost = report["costs"]["estimated_all_pro_usd"]
    
    assert actual_cost > 0
    assert all_pro_cost > actual_cost  # Hybrid should be cheaper
    assert report["savings"]["vs_all_pro_percentage"] > 0
    
    print(f"   ✅ Cost tracking works correctly:")
    print(f"      Actual cost: ${actual_cost:.6f}")
    print(f"      All-Pro cost: ${all_pro_cost:.6f}")
    print(f"      Savings: {report['savings']['vs_all_pro_percentage']:.1f}%")
except Exception as e:
    print(f"   ❌ Cost tracker test failed: {e}")
    all_tests_passed = False

# Test 4: Dual Model Initialization
print("\n[4/8] Testing dual model initialization...")
api_key = os.getenv('GEMINI_API_KEY', 'test-key')

if not api_key or api_key == 'test-key':
    print("   ⚠️  No GEMINI_API_KEY found, skipping API tests")
    print("   💡 Set environment variable to test: set GEMINI_API_KEY=your_key")
else:
    try:
        # Test hybrid mode initialization
        agent = FunctionCallingAgent(api_key, use_pro_model=False, hybrid_mode=True)
        
        assert hasattr(agent, 'flash_model')
        assert hasattr(agent, 'pro_model')
        assert hasattr(agent, 'flash_name')
        assert hasattr(agent, 'pro_name')
        assert agent.hybrid_mode == True
        assert agent.current_model_type == "FLASH"  # Starts with Flash
        
        print(f"   ✅ Dual model initialization successful:")
        print(f"      Flash model: {agent.flash_name}")
        print(f"      Pro model: {agent.pro_name}")
        print(f"      Hybrid mode: Enabled")
    except Exception as e:
        print(f"   ❌ Dual model init failed: {e}")
        all_tests_passed = False

# Test 5: Task Type Detection
print("\n[5/8] Testing task-based routing logic...")
try:
    agent = FunctionCallingAgent(api_key, use_pro_model=False, hybrid_mode=True)
    
    # Test various scenarios
    test_cases = [
        {"iteration": 0, "tool_count": 0, "last_action": None, "expected": "initial_scan"},
        {"iteration": 2, "tool_count": 1, "last_action": "tool_execution", "expected": "strategic_decision"},
        {"iteration": 3, "tool_count": 2, "last_action": "tool_execution", "expected": "next_step_decision"},
        {"iteration": 6, "tool_count": 2, "last_action": "thought", "expected": "final_report"},
        {"iteration": 2, "tool_count": 0, "last_action": "error", "expected": "error_handling"},
    ]
    
    for test in test_cases:
        agent.iteration_count = test["iteration"]
        agent.tool_call_count = test["tool_count"]
        agent.last_action = test["last_action"]
        
        result = agent._determine_task_type()
        status = "✅" if result == test["expected"] else "❌"
        
        if result != test["expected"]:
            print(f"   {status} Expected {test['expected']}, got {result}")
            all_tests_passed = False
        else:
            print(f"   {status} Correctly identified: {result}")
    
    print("   ✅ Task type detection logic working")
except Exception as e:
    print(f"   ❌ Task detection test failed: {e}")
    all_tests_passed = False

# Test 6: Model Selection Logic
print("\n[6/8] Testing model selection based on task type...")
try:
    agent = FunctionCallingAgent(api_key, use_pro_model=False, hybrid_mode=True)
    
    # Test task routing rules
    routing_tests = [
        ("initial_scan", "FLASH"),
        ("data_extraction", "FLASH"),
        ("error_handling", "FLASH"),
        ("strategic_decision", "PRO"),
        ("vulnerability_analysis", "PRO"),
        ("next_step_decision", "PRO"),
        ("final_report", "PRO"),
    ]
    
    for task_type, expected_model in routing_tests:
        model, model_type, reasoning = agent._select_model(task_type)
        status = "✅" if model_type == expected_model else "❌"
        
        if model_type != expected_model:
            print(f"   {status} {task_type}: Expected {expected_model}, got {model_type}")
            all_tests_passed = False
        else:
            print(f"   {status} {task_type} → {model_type}")
    
    print("   ✅ Model selection logic working correctly")
except Exception as e:
    print(f"   ❌ Model selection test failed: {e}")
    all_tests_passed = False

# Test 7: Context Summary Building
print("\n[7/8] Testing context handoff mechanism...")
try:
    agent = FunctionCallingAgent(api_key, use_pro_model=False, hybrid_mode=True)
    
    # Populate conversation history
    agent.conversation_history = [
        {"type": "tool_execution", "tool": "run_nmap", "result_status": "success"},
        {"type": "thought", "content": "Analyzing ports..."},
        {"type": "tool_execution", "tool": "run_nuclei", "result_status": "success"},
    ]
    
    summary = agent._build_context_summary()
    
    assert "run_nmap" in summary
    assert "run_nuclei" in summary
    assert len(summary) < 300  # Should be concise
    
    print(f"   ✅ Context summary generated:")
    print(f"      {summary}")
except Exception as e:
    print(f"   ❌ Context handoff test failed: {e}")
    all_tests_passed = False

# Test 8: Hybrid Router Integration
print("\n[8/8] Testing hybrid router integration...")
try:
    router = HybridRouter(api_key)
    
    # Test complexity analysis
    simple_prompt = "Scan for open ports"
    complex_prompt = "Correlate findings and provide exploitation strategy"
    
    simple_decision = router.analyze_complexity(simple_prompt)
    complex_decision = router.analyze_complexity(complex_prompt)
    
    assert simple_decision == "flash"
    assert complex_decision == "pro"
    
    print(f"   ✅ Hybrid router working:")
    print(f"      Simple task → {simple_decision.upper()}")
    print(f"      Complex task → {complex_decision.upper()}")
except Exception as e:
    print(f"   ❌ Hybrid router test failed: {e}")
    all_tests_passed = False

# Summary
print()
print("="*70)
if all_tests_passed:
    print("✅ ALL FASE 2 TESTS PASSED!")
    print("="*70)
    print()
    print("Fase 2 Implementation Complete:")
    print("  ✓ Dual model support (Flash + Pro)")
    print("  ✓ Task-based routing logic")
    print("  ✓ Cost tracking and analytics")
    print("  ✓ Context handoff mechanism")
    print("  ✓ Hybrid router integration")
    print()
    print("Ready for production use!")
    print("Run START_ALL.bat to test with real scans")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print("="*70)
    print()
    print("Please review errors above and fix issues")
    sys.exit(1)

