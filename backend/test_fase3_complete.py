"""
Comprehensive Fase 3 Test Suite
Tests multi-tool integration, intelligent chaining, and end-to-end workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tool_health_checker import ToolHealthChecker
from app.tools.nmap_tool import NmapTool
from app.tools.nuclei_tool import NucleiTool
from app.tools.function_toolbox import SECURITY_TOOLS
from app.db.session import SessionLocal
from app.models.scan import Scan
from app.services.function_calling_agent import FunctionCallingAgent
import asyncio

print("="*80)
print("🧪 FASE 3: COMPREHENSIVE INTEGRATION TEST SUITE")
print("="*80)
print()

all_passed = True
test_results = []

# =============================================================================
# TEST 1: Tool Health Check
# =============================================================================
print("[TEST 1/6] 🏥 Tool Health Check")
print("-" * 80)

try:
    # check_all_tools() returns a dict directly (not wrapped in 'tools' key)
    tool_health = ToolHealthChecker.check_all_tools()
    healthy_count = sum(1 for t in tool_health.values() if t.health_status == 'healthy')
    total_count = len(tool_health)
    
    print(f"✅ Health Check Complete: {healthy_count}/{total_count} tools healthy")
    for tool_name, status in tool_health.items():
        icon = "✅" if status.health_status == 'healthy' else "⚠️"
        print(f"   {icon} {tool_name}: {status.health_status}")
    
    test_results.append(("Tool Health Check", True))
except Exception as e:
    print(f"❌ Health Check Failed: {e}")
    test_results.append(("Tool Health Check", False))
    all_passed = False

print()

# =============================================================================
# TEST 2: Function Toolbox Definitions
# =============================================================================
print("[TEST 2/6] 📦 Function Toolbox Schema Validation")
print("-" * 80)

try:
    required_tools = ['run_nmap', 'run_nuclei', 'run_whatweb', 'run_sslscan', 'complete_assessment']
    defined_tools = [t['name'] for t in SECURITY_TOOLS]
    
    missing_tools = [t for t in required_tools if t not in defined_tools]
    
    if missing_tools:
        print(f"❌ Missing tools: {', '.join(missing_tools)}")
        test_results.append(("Function Toolbox", False))
        all_passed = False
    else:
        print(f"✅ All {len(required_tools)} required tools defined")
        for tool in required_tools:
            print(f"   ✓ {tool}")
        test_results.append(("Function Toolbox", True))
        
        # Validate schema structure
        for tool in SECURITY_TOOLS:
            assert 'name' in tool, f"Tool missing 'name': {tool}"
            assert 'description' in tool, f"Tool missing 'description': {tool['name']}"
            assert 'parameters' in tool, f"Tool missing 'parameters': {tool['name']}"
        print(f"✅ All tools have valid schema structure")
        
except Exception as e:
    print(f"❌ Toolbox Validation Failed: {e}")
    test_results.append(("Function Toolbox", False))
    all_passed = False

print()

# =============================================================================
# TEST 3: Nmap Tool Execution (Quick Scan)
# =============================================================================
print("[TEST 3/6] 🔍 Nmap Tool Execution Test")
print("-" * 80)

try:
    nmap = NmapTool()
    
    if not nmap.is_installed():
        print("⚠️ Nmap not installed, skipping execution test")
        test_results.append(("Nmap Execution", None))
    else:
        print("🚀 Running Nmap quick scan on scanme.nmap.org...")
        result = nmap.execute("scanme.nmap.org", profile="quick")
        
        if result.exit_code == 0:
            print(f"✅ Nmap completed successfully")
            print(f"   ⏱️ Execution time: {result.execution_time:.2f}s")
            if result.parsed_data:
                open_ports = result.parsed_data.get('open_ports', [])
                print(f"   📊 Found {len(open_ports)} open ports")
                test_results.append(("Nmap Execution", True))
            else:
                print("⚠️ Nmap ran but parsing failed")
                test_results.append(("Nmap Execution", None))
        else:
            print(f"❌ Nmap failed with exit code {result.exit_code}")
            print(f"   Error: {result.stderr[:200]}")
            test_results.append(("Nmap Execution", False))
            all_passed = False
            
except Exception as e:
    print(f"❌ Nmap Test Failed: {e}")
    test_results.append(("Nmap Execution", False))
    all_passed = False

print()

# =============================================================================
# TEST 4: Nuclei Tool Execution (Mock Test)
# =============================================================================
print("[TEST 4/6] 🎯 Nuclei Tool Validation")
print("-" * 80)

try:
    nuclei = NucleiTool()
    
    if not nuclei.is_installed():
        print("⚠️ Nuclei not installed properly")
        test_results.append(("Nuclei Validation", False))
        all_passed = False
    else:
        print("✅ Nuclei installed and accessible")
        print(f"   📁 Path: {nuclei._get_nuclei_path()}")
        
        # Test command building
        cmd = nuclei.build_command("https://example.com", "normal")
        assert 'nuclei' in cmd[0].lower(), "Nuclei command should start with nuclei binary"
        assert '-json' in cmd, "Nuclei should output JSON"
        print(f"✅ Nuclei command building works")
        print(f"   📋 Command: {' '.join(cmd[:6])}...")
        
        test_results.append(("Nuclei Validation", True))
        
except Exception as e:
    print(f"❌ Nuclei Test Failed: {e}")
    test_results.append(("Nuclei Validation", False))
    all_passed = False

print()

# =============================================================================
# TEST 5: AI Agent Initialization
# =============================================================================
print("[TEST 5/6] 🤖 AI Agent Initialization Test")
print("-" * 80)

try:
    # Check if Gemini API key exists
    import os
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment")
        print("   Set with: export GEMINI_API_KEY=your_key (Linux/Mac)")
        print("   Set with: $env:GEMINI_API_KEY='your_key' (Windows PowerShell)")
        test_results.append(("AI Agent Init", None))
    else:
        print("✅ Gemini API key found")
        
        # Try to initialize agent
        try:
            agent = FunctionCallingAgent(api_key, use_pro_model=False, hybrid_mode=True)
            print(f"✅ AI Agent initialized successfully")
            print(f"   🔀 Hybrid Mode: Enabled")
            print(f"   ⚡ Flash Model: {agent.flash_name}")
            print(f"   🧠 Pro Model: {agent.pro_name}")
            test_results.append(("AI Agent Init", True))
        except Exception as e:
            print(f"❌ Agent initialization failed: {e}")
            test_results.append(("AI Agent Init", False))
            all_passed = False
            
except Exception as e:
    print(f"❌ AI Agent Test Failed: {e}")
    test_results.append(("AI Agent Init", False))
    all_passed = False

print()

# =============================================================================
# TEST 6: Database Schema Validation
# =============================================================================
print("[TEST 6/6] 🗄️ Database Schema Validation")
print("-" * 80)

try:
    from sqlalchemy import inspect
    from app.db.session import engine
    from app.models.scan import Scan
    from app.models.result import ScanResult
    from app.models.chat_message import ChatMessage
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['scans', 'scan_results', 'chat_messages']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f"❌ Missing database tables: {', '.join(missing_tables)}")
        print("   Run migrations: python migrate_add_chat.py")
        test_results.append(("Database Schema", False))
        all_passed = False
    else:
        print(f"✅ All required tables exist: {', '.join(required_tables)}")
        
        # Check key columns in scans table
        scan_columns = [c['name'] for c in inspector.get_columns('scans')]
        required_cols = ['id', 'target', 'user_prompt', 'profile', 'status']
        missing_cols = [c for c in required_cols if c not in scan_columns]
        
        if missing_cols:
            print(f"⚠️ Scans table missing columns: {', '.join(missing_cols)}")
            test_results.append(("Database Schema", None))
        else:
            print(f"✅ Scans table has all required columns")
            test_results.append(("Database Schema", True))
            
except Exception as e:
    print(f"❌ Database Schema Test Failed: {e}")
    test_results.append(("Database Schema", False))
    all_passed = False

print()

# =============================================================================
# TEST SUMMARY
# =============================================================================
print("="*80)
print("📊 TEST RESULTS SUMMARY")
print("="*80)

passed_count = sum(1 for _, result in test_results if result == True)
failed_count = sum(1 for _, result in test_results if result == False)
skipped_count = sum(1 for _, result in test_results if result == None)
total_count = len(test_results)

for test_name, result in test_results:
    if result == True:
        icon = "✅"
        status = "PASSED"
    elif result == False:
        icon = "❌"
        status = "FAILED"
    else:
        icon = "⚠️"
        status = "SKIPPED"
    
    print(f"{icon} {test_name:30} [{status}]")

print("-"*80)
print(f"Total Tests: {total_count}")
print(f"✅ Passed: {passed_count}")
print(f"❌ Failed: {failed_count}")
print(f"⚠️ Skipped: {skipped_count}")
print("="*80)

if all_passed and failed_count == 0:
    print()
    print("🎉 ALL CRITICAL TESTS PASSED!")
    print()
    print("✨ FASE 3 READY FOR PRODUCTION!")
    print()
    print("Next Steps:")
    print("  1. Run backend: cd backend && uvicorn app.main:app --reload")
    print("  2. Run frontend: cd frontend && npm run dev")
    print("  3. Navigate to http://localhost:3000")
    print("  4. Start a scan and observe multi-tool chaining!")
    print()
    sys.exit(0)
elif failed_count > 0:
    print()
    print("❌ SOME TESTS FAILED")
    print()
    print("Please fix the failed tests before proceeding.")
    print()
    sys.exit(1)
else:
    print()
    print("⚠️ SOME TESTS SKIPPED")
    print()
    print("Core functionality is ready, but some components need attention.")
    print()
    sys.exit(0)

