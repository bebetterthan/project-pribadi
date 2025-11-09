#!/usr/bin/env python3
"""
Test Tool Health Checker
Verify all pentesting tools are accessible
"""
import sys

print("=" * 70)
print("🔍 TESTING TOOL HEALTH CHECKER")
print("=" * 70)
print()

try:
    from app.services.tool_health_checker import ToolHealthChecker
    
    # Check all tools
    results = ToolHealthChecker.check_all_tools()
    
    print("\n" + "=" * 70)
    print("📊 DETAILED RESULTS:")
    print("=" * 70)
    
    all_healthy = True
    for tool_name, status in results.items():
        print(f"\n🛠️  {tool_name.upper()}:")
        print(f"   Status: {status.health_status}")
        print(f"   Installed: {status.is_installed}")
        if status.is_installed:
            print(f"   Version: {status.version}")
            print(f"   Path: {status.install_path}")
        if status.error_message:
            print(f"   ⚠️ Warning: {status.error_message}")
        
        if status.health_status != "healthy":
            all_healthy = False
    
    print("\n" + "=" * 70)
    if all_healthy:
        print("✅ ALL TOOLS HEALTHY - Ready for Fase 3!")
    else:
        print("⚠️ SOME TOOLS HAVE ISSUES - But can proceed with available tools")
    print("=" * 70)
    
    # Get summary for health endpoint
    summary = ToolHealthChecker.get_health_summary()
    print(f"\n🏥 Overall Status: {summary['overall_status'].upper()}")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

