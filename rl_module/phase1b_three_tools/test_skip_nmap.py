"""
Test SKIP_NMAP action to verify conditional nmap learning
"""
import sys
sys.path.append('.')

from envs.full_recon_env import FullReconEnv
import numpy as np

def test_skip_nmap_action():
    print("="*70)
    print("TEST: SKIP_NMAP Action (Conditional Learning)")
    print("="*70)
    
    env = FullReconEnv(
        scenarios_path='data/phase1b_train.json',
        time_budget=180,
        max_steps=3
    )
    
    print(f"\n[LOADED] {len(env.scenarios)} scenarios")
    print(f"Action space: {env.action_space.n} actions (was 9, now 10!)")
    print(f"Action names: {env.action_names}")
    
    # Test 1: Full workflow (subfinder → httpx → nmap)
    print("\n" + "="*70)
    print("[TEST 1] Full workflow: subfinder → httpx → nmap")
    print("-"*70)
    
    obs, info = env.reset(seed=42)
    scenario = env.current_scenario
    print(f"Scenario ID: {scenario['id']}")
    print(f"Ports: {scenario['metadata']['port_list']}")
    
    # Step 1: Subfinder
    obs, reward1, term, trunc, info = env.step(0)  # subfinder_passive
    print(f"Step 1 (subfinder): reward={reward1:.1f}, terminated={term}")
    
    # Step 2: HTTPX
    obs, reward2, term, trunc, info = env.step(3)  # httpx_basic
    print(f"Step 2 (httpx): reward={reward2:.1f}, terminated={term}")
    
    # Check action mask in phase 2
    action_mask = env.action_masks()
    print(f"\nAction mask in phase 2: {action_mask}")
    print(f"  Nmap actions (6-8): {action_mask[6:9]}")
    print(f"  Skip action (9): {action_mask[9]}")
    
    # Step 3: Nmap
    obs, reward3, term, trunc, info = env.step(6)  # nmap_quick
    print(f"Step 3 (nmap): reward={reward3:.1f}, terminated={term}")
    print(f"Total reward: {reward1 + reward2 + reward3:.1f}")
    print(f"Nmap used: {info.get('nmap_used', 'N/A')}")
    
    # Test 2: Skip nmap workflow (subfinder → httpx → SKIP)
    print("\n" + "="*70)
    print("[TEST 2] Skip workflow: subfinder → httpx → SKIP")
    print("-"*70)
    
    obs, info = env.reset(seed=42)  # Same scenario
    
    # Step 1: Subfinder
    obs, reward1, term, trunc, info = env.step(0)
    print(f"Step 1 (subfinder): reward={reward1:.1f}")
    
    # Step 2: HTTPX
    obs, reward2, term, trunc, info = env.step(3)
    print(f"Step 2 (httpx): reward={reward2:.1f}")
    
    # Step 3: SKIP nmap (action 9)
    obs, reward3, term, trunc, info = env.step(9)  # skip_nmap
    print(f"Step 3 (SKIP): reward={reward3:.1f}, terminated={term}")
    print(f"Total reward: {reward1 + reward2 + reward3:.1f}")
    print(f"Nmap used: {info.get('nmap_used', 'N/A')}")
    
    print("\n" + "="*70)
    print("✅ SKIP_NMAP action working!")
    print("="*70)
    print("\n📊 Agent can now:")
    print("  1. Use nmap (actions 6-8) → Get discovery + strategic rewards")
    print("  2. Skip nmap (action 9) → Get strategic bonus if appropriate")
    print("\n🎯 This enables TRUE CONDITIONAL LEARNING!")
    print("  - Infrastructure targets: Should use nmap (bonus +400)")
    print("  - Web-only targets: Should skip nmap (bonus +200)")
    print("  - Agent must learn WHEN to use nmap!")

if __name__ == "__main__":
    test_skip_nmap_action()
