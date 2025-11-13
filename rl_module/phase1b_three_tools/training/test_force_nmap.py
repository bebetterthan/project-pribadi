#!/usr/bin/env python3
"""Test that agent MUST use nmap to get completion bonus"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "envs"))

from full_recon_env import FullReconEnv

# Load environment
env_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
env = FullReconEnv(str(env_path))

print("=" * 70)
print("TESTING: Does skipping nmap prevent completion bonus?")
print("=" * 70)
print()

# TEST 1: Skip nmap (only subfinder + httpx)
print("[TEST 1] Two tools only (subfinder + httpx), NO nmap:")
obs, info = env.reset()
env.step(0)  # subfinder_passive
obs, reward2, term, trunc, info = env.step(3)  # httpx_basic
env.step_count = 3  # Force termination
env._check_termination()

print(f"  Terminated: {env.terminated}")
print(f"  Nmap used: {env.tools_used['nmap']['used']}")
print(f"  Reward breakdown: {env.reward_breakdown}")
print(f"  Completion bonus: {env.reward_breakdown['completion']}")
print(f"  Efficiency bonus: {env.reward_breakdown['efficiency']}")
print()

# TEST 2: Full 3-tool workflow
print("[TEST 2] Full workflow (subfinder + httpx + nmap):")
obs, info = env.reset()
env.step(0)  # subfinder
env.step(4)  # httpx
obs, reward3, term, trunc, info = env.step(6)  # nmap_quick

print(f"  Terminated: {env.terminated}")
print(f"  Nmap used: {env.tools_used['nmap']['used']}")
print(f"  Reward breakdown: {env.reward_breakdown}")
print(f"  Completion bonus: {env.reward_breakdown['completion']}")
print(f"  Efficiency bonus: {env.reward_breakdown['efficiency']}")
print()

print("=" * 70)
print("[EXPECTED] Test 1 should have 0 completion/efficiency bonus")
print("[EXPECTED] Test 2 should have non-zero completion/efficiency bonus")
print("=" * 70)
