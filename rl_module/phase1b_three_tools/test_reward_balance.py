"""
Test REWARD REBALANCING - Make skipping attractive on web-only targets
"""
import sys
sys.path.append('.')

from envs.full_recon_env import FullReconEnv
import numpy as np

def test_reward_rebalancing():
    print("="*70)
    print("TEST: REWARD REBALANCING (Skip vs Use Nmap)")
    print("="*70)
    
    env = FullReconEnv(
        scenarios_path='data/phase1b_train.json',
        time_budget=180,
        max_steps=3
    )
    
    print(f"\n[LOADED] {len(env.scenarios)} scenarios")
    
    # Find web-only and infrastructure scenarios
    web_only_scenarios = []
    infra_scenarios = []
    
    for i, scenario in enumerate(env.scenarios):
        ports = scenario['metadata']['port_list']
        web_ports = [80, 443, 8080, 8443, 3000, 5000]
        infra_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017, 9200, 9092]
        
        has_web = any(p in web_ports for p in ports)
        has_infra = any(p in infra_ports for p in ports)
        
        if has_web and not has_infra:
            web_only_scenarios.append((i, scenario['id'], ports))
        elif has_infra:
            infra_scenarios.append((i, scenario['id'], ports))
    
    print(f"\n📊 Scenario Analysis:")
    print(f"  Web-only scenarios: {len(web_only_scenarios)}")
    print(f"  Infrastructure scenarios: {len(infra_scenarios)}")
    
    # Test 1: Web-only target - SKIP should be better!
    if web_only_scenarios:
        idx, scenario_id, ports = web_only_scenarios[0]
        print("\n" + "="*70)
        print(f"[TEST 1] WEB-ONLY TARGET: {scenario_id}")
        print(f"Ports: {ports}")
        print("-"*70)
        
        # Option A: Use nmap
        env.reset()
        env.current_scenario_idx = idx
        env.current_scenario = env.scenarios[idx]
        obs, r1, _, _, _ = env.step(0)  # subfinder
        obs, r2, _, _, _ = env.step(3)  # httpx
        obs, r3, term, _, info = env.step(6)  # nmap_quick
        total_nmap = r1 + r2 + r3
        
        print(f"\nOption A: USE NMAP")
        print(f"  Step 1 (subfinder): {r1:.0f}")
        print(f"  Step 2 (httpx): {r2:.0f}")
        print(f"  Step 3 (nmap): {r3:.0f}")
        print(f"  TOTAL: {total_nmap:.0f}")
        print(f"  Breakdown: {env.reward_breakdown}")
        
        # Option B: Skip nmap
        env.reset()
        env.current_scenario_idx = idx
        env.current_scenario = env.scenarios[idx]
        obs, r1, _, _, _ = env.step(0)  # subfinder
        obs, r2, _, _, _ = env.step(3)  # httpx
        obs, r3, term, _, info = env.step(9)  # skip_nmap
        total_skip = r1 + r2 + r3
        
        print(f"\nOption B: SKIP NMAP")
        print(f"  Step 1 (subfinder): {r1:.0f}")
        print(f"  Step 2 (httpx): {r2:.0f}")
        print(f"  Step 3 (skip): {r3:.0f}")
        print(f"  TOTAL: {total_skip:.0f}")
        print(f"  Breakdown: {env.reward_breakdown}")
        
        diff = total_skip - total_nmap
        diff_pct = (diff / total_nmap * 100) if total_nmap > 0 else 0
        
        print(f"\n🎯 RESULT:")
        print(f"  Skip: {total_skip:.0f}")
        print(f"  Use:  {total_nmap:.0f}")
        print(f"  Difference: {diff:+.0f} ({diff_pct:+.1f}%)")
        
        if total_skip > total_nmap:
            print(f"  ✅ CORRECT! Skipping is better on web-only (+{diff:.0f})")
        else:
            print(f"  ❌ WRONG! Using nmap still better (+{-diff:.0f})")
    
    # Test 2: Infrastructure target - USE should be better!
    if infra_scenarios:
        idx, scenario_id, ports = infra_scenarios[0]
        print("\n" + "="*70)
        print(f"[TEST 2] INFRASTRUCTURE TARGET: {scenario_id}")
        print(f"Ports: {ports}")
        print("-"*70)
        
        # Option A: Use nmap
        env.reset()
        env.current_scenario_idx = idx
        env.current_scenario = env.scenarios[idx]
        obs, r1, _, _, _ = env.step(0)  # subfinder
        obs, r2, _, _, _ = env.step(3)  # httpx
        obs, r3, term, _, info = env.step(8)  # nmap_service (optimal!)
        total_nmap = r1 + r2 + r3
        
        print(f"\nOption A: USE NMAP (service mode)")
        print(f"  Step 1 (subfinder): {r1:.0f}")
        print(f"  Step 2 (httpx): {r2:.0f}")
        print(f"  Step 3 (nmap): {r3:.0f}")
        print(f"  TOTAL: {total_nmap:.0f}")
        print(f"  Breakdown: {env.reward_breakdown}")
        
        # Option B: Skip nmap
        env.reset()
        env.current_scenario_idx = idx
        env.current_scenario = env.scenarios[idx]
        obs, r1, _, _, _ = env.step(0)  # subfinder
        obs, r2, _, _, _ = env.step(3)  # httpx
        obs, r3, term, _, info = env.step(9)  # skip_nmap
        total_skip = r1 + r2 + r3
        
        print(f"\nOption B: SKIP NMAP")
        print(f"  Step 1 (subfinder): {r1:.0f}")
        print(f"  Step 2 (httpx): {r2:.0f}")
        print(f"  Step 3 (skip): {r3:.0f}")
        print(f"  TOTAL: {total_skip:.0f}")
        print(f"  Breakdown: {env.reward_breakdown}")
        
        diff = total_nmap - total_skip
        diff_pct = (diff / total_skip * 100) if total_skip > 0 else 0
        
        print(f"\n🎯 RESULT:")
        print(f"  Use:  {total_nmap:.0f}")
        print(f"  Skip: {total_skip:.0f}")
        print(f"  Difference: {diff:+.0f} ({diff_pct:+.1f}%)")
        
        if total_nmap > total_skip:
            print(f"  ✅ CORRECT! Using nmap is better on infrastructure (+{diff:.0f})")
        else:
            print(f"  ❌ WRONG! Skipping still better (+{-diff:.0f})")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n📊 Expected Behavior:")
    print("  - Web-only targets: Skip > Use (agent should skip)")
    print("  - Infrastructure targets: Use > Skip (agent should use nmap)")
    print("\n🎯 If both conditions met → Reward balance is CORRECT!")

if __name__ == "__main__":
    test_reward_rebalancing()
