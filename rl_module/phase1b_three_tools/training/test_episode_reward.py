#!/usr/bin/env python3
"""Test FULL episode reward accumulation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "envs"))

from full_recon_env import FullReconEnv

# Load environment
env_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
env = FullReconEnv(str(env_path))

print("=" * 70)
print("FULL EPISODE REWARD TRACKING")
print("=" * 70)
print()

# TEST 1: Full 3-tool workflow
print("[TEST 1] Full workflow: subfinder → httpx → nmap")
print("-" * 70)
obs, info = env.reset()
cumulative = 0

obs, reward1, term, trunc, info = env.step(0)  # subfinder_passive
cumulative += reward1
print(f"Step 1 (subfinder): +{reward1:.0f} | Cumulative: {cumulative:.0f}")

obs, reward2, term, trunc, info = env.step(4)  # httpx_thorough
cumulative += reward2
print(f"Step 2 (httpx):     +{reward2:.0f} | Cumulative: {cumulative:.0f}")

obs, reward3, term, trunc, info = env.step(8)  # nmap_service
cumulative += reward3
print(f"Step 3 (nmap):      +{reward3:.0f} | Cumulative: {cumulative:.0f}")

print()
print(f"TOTAL EPISODE REWARD: {cumulative:.0f}")
print(f"Reward breakdown: {env.reward_breakdown}")
print()

# TEST 2: Skip nmap (2 tools only)
print("[TEST 2] Skip nmap: subfinder → httpx → terminate")
print("-" * 70)
obs, info = env.reset()
cumulative2 = 0

obs, reward1, term, trunc, info = env.step(0)  # subfinder
cumulative2 += reward1
print(f"Step 1 (subfinder): +{reward1:.0f} | Cumulative: {cumulative2:.0f}")

obs, reward2, term, trunc, info = env.step(3)  # httpx_basic
cumulative2 += reward2
print(f"Step 2 (httpx):     +{reward2:.0f} | Cumulative: {cumulative2:.0f}")

# Force terminate by reaching max_steps
env.step_count = 3
env._check_termination()
print(f"Step 3: TERMINATED (no nmap)")

print()
print(f"TOTAL EPISODE REWARD: {cumulative2:.0f}")
print(f"Reward breakdown: {env.reward_breakdown}")
print()

# Analysis
print("=" * 70)
print("ANALYSIS")
print("=" * 70)
print(f"Full workflow reward:  {cumulative:.0f}")
print(f"Skip nmap reward:      {cumulative2:.0f}")
print(f"Difference:            {cumulative - cumulative2:.0f} ({((cumulative - cumulative2)/cumulative2*100):.1f}%)")
print()

if cumulative > cumulative2 * 1.5:
    print("✅ Strong incentive to use all 3 tools!")
elif cumulative > cumulative2 * 1.2:
    print("⚠️  Moderate incentive - may need more")
else:
    print("❌ Weak incentive - agent will skip nmap!")

print("=" * 70)
