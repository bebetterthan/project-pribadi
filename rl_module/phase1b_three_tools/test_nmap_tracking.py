"""
Test that nmap_used tracking is now correctly reported in info dict
"""
from envs.full_recon_env import FullReconEnv
import numpy as np

def test_nmap_tracking():
    """Test that info dict contains nmap_used after episode termination"""
    print("=" * 70)
    print("TEST: Nmap Usage Tracking in Info Dict")
    print("=" * 70)
    
    env = FullReconEnv(
        scenarios_path='data/phase1b_train.json',
        time_budget=180,
        max_steps=3
    )
    
    # Test 1: Full 3-tool workflow (WITH nmap)
    print("\n[TEST 1] Full workflow: subfinder → httpx → nmap")
    print("-" * 70)
    obs, info = env.reset()
    
    # Step 1: Subfinder
    action = 0  # subfinder_passive
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step 1 (subfinder): terminated={terminated}, 'nmap_used' in info={('nmap_used' in info)}")
    
    # Step 2: HTTPX
    action = 3  # httpx_basic
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step 2 (httpx): terminated={terminated}, 'nmap_used' in info={('nmap_used' in info)}")
    
    # Step 3: Nmap
    action = 6  # nmap_quick
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step 3 (nmap): terminated={terminated}, 'nmap_used' in info={('nmap_used' in info)}")
    
    if 'nmap_used' in info:
        print(f"✅ nmap_used = {info['nmap_used']}")
        assert info['nmap_used'] == 1, "Expected nmap_used=1 when nmap was called!"
        print("✅ PASS: nmap_used correctly set to 1")
    else:
        print("❌ FAIL: 'nmap_used' key missing from info dict!")
        return False
    
    # Test 2: Try to skip nmap (should be IMPOSSIBLE due to action masking)
    print("\n[TEST 2] Verify action masking forces nmap in step 3")
    print("-" * 70)
    obs, info = env.reset()
    
    # Step 1: Subfinder
    obs, reward, terminated, truncated, info = env.step(0)
    print(f"Step 1 done, current_phase={env.current_phase}")
    
    # Step 2: HTTPX
    obs, reward, terminated, truncated, info = env.step(3)
    print(f"Step 2 done, current_phase={env.current_phase}")
    
    # Step 3: Try invalid action (not nmap) - should terminate with penalty
    action_mask = env.action_masks()
    print(f"Action mask in phase 2: {action_mask}")
    print(f"  Subfinder (0-2): {action_mask[0:3]}")
    print(f"  HTTPX (3-5): {action_mask[3:6]}")
    print(f"  Nmap (6-8): {action_mask[6:9]}")
    
    # Try to take httpx action (should be invalid)
    action = 3  # httpx (invalid in phase 2)
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step 3 (invalid httpx): reward={reward}, terminated={terminated}")
    
    if reward == -10.0 and terminated:
        print("✅ PASS: Invalid action correctly penalized and terminated")
    else:
        print(f"❌ FAIL: Expected reward=-10, terminated=True for invalid action")
        return False
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)
    print("\n📊 Summary:")
    print("  1. info['nmap_used'] is now correctly added to episode termination info")
    print("  2. Training script should now be able to track nmap usage")
    print("  3. Action masking forces agent to use nmap in step 3 (or take penalty)")
    print("\n⚠️ HYPOTHESIS UPDATE:")
    print("  If nmap usage is STILL 0% after this fix, it means:")
    print("  - Agent is taking INVALID actions (getting -10 reward)")
    print("  - Or there's a bug in training script's nmap_usage calculation")
    print("  - NOT that agent is skipping nmap through valid actions!")
    
    return True

if __name__ == '__main__':
    test_nmap_tracking()
