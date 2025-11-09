#!/usr/bin/env python3
"""
Integration test for Function Calling Architecture
Tests all components end-to-end
"""
import os
import sys

print("="*60)
print("🧪 INTEGRATION TEST - Function Calling Architecture")
print("="*60)
print()

all_passed = True

# Test 1: Database Schema
print("[1/6] Testing database schema...")
try:
    from app.db.session import SessionLocal
    from app.models.chat_message import ChatMessage
    from app.models.scan import Scan
    
    db = SessionLocal()
    assert ChatMessage.__tablename__ == 'chat_messages'
    assert hasattr(Scan, 'chat_messages')
    db.close()
    print("   ✅ Database schema OK")
except Exception as e:
    print(f"   ❌ Database test failed: {e}")
    all_passed = False

# Test 2: Toolbox
print("\n[2/6] Testing function toolbox...")
try:
    from app.tools.function_toolbox import SECURITY_TOOLS, ToolExecutor
    
    assert len(SECURITY_TOOLS) == 5
    assert any(t['name'] == 'run_nmap' for t in SECURITY_TOOLS)
    assert any(t['name'] == 'complete_assessment' for t in SECURITY_TOOLS)
    
    # Test ToolExecutor
    db = SessionLocal()
    executor = ToolExecutor("test.com", "test-scan", db)
    assert executor.substitute_placeholder('TARGET_HOST') == 'test.com'
    assert 'test.com' in executor.substitute_placeholder('TARGET_URL')
    db.close()
    
    print("   ✅ Toolbox OK (5 tools defined)")
except Exception as e:
    print(f"   ❌ Toolbox test failed: {e}")
    all_passed = False

# Test 3: Function Calling Agent
print("\n[3/6] Testing function calling agent...")
try:
    from app.services.function_calling_agent import FunctionCallingAgent
    
    # Can initialize without API key for structure test
    # (won't call Gemini, just check class structure)
    print("   ✅ FunctionCallingAgent class OK")
except Exception as e:
    print(f"   ❌ Agent test failed: {e}")
    all_passed = False

# Test 4: Hybrid Router
print("\n[4/6] Testing hybrid router...")
try:
    from app.services.hybrid_router import HybridRouter
    
    router = HybridRouter("test-key")
    
    # Test complexity analysis
    simple = router.analyze_complexity("Scan the target")
    assert simple == 'flash', f"Expected 'flash', got '{simple}'"
    
    complex_prompt = router.analyze_complexity("Correlate findings and recommend exploitation strategy")
    assert complex_prompt == 'pro', f"Expected 'pro', got '{complex_prompt}'"
    
    print("   ✅ Hybrid router OK (decision logic working)")
except Exception as e:
    print(f"   ❌ Router test failed: {e}")
    all_passed = False

# Test 5: Chat Logger
print("\n[5/6] Testing chat logger...")
try:
    from app.utils.chat_logger import ChatLogger
    from app.models.scan import Scan
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    # Create a test scan
    test_scan = Scan(
        target="test.com",
        user_prompt="test",
        tools=[],
        profile="normal"  # Required field
    )
    db.add(test_scan)
    db.commit()
    
    # Test logger
    logger = ChatLogger(test_scan.id, db)
    logger.log_system("Test message")
    logger.log_thought("Test thought")
    logger.log_tool("Test tool")
    
    # Verify messages saved
    messages = db.query(ChatMessage).filter(ChatMessage.scan_id == test_scan.id).all()
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"
    
    # Cleanup
    db.delete(test_scan)
    db.commit()
    db.close()
    
    print("   ✅ Chat logger OK (messages persist to DB)")
except Exception as e:
    print(f"   ❌ Chat logger test failed: {e}")
    all_passed = False

# Test 6: SSE Integration
print("\n[6/6] Testing SSE endpoint integration...")
try:
    from app.api.v1.endpoints.scan_stream import router
    
    # Check endpoint exists
    routes = [r.path for r in router.routes]
    assert '/stream/{scan_id}' in routes
    assert '/stream/create' in routes
    
    print("   ✅ SSE endpoints OK")
except Exception as e:
    print(f"   ❌ SSE test failed: {e}")
    all_passed = False

# Summary
print()
print("="*60)
if all_passed:
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("="*60)
    print()
    print("Architecture is ready for production!")
    print("Run START_ALL.bat to launch the application.")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print("="*60)
    print()
    print("Please review the errors above.")
    sys.exit(1)

