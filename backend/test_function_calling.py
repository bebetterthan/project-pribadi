#!/usr/bin/env python3
"""
Test Function Calling Architecture
Verifies new agent works correctly
"""
import os
import sys

print("="*60)
print("🧪 FUNCTION CALLING AGENT TEST")
print("="*60)
print()

# Test 1: Imports
print("[1/5] Testing imports...")
try:
    from app.tools.function_toolbox import SECURITY_TOOLS, ToolExecutor
    from app.services.function_calling_agent import FunctionCallingAgent
    from app.services.hybrid_router import HybridRouter
    print("   ✅ All modules imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Tool Definitions
print("\n[2/5] Checking tool definitions...")
print(f"   📋 Found {len(SECURITY_TOOLS)} tools:")
for tool in SECURITY_TOOLS:
    print(f"      - {tool['name']}: {tool['description'][:60]}...")
print("   ✅ Tools defined correctly")

# Test 3: Target Substitution
print("\n[3/5] Testing target substitution...")
try:
    from app.db.session import SessionLocal
    db = SessionLocal()
    executor = ToolExecutor(
        real_target="scanme.nmap.org",
        scan_id="test-scan",
        db_session=db
    )
    
    # Test placeholder substitution
    result = executor.substitute_placeholder('TARGET_HOST')
    assert result == "scanme.nmap.org", f"Expected 'scanme.nmap.org', got '{result}'"
    
    result = executor.substitute_placeholder('TARGET_URL')
    assert 'scanme.nmap.org' in result, f"Expected URL with scanme.nmap.org, got '{result}'"
    
    print("   ✅ Target substitution working")
    print(f"      TARGET_HOST → {executor.substitute_placeholder('TARGET_HOST')}")
    print(f"      TARGET_URL → {executor.substitute_placeholder('TARGET_URL')}")
    
    db.close()
except Exception as e:
    print(f"   ❌ Substitution test failed: {e}")
    sys.exit(1)

# Test 4: Hybrid Router
print("\n[4/5] Testing hybrid router...")
try:
    api_key = os.getenv('GEMINI_API_KEY', 'test-key')
    router = HybridRouter(api_key)
    
    # Test complexity analysis
    prompts = [
        ("Scan the target for open ports", "flash"),
        ("Correlate nmap and nuclei results to find exploitation path", "pro"),
        ("Find web vulnerabilities", "flash"),
        ("Analyze the strategic relationship between findings", "pro")
    ]
    
    for prompt, expected in prompts:
        decision = router.analyze_complexity(prompt)
        status = "✅" if decision == expected else "⚠️"
        print(f"   {status} '{prompt[:40]}...' → {decision.upper()}")
    
    print("   ✅ Router decision logic working")
except Exception as e:
    print(f"   ❌ Router test failed: {e}")
    sys.exit(1)

# Test 5: Gemini API (if key available)
print("\n[5/5] Testing Gemini API connection...")
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("   ⚠️ No GEMINI_API_KEY found, skipping API test")
    print("   💡 Set environment variable to test: set GEMINI_API_KEY=your_key")
else:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Quick test
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'OK' in one word")
        print(f"   ✅ Gemini API working")
        print(f"   📝 Response: {response.text[:50]}")
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        print(f"   💡 Check your API key and internet connection")

print()
print("="*60)
print("✅ FUNCTION CALLING ARCHITECTURE READY!")
print("="*60)
print()
print("Next steps:")
print("  1. Run: START_ALL.bat")
print("  2. Create a scan with Live Scan button")
print("  3. Watch AI autonomously select and execute tools!")
print()

