"""
Quick test of Reward V2 - Check reward ranges
"""

from envs.subfinder_httpx_env import SubfinderHttpxEnv
import numpy as np

print("🧪 TESTING REWARD V2 - Simplified Reward Function")
print("="*60)

env = SubfinderHttpxEnv(scenarios_path="data/scenarios/phase1_training.json")

print("\n📊 Running 5 test episodes...\n")

rewards = []
for i in range(5):
    obs, _ = env.reset()
    episode_reward = 0
    done = False
    steps = 0
    actions_taken = []
    
    while not done:
        # Random valid action
        valid_actions = np.where(env.action_masks())[0]
        action = np.random.choice(valid_actions)
        actions_taken.append(action)
        
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        done = terminated or truncated
        steps += 1
        
        # Print step details
        if 'reward_breakdown' in info:
            print(f"  Step {steps}: action={action}, reward={reward:.1f}, breakdown={info['reward_breakdown']}")
    
    rewards.append(episode_reward)
    print(f"\n✅ Episode {i+1}: {episode_reward:7.2f} reward ({steps} steps, actions={actions_taken})")
    print(f"   Subdomains: {len(env.found_subdomains)}, Live: {len(env.live_hosts)}")
    print()

print("="*60)
print(f"📈 RESULTS:")
print(f"   Mean: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
print(f"   Min: {np.min(rewards):.2f}")
print(f"   Max: {np.max(rewards):.2f}")
print()

# Check for negative rewards
negative_count = sum(1 for r in rewards if r < 0)
print(f"✅ Negative rewards: {negative_count}/5 (should be 0!)")
print(f"✅ All positive or zero: {all(r >= 0 for r in rewards)}")

# Expected ranges
print(f"\n🎯 EXPECTED RANGES (Reward V2):")
print(f"   Timeout (no discovery): 0")
print(f"   Bad strategy (low coverage): 60-100")
print(f"   Medium strategy: 160-250")
print(f"   Good strategy: 300-450")
print(f"   Excellent strategy: 450-600")
