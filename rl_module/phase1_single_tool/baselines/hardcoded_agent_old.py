"""
BASELINE AGENT: Hardcoded "Always Comprehensive" Strategy
==========================================================

Simple baseline that always chooses comprehensive mode.

Represents the "safe but slow" approach - always use most thorough scan.
Used for comparison to measure RL agent efficiency improvement.
Target: RL agent should beat hardcoded by >30%
"""

import numpy as np
from typing import Any


class HardcodedAgent:
    """Always choose comprehensive scan (safest but slowest)"""
    
    def __init__(self, env: Any):
        """
        Args:
            env: Gymnasium environment with action_space and action_masks()
        """
        self.env = env
        self.action_space = env.action_space
        # Comprehensive mode is action 2
        self.preferred_action = 2
        
    def select_action(self, observation: np.ndarray) -> int:
        """
        Select action: Always prefer comprehensive, fallback if not valid.
        
        Strategy:
        1. Try comprehensive (most thorough)
        2. If not valid, try active
        3. If not valid, try passive
        
        Args:
            observation: Current environment observation (unused)
        
        Returns:
            Action index
        """
        # Get valid actions
        action_mask = self.env.action_masks()
        
        # Preference order: comprehensive > active > passive
        preference_order = [2, 1, 0]  # comprehensive, active, passive
        
        for action in preference_order:
            if action_mask[action]:
                return action
        
        # Fallback (should never happen if action_masks() works correctly)
        valid_actions = np.where(action_mask)[0]
        return valid_actions[0] if len(valid_actions) > 0 else 0
    
    def __repr__(self) -> str:
        return "HardcodedAgent(strategy='always_comprehensive')"


# Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from envs.subfinder_env import SubfinderEnv
    
    print("🧪 Testing HardcodedAgent...\n")
    
    # Create environment and agent
    env = SubfinderEnv(scenarios_path="data/scenarios/phase1_training.json")
    agent = HardcodedAgent(env)
    
    print(f"✅ Agent created: {agent}")
    
    # Run test episodes
    print("\n🎮 Running 5 test episodes...\n")
    total_rewards = []
    
    for ep in range(5):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        step = 0
        
        while not done and step < 10:
            action = agent.select_action(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            step += 1
        
        total_rewards.append(episode_reward)
        print(f"Episode {ep+1}: {episode_reward:.2f} reward, {info['total_subdomains_found']} subdomains")
    
    avg_reward = np.mean(total_rewards)
    std_reward = np.std(total_rewards)
    
    print(f"\n✅ Hardcoded Baseline: {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min: {min(total_rewards):.2f}")
    print(f"   Max: {max(total_rewards):.2f}")
    
    print("\n🎉 HardcodedAgent test complete!")
