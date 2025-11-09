#!/usr/bin/env python3
"""
Test script to verify error logging is working correctly
Simulates the '\n description' error scenario
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("ERROR LOGGING TEST - Simulating '\n description' error")
print("="*80)
print()

# Test 1: Print with flush
print("[TEST 1] Direct print() with flush():")
print("   This is a test message", flush=True)
sys.stdout.flush()
print("   ✅ Print with flush works!")
print()

# Test 2: Logger import and use
print("[TEST 2] Testing loguru logger:")
from app.utils.logger import logger
logger.info("[TEST] Logger INFO message")
logger.warning("[TEST] Logger WARNING message")
logger.error("[TEST] Logger ERROR message")
print("   ✅ Logger works!")
print()

# Test 3: Simulate KeyError
print("[TEST 3] Simulating KeyError('\n description'):")
try:
    # This simulates the protobuf parsing error
    test_dict = {"normal_key": "value1"}
    key_with_newline = "\n description"  # Problematic key
    
    print(f"   Attempting to access key: {repr(key_with_newline)}")
    value = test_dict[key_with_newline]  # This will raise KeyError
except KeyError as e:
    error_msg = f"""
{'='*80}
❌ KeyError Caught!
{'='*80}
Error Message: {repr(str(e))}
Error Type: {type(e).__name__}
This is what happens when protobuf has malformed key
{'='*80}
"""
    print(error_msg, flush=True)
    sys.stdout.flush()
    logger.error(f"❌ Caught KeyError: {e}", exc_info=True)
print()

# Test 4: Test async exception in generator context
print("[TEST 4] Testing exception in async generator:")
async def test_generator():
    yield {"type": "test", "content": "Before error"}
    raise KeyError("'\n description'")  # Simulate the actual error
    yield {"type": "test", "content": "After error (never reached)"}

import asyncio

async def run_test_generator():
    try:
        async for event in test_generator():
            print(f"   Event: {event}")
    except KeyError as e:
        error_msg = f"""
{'='*80}
❌ Exception from Generator Caught!
{'='*80}
Error Message: {e}
This shows that exceptions ARE propagated from generators
{'='*80}
"""
        print(error_msg, flush=True)
        sys.stdout.flush()
        logger.error(f"❌ Generator exception: {e}", exc_info=True)

asyncio.run(run_test_generator())
print()

print("="*80)
print("ERROR LOGGING TEST COMPLETE")
print("="*80)
print()
print("CONCLUSION:")
print("- print() with flush() works: ✅")
print("- logger works: ✅")
print("- KeyError simulation works: ✅")
print("- Exception propagation from generator: ✅")
print()
print("If you see all these messages, logging infrastructure is working!")
print("The issue must be in the actual scan flow.")
print("="*80)

