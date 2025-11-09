"""
Quick Diagnostic: Test Gemini Function Calling Behavior

This script tests if Gemini will use function calling or output JSON text.
Run this BEFORE starting full scan to diagnose the issue.

Usage:
    python test_gemini_function_calling.py
"""

import os
import sys
import google.generativeai as genai
from app.core.tool_definition_manager import ToolDefinitionManager
from app.utils.logger import logger

def test_function_calling():
    """Test if Gemini uses function calling correctly"""
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    
    print(f"✅ API Key found (length: {len(api_key)})")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Get tool definitions
    print("\n📋 Loading tool definitions...")
    flash_tools = ToolDefinitionManager.get_flash_tools()
    print(f"✅ Loaded {len(flash_tools[0].function_declarations)} tools")
    
    # Test 1: Without forcing function calls
    print("\n" + "="*80)
    print("TEST 1: Normal Mode (No Force)")
    print("="*80)
    
    model_normal = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        tools=flash_tools,
        system_instruction="You are a security agent. Use function calling to execute scans."
    )
    
    chat_normal = model_normal.start_chat(enable_automatic_function_calling=False)
    
    prompt = """Perform a port scan on the target using nmap.

CRITICAL: Use the run_nmap function. Do NOT output JSON text.

Call run_nmap with:
- target_placeholder: "TARGET_HOST"
- scan_profile: "quick"

Execute now."""
    
    print("\n📤 Sending prompt...")
    response = chat_normal.send_message(prompt)
    
    print("\n📥 Response received:")
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        
        if hasattr(part, 'function_call') and part.function_call:
            print("✅ SUCCESS: Gemini made a FUNCTION CALL")
            print(f"   Function: {part.function_call.name}")
            print(f"   Arguments: {dict(part.function_call.args)}")
        elif hasattr(part, 'text') and part.text:
            print("❌ FAILURE: Gemini returned TEXT instead of function call")
            print(f"   Text (first 200 chars): {part.text[:200]}...")
            if '{"' in part.text or 'scan_commands' in part.text:
                print("   ⚠️ Detected JSON output - this is the problem!")
        else:
            print("⚠️ UNKNOWN: Response has no function_call or text")
    else:
        print("❌ ERROR: No response candidates")
    
    # Test 2: With forced function calling (Option A)
    print("\n" + "="*80)
    print("TEST 2: Forced Function Calling Mode (Option A)")
    print("="*80)
    
    model_forced = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        tools=flash_tools,
        system_instruction="You MUST use function calling. NEVER output JSON text."
    )
    
    chat_forced = model_forced.start_chat(enable_automatic_function_calling=False)
    
    print("\n📤 Sending prompt with tool_config...")
    try:
        response = chat_forced.send_message(
            prompt,
            tool_config={
                'function_calling_config': {
                    'mode': 'ANY'  # Force function calling
                }
            }
        )
        
        print("\n📥 Response received:")
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            if hasattr(part, 'function_call') and part.function_call:
                print("✅ SUCCESS: Forced function calling WORKED!")
                print(f"   Function: {part.function_call.name}")
                print(f"   Arguments: {dict(part.function_call.args)}")
            elif hasattr(part, 'text') and part.text:
                print("❌ FAILURE: Forced mode FAILED - still getting text")
                print(f"   Text: {part.text[:200]}...")
            else:
                print("⚠️ UNKNOWN: Response has no function_call or text")
        else:
            print("❌ ERROR: No response candidates")
    except Exception as e:
        print(f"❌ ERROR: Exception during forced mode: {e}")
        print("   This means tool_config is not supported or has wrong format")
    
    # Test 3: With Gemini 1.5 Pro (Option B)
    print("\n" + "="*80)
    print("TEST 3: Gemini 1.5 Pro Stable Model (Option B)")
    print("="*80)
    
    model_pro = genai.GenerativeModel(
        model_name='gemini-1.5-pro-002',
        tools=flash_tools,
        system_instruction="You MUST use function calling."
    )
    
    chat_pro = model_pro.start_chat(enable_automatic_function_calling=False)
    
    print("\n📤 Sending prompt to Pro model...")
    try:
        response = chat_pro.send_message(prompt)
        
        print("\n📥 Response received:")
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            if hasattr(part, 'function_call') and part.function_call:
                print("✅ SUCCESS: Pro model used FUNCTION CALLING")
                print(f"   Function: {part.function_call.name}")
                print(f"   Arguments: {dict(part.function_call.args)}")
            elif hasattr(part, 'text') and part.text:
                print("❌ FAILURE: Pro model also returns text")
                print(f"   Text: {part.text[:200]}...")
            else:
                print("⚠️ UNKNOWN: Response has no function_call or text")
        else:
            print("❌ ERROR: No response candidates")
    except Exception as e:
        print(f"❌ ERROR: Exception with Pro model: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    print("""
Next Steps Based on Results:

If TEST 1 PASSED:
  → Your original prompts were already working!
  → Just restart backend and test

If TEST 2 PASSED:
  → Option A works! Forced function calling is the solution
  → Changes already applied to hybrid_orchestrator.py
  → Restart backend and test

If TEST 3 PASSED (but 1 & 2 failed):
  → Switch to Gemini 1.5 Pro
  → Set USE_STABLE_PRO_MODEL = True in hybrid_orchestrator.py line 70
  → Restart backend and test

If ALL TESTS FAILED:
  → Problem with API key, tool definitions, or Gemini account
  → Check API key permissions
  → Check if function calling is enabled for your account
  → Contact project manager

Run this test now to see which option works!
""")

if __name__ == "__main__":
    try:
        test_function_calling()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

