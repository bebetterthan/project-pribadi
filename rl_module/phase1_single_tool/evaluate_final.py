"""
Quick script to evaluate the trained model from the last run
"""

import numpy as np
from pathlib import Path
from stable_baselines3 import PPO
from envs.subfinder_httpx_env import SubfinderHttpxEnv

# Load the trained model
model_path = "outputs/run_20251113_034834/final_model"
eval_scenarios = "data/scenarios/phase1_eval.json"

print("🤖 Loading trained model...")
model = PPO.load(model_path)

print("🌍 Creating evaluation environment...")
env = SubfinderHttpxEnv(scenarios_path=eval_scenarios)

print("📊 Evaluating on 10 episodes...\n")

rewards = []
for i in range(10):
    obs, _ = env.reset()
    episode_reward = 0
    done = False
    steps = 0
    
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        done = terminated or truncated
        steps += 1
    
    rewards.append(episode_reward)
    print(f"Episode {i+1:2d}: {episode_reward:7.2f} reward ({steps} steps)")

print(f"\n🎯 Final Results:")
print(f"   Mean: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
print(f"   Min: {np.min(rewards):.2f}, Max: {np.max(rewards):.2f}")

# Compare to baselines
print(f"\n📊 Baseline Comparison:")
print(f"   Random baseline:   304.67 ± 63.56")
print(f"   Hardcoded baseline: 328.31 ± 166.89")
print(f"   Trained agent:     {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")

improvement_vs_random = (np.mean(rewards) / 304.67 - 1) * 100
improvement_vs_hardcoded = (np.mean(rewards) / 328.31 - 1) * 100

print(f"\n🚀 Improvement:")
print(f"   vs Random: {improvement_vs_random:+.1f}%")
print(f"   vs Hardcoded: {improvement_vs_hardcoded:+.1f}%")

# Success criteria
print(f"\n✅ Success Criteria:")
target_2x_random = 304.67 * 2
target_13x_hardcoded = 328.31 * 1.3
print(f"   Target (2x random): {target_2x_random:.2f} - {'✅ PASS' if np.mean(rewards) > target_2x_random else '❌ FAIL'}")
print(f"   Target (1.3x hardcoded): {target_13x_hardcoded:.2f} - {'✅ PASS' if np.mean(rewards) > target_13x_hardcoded else '❌ FAIL'}")
