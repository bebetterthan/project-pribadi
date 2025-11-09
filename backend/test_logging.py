#!/usr/bin/env python3
"""
Quick test to verify logging configuration works
Run this before starting full backend
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("LOGGING TEST - Verifying console output")
print("=" * 60)
print()

# Import logger
from app.utils.logger import logger

print("[TEST 1] Logger imported successfully")
print()

# Test different log levels
logger.debug("[TEST] This is a DEBUG message")
logger.info("[TEST] This is an INFO message")
logger.warning("[TEST] This is a WARNING message")
logger.error("[TEST] This is an ERROR message")

print()
print("=" * 60)
print("If you see colored log messages above, logging is working!")
print("=" * 60)
print()

# Test error with traceback
try:
    print("[TEST 2] Testing error with traceback...")
    raise ValueError("Test error for traceback demonstration")
except Exception as e:
    logger.exception("[TEST] Caught exception (should show full traceback):")

print()
print("=" * 60)
print("LOGGING TEST COMPLETE")
print("=" * 60)

