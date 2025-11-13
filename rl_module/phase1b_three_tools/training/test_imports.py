"""Quick test to verify imports work"""
import sys
from pathlib import Path

print("Testing imports...")
print(f"Python: {sys.version}")
print(f"Path: {sys.executable}")

try:
    import numpy as np
    print("✓ numpy OK")
except Exception as e:
    print(f"✗ numpy FAIL: {e}")

try:
    import gymnasium as gym
    print("✓ gymnasium OK")
except Exception as e:
    print(f"✗ gymnasium FAIL: {e}")

try:
    from stable_baselines3 import PPO
    print("✓ stable_baselines3 OK")
except Exception as e:
    print(f"✗ stable_baselines3 FAIL: {e}")

print("\nAll imports successful! Ready to train.")
