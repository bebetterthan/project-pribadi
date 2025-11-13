#!/usr/bin/env python3
"""Test that nmap actions actually work in the environment"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "envs"))

from full_recon_env import FullReconEnv
import numpy as np

# Load environment
env_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
env = FullReconEnv(str(env_path))

print("=" * 70)
print("TESTING NMAP ACTIONS")
print("=" * 70)
print()

# Reset environment
obs, info = env.reset()
print(f"[RESET] Episode started")
print(f"  Scenario ID: {env.current_scenario['id']}")
print(f"  Ports: {env.current_scenario['metadata']['port_list']}")
print()

# Step 1: Subfinder active
print("[STEP 1] Action: subfinder_active (action 0)")
obs, reward, term, trunc, info = env.step(0)
print(f"  Reward: {reward:.1f}")
print(f"  Subdomains found: {len(env.discovered['subdomains'])}")
print(f"  Tool used: {env.tools_used['subfinder']}")
print()

# Step 2: HTTPX thorough
print("[STEP 2] Action: httpx_thorough (action 4)")
obs, reward, term, trunc, info = env.step(4)
print(f"  Reward: {reward:.1f}")
print(f"  Endpoints found: {len(env.discovered['live_endpoints'])}")
print(f"  Tool used: {env.tools_used['httpx']}")
print()

# Step 3: Test ALL nmap modes
print("[STEP 3] Testing nmap modes...")
print()

for nmap_action in [6, 7, 8]:  # quick, full, service
    # Reset for clean test
    obs, info = env.reset()
    env.step(0)  # subfinder
    env.step(4)  # httpx
    
    # Try nmap
    mode_name = ['quick', 'full', 'service'][nmap_action - 6]
    print(f"  Testing action {nmap_action} (nmap_{mode_name}):")
    obs, reward, term, trunc, info = env.step(nmap_action)
    
    print(f"    Reward: {reward:.1f}")
    print(f"    Terminated: {term}")
    print(f"    Nmap used: {env.tools_used['nmap']['used']}")
    print(f"    Nmap mode: {env.tools_used['nmap']['mode']}")
    print(f"    Ports found: {len(env.discovered['open_ports'])}")
    print(f"    Reward breakdown: {env.reward_breakdown}")
    print()

print("=" * 70)
print("[RESULT] If all nmap modes show 'used: True', environment is WORKING!")
print("=" * 70)
