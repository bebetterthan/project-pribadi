"""
Verification Script for Dual-Model + FFUF/SQLMAP System

Tests all new components without actually running scans.
"""
import sys
import asyncio

def test_imports():
    """Test that all new modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from app.core.model_selector import ModelSelector, DecisionContext, EscalationTrigger
        print("✅ ModelSelector imported")
        
        from app.core.pro_analyzer import ProStrategicAnalyzer
        print("✅ ProStrategicAnalyzer imported")
        
        from app.core.escalation_handler import EscalationHandler
        print("✅ EscalationHandler imported")
        
        from app.tools.sqlmap_tool import SqlmapTool
        print("✅ SqlmapTool imported")
        
        from app.tools.ffuf_tool import FfufTool
        print("✅ FfufTool imported")
        
        from app.core.performance_monitor import performance_monitor
        print("✅ PerformanceMonitor imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_selector():
    """Test ModelSelector logic"""
    print("\n🔍 Testing ModelSelector...")
    
    try:
        from app.core.model_selector import ModelSelector, DecisionContext
        
        selector = ModelSelector()
        
        # Test tactical decision (should use Flash)
        model, reason = selector.select_model(DecisionContext.TOOL_SELECTION)
        assert model.value == "flash-2.5", f"Expected Flash for tool selection, got {model.value}"
        print(f"✅ Tactical decision → {model.value}")
        
        # Test strategic decision (should use Pro)
        model, reason = selector.select_model(DecisionContext.CRITICAL_FINDING, severity='critical')
        assert model.value == "pro-2.5", f"Expected Pro for critical finding, got {model.value}"
        print(f"✅ Strategic decision → {model.value}")
        
        # Test aggressive tool (should escalate to Pro)
        model, reason = selector.select_model(DecisionContext.TOOL_SELECTION, tool_name='sqlmap')
        assert model.value == "pro-2.5", f"Expected Pro for SQLMAP, got {model.value}"
        print(f"✅ Aggressive tool → {model.value}")
        
        # Check statistics
        stats = selector.get_statistics()
        print(f"✅ Statistics: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ ModelSelector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_escalation_trigger():
    """Test escalation trigger logic"""
    print("\n🔍 Testing EscalationTrigger...")
    
    try:
        from app.core.model_selector import EscalationTrigger, DecisionContext
        
        # Test critical finding trigger
        should_escalate, reason = EscalationTrigger.should_escalate(
            context=DecisionContext.TOOL_SELECTION,
            finding_severity='critical'
        )
        assert should_escalate, "Expected escalation for critical finding"
        print(f"✅ Critical finding triggers escalation: {reason}")
        
        # Test aggressive tool trigger
        should_escalate, reason = EscalationTrigger.should_escalate(
            context=DecisionContext.FUNCTION_CALL,
            tool_name='sqlmap'
        )
        assert should_escalate, "Expected escalation for SQLMAP"
        print(f"✅ SQLMAP triggers escalation: {reason}")
        
        # Test anomaly trigger
        should_escalate, reason = EscalationTrigger.should_escalate(
            context=DecisionContext.TOOL_SELECTION,
            findings_count=1000
        )
        assert should_escalate, "Expected escalation for high findings count"
        print(f"✅ Anomaly triggers escalation: {reason}")
        
        # Test routine decision (should NOT escalate)
        should_escalate, reason = EscalationTrigger.should_escalate(
            context=DecisionContext.TOOL_SELECTION
        )
        assert not should_escalate, "Expected NO escalation for routine decision"
        print(f"✅ Routine decision does NOT escalate: {reason}")
        
        return True
    except Exception as e:
        print(f"❌ EscalationTrigger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sqlmap_tool():
    """Test SQLMAP tool wrapper"""
    print("\n🔍 Testing SqlmapTool...")
    
    try:
        from app.tools.sqlmap_tool import SqlmapTool
        
        tool = SqlmapTool()
        print(f"✅ SqlmapTool initialized")
        print(f"   Verification Tool: {tool.is_verification_tool}")
        print(f"   Requires Authorization: {tool.requires_authorization}")
        print(f"   Timeout: {tool.timeout}s")
        
        # Test command building
        cmd = tool.build_command(
            target_url="https://example.com/page?id=1",
            parameter="id",
            level=1,
            risk=1
        )
        print(f"✅ Command built: {' '.join(cmd[:5])}...")
        
        # Verify safety constraints
        assert '--batch' in cmd, "Missing --batch flag"
        assert '--dbs' in cmd, "Missing database enumeration"
        assert '--dump' not in cmd and '--dump-all' not in cmd, "DANGER: Data exfiltration flags present!"
        print(f"✅ Safety constraints verified")
        
        return True
    except Exception as e:
        print(f"❌ SqlmapTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ffuf_tool():
    """Test FFUF tool wrapper"""
    print("\n🔍 Testing FfufTool...")
    
    try:
        from app.tools.ffuf_tool import FfufTool
        
        tool = FfufTool()
        print(f"✅ FfufTool initialized")
        print(f"   Timeout: {tool.timeout}s")
        
        # Test command building
        cmd = tool.build_command(
            target="https://example.com/FUZZ",
            profile="normal"
        )
        print(f"✅ Command built: {' '.join(cmd[:5])}...")
        
        # Verify FUZZ placeholder
        assert any('FUZZ' in str(arg) for arg in cmd), "Missing FUZZ placeholder"
        print(f"✅ FUZZ placeholder verified")
        
        return True
    except Exception as e:
        print(f"❌ FfufTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_function_toolbox_sqlmap():
    """Test SQLMAP integration in function toolbox"""
    print("\n🔍 Testing function toolbox SQLMAP integration...")
    
    try:
        from app.tools.function_toolbox import create_security_tools
        
        tools = create_security_tools()
        function_declarations = tools[0].function_declarations
        
        # Find run_sqlmap
        sqlmap_func = None
        for func in function_declarations:
            if func.name == 'run_sqlmap':
                sqlmap_func = func
                break
        
        assert sqlmap_func is not None, "run_sqlmap function not found!"
        print(f"✅ run_sqlmap function registered")
        print(f"   Description: {sqlmap_func.description[:80]}...")
        
        # Verify it's marked as aggressive
        assert '⚠️' in sqlmap_func.description or 'AGGRESSIVE' in sqlmap_func.description, "Not marked as aggressive!"
        print(f"✅ Marked as AGGRESSIVE tool")
        
        return True
    except Exception as e:
        print(f"❌ Function toolbox test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("=" * 70)
    print("🎯 DUAL-MODEL + FFUF/SQLMAP SYSTEM VERIFICATION")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("ModelSelector", test_model_selector()))
    results.append(("EscalationTrigger", test_escalation_trigger()))
    results.append(("SqlmapTool", test_sqlmap_tool()))
    results.append(("FfufTool", test_ffuf_tool()))
    results.append(("Function Toolbox", test_function_toolbox_sqlmap()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n📋 IMPLEMENTED FEATURES:")
        print("   ✅ Dual-Model Architecture (Flash + Pro)")
        print("   ✅ Smart Escalation System")
        print("   ✅ Pro Strategic Analyzer")
        print("   ✅ SQLMAP Integration (with Pro approval)")
        print("   ✅ FFUF Integration")
        print("   ✅ Model Selector & Cost Tracking")
        print("   ✅ Performance Monitoring")
        print("\n🚀 System ready for production testing!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

