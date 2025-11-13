"""
BASELINE AGENT: Random Action Selection
========================================

Simple baseline that selects random valid actions.

Used for comparison to measure RL agent improvement.
Target: RL agent should beat random by >100%
"""

import numpy as np
from typing import Any


class RandomAgent:
    """Random action selection baseline"""
    
    def __init__(self, env: Any):
        """
        Args:
            env: Gymnasium environment with action_space and action_masks()
        """
        self.env = env
        self.action_space = env.action_space
    
    def select_action(self, observation: np.ndarray) -> int:
        """
        Select random valid action.
        
        Args:
            observation: Current environment observation (unused)
        
        Returns:
            Random valid action index
        """
        # Get valid actions from environment
        action_mask = self.env.action_masks()
        valid_actions = np.where(action_mask)[0]
        
        # Choose random valid action
        action = np.random.choice(valid_actions)
        
        return action
    
    def __repr__(self) -> str:
        return "RandomAgent()"


# Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from envs.subfinder_env import SubfinderEnv
    
    print("🧪 Testing RandomAgent...\n")
    
    # Create environment and agent
    env = SubfinderEnv(scenarios_path="data/scenarios/phase1_training.json")
    agent = RandomAgent(env)
    
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
    
    print(f"\n✅ Random Baseline: {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min: {min(total_rewards):.2f}")
    print(f"   Max: {max(total_rewards):.2f}")
    
    print("\n🎉 RandomAgent test complete!")
