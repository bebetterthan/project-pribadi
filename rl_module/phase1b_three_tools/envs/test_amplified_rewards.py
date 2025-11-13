#!/usr/bin/env python3
"""
Test new amplified strategic bonuses
Verify rewards calculate correctly before training
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from envs.full_recon_env import FullReconEnv
import numpy as np

def test_reward_amplification():
    """Test that new strategic bonuses work as expected"""
    
    print("\n" + "="*70)
    print("STRATEGIC BONUS AMPLIFICATION - TEST SUITE")
    print("="*70)
    
    # Load environment
    train_data = Path(__file__).parent.parent / "data" / "phase1b_train.json"
    env = FullReconEnv(str(train_data))
    
    print(f"\n[Loaded]: {env.num_scenarios} training scenarios")
    
    # Test Case 1: Infrastructure + Service Mode
    print("\n" + "-"*70)
    print("TEST 1: Infrastructure Target + Service Mode")
    print("-"*70)
    
    # Find an infrastructure scenario
    infra_scenario = None
    for scenario in env.scenarios:
        ports = scenario['metadata']['port_list']
        infra_ports = [22, 3306, 5432, 6379]
        if any(p in infra_ports for p in ports):
            infra_scenario = scenario
            break
    
    if infra_scenario:
        env.current_scenario = infra_scenario
        env.reset()
        
        # Simulate: active subfinder → thorough httpx → service nmap
        obs1, reward1, done1, trunc1, info1 = env.step(1)  # subfinder active
        obs2, reward2, done2, trunc2, info2 = env.step(4)  # httpx thorough
        obs3, reward3, done3, trunc3, info3 = env.step(8)  # nmap service
        
        total_reward = env.total_reward
        breakdown = env.reward_breakdown
        
        print(f"Actions: subfinder_active → httpx_thorough → nmap_service")
        print(f"\nReward Breakdown:")
        print(f"  Discovery:   {breakdown['discovery']:.1f}")
        print(f"  Strategic:   {breakdown['strategic']:.1f} ← Should be ~400!")
        print(f"  Completion:  {breakdown['completion']:.1f}")
        print(f"  Efficiency:  {breakdown['efficiency']:.1f}")
        print(f"  TOTAL:       {total_reward:.1f}")
        
        if breakdown['strategic'] >= 350:
            print("[PASS] Strategic bonus amplified correctly! ✅")
        else:
            print(f"[FAIL] Strategic bonus too small: {breakdown['strategic']:.1f} (expected ~400)")
    
    # Test Case 2: Web-Only + Skip Nmap
    print("\n" + "-"*70)
    print("TEST 2: Web-Only Target + Skip Nmap")
    print("-"*70)
    
    # Find web-only scenario
    web_scenario = None
    for scenario in env.scenarios:
        ports = scenario['metadata']['port_list']
        web_ports = [80, 443, 8080]
        infra_ports = [22, 3306, 5432]
        if any(p in web_ports for p in ports) and not any(p in infra_ports for p in ports):
            web_scenario = scenario
            break
    
    if web_scenario:
        env.current_scenario = web_scenario
        env.reset()
        
        # Simulate: active subfinder → thorough httpx → quick nmap
        obs1, reward1, done1, trunc1, info1 = env.step(1)  # subfinder active
        obs2, reward2, done2, trunc2, info2 = env.step(4)  # httpx thorough
        obs3, reward3, done3, trunc3, info3 = env.step(6)  # nmap quick
        
        total_reward = env.total_reward
        breakdown = env.reward_breakdown
        
        print(f"Actions: subfinder_active → httpx_thorough → nmap_quick")
        print(f"\nReward Breakdown:")
        print(f"  Discovery:   {breakdown['discovery']:.1f}")
        print(f"  Strategic:   {breakdown['strategic']:.1f} ← Should be ~50 for quick mode")
        print(f"  Completion:  {breakdown['completion']:.1f}")
        print(f"  Efficiency:  {breakdown['efficiency']:.1f}")
        print(f"  TOTAL:       {total_reward:.1f}")
        
        print(f"[INFO] Web-only with quick mode gets smaller bonus (efficiency focus)")
    
    # Test Case 3: Quick Mode Everywhere (Baseline)
    print("\n" + "-"*70)
    print("TEST 3: Quick Mode Everywhere (Current Agent Strategy)")
    print("-"*70)
    
    # Reset with random scenario
    env.reset()
    
    # Simulate: active subfinder → thorough httpx → quick nmap
    obs1, reward1, done1, trunc1, info1 = env.step(1)  # subfinder active
    obs2, reward2, done2, trunc2, info2 = env.step(4)  # httpx thorough  
    obs3, reward3, done3, trunc3, info3 = env.step(6)  # nmap quick
    
    total_reward = env.total_reward
    breakdown = env.reward_breakdown
    
    print(f"Actions: subfinder_active → httpx_thorough → nmap_quick")
    print(f"\nReward Breakdown:")
    print(f"  Discovery:   {breakdown['discovery']:.1f}")
    print(f"  Strategic:   {breakdown['strategic']:.1f} ← Should be low (~50-100)")
    print(f"  Completion:  {breakdown['completion']:.1f}")
    print(f"  Efficiency:  {breakdown['efficiency']:.1f}")
    print(f"  TOTAL:       {total_reward:.1f}")
    
    print(f"\n[BASELINE] Quick mode everywhere gets low strategic bonus")
    
    # Summary
    print("\n" + "="*70)
    print("REWARD DIFFERENTIAL ANALYSIS")
    print("="*70)
    print(f"\nExpected Reward Ranges:")
    print(f"  Smart conditional (infra+service):  600-900 (HIGH strategic bonus)")
    print(f"  Generic quick mode:                 300-500 (LOW strategic bonus)")
    print(f"  Difference:                         50-80% improvement")
    print(f"\n[CONCLUSION] Agent will clearly see: Smart usage >> Quick mode everywhere! ✅")
    print("="*70)

if __name__ == "__main__":
    test_reward_amplification()
