"""
Quick Performance Test: Subfinder+HTTPX Environment
====================================================

Test if sandbox meets >1000 steps/sec requirement with 22-dim state.
"""

import time
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from envs.subfinder_httpx_env import SubfinderHttpxEnv


def test_performance():
    print("="*60)
    print("⚡ PERFORMANCE TEST: SubfinderHttpxEnv")
    print("="*60)
    
    env = SubfinderHttpxEnv(scenarios_path="data/scenarios/phase1_training.json")
    
    print(f"\n📊 Environment:")
    print(f"   State space: {env.observation_space.shape} (22-dim)")
    print(f"   Action space: {env.action_space.n} (6 actions)")
    print(f"   Scenarios: {len(env.scenarios)}")
    
    # Warm-up
    print(f"\n🔥 Warming up...")
    for _ in range(100):
        env.reset()
        masks = env.action_masks()
        valid = np.where(masks)[0]
        if len(valid) > 0:
            env.step(valid[0])
    
    # Measure
    print(f"\n⏱️ Measuring performance...")
    start = time.perf_counter()
    steps = 0
    episodes = 0
    
    while steps < 10000 and episodes < 500:
        env.reset()
        episodes += 1
        
        for _ in range(20):
            masks = env.action_masks()
            valid = np.where(masks)[0]
            
            if len(valid) == 0:
                break
            
            obs, reward, terminated, truncated, info = env.step(valid[0])
            steps += 1
            
            if terminated or truncated:
                break
    
    elapsed = time.perf_counter() - start
    steps_per_sec = steps / elapsed
    
    print(f"\n✅ RESULTS:")
    print(f"   Steps: {steps}")
    print(f"   Episodes: {episodes}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Speed: {steps_per_sec:.0f} steps/second")
    
    # Check target
    target = 1000
    status = "✅ PASS" if steps_per_sec > target else "❌ FAIL"
    print(f"\n🎯 Target: >{target} steps/sec")
    print(f"   Status: {status}")
    
    if steps_per_sec > target:
        print(f"   Speedup: {steps_per_sec/target:.1f}x faster than target!")
    
    return steps_per_sec > target


if __name__ == "__main__":
    success = test_performance()
    print("\n" + "="*60)
    exit(0 if success else 1)
