"""
BASELINE AGENT: Random Strategy Selection (2-TOOL)
===================================================

Random baseline for Subfinder + HTTPX 2-tool workflow.
Selects random valid action for each phase.

Target: RL agent should beat this by >100%
"""

import numpy as np
from typing import Any


class RandomAgent:
    """Random action selection baseline (2-tool workflow)"""
    
    def __init__(self, env: Any):
        """
        Args:
            env: Gymnasium environment with action_space and action_masks()
        """
        self.env = env
        self.action_space = env.action_space
    
    def select_action(self, observation: np.ndarray) -> int:
        """
        Select random valid action based on current phase.
        
        Args:
            observation: Current environment observation
        
        Returns:
            Action index (0-5: 3 subfinder + 3 httpx)
        """
        # Get valid actions for current phase
        # Use unwrapped to access action_masks() if env is wrapped by Monitor
        env_unwrapped = getattr(self.env, 'unwrapped', self.env)
        action_mask = env_unwrapped.action_masks()
        valid_actions = np.where(action_mask)[0]
        
        # Choose random valid action
        if len(valid_actions) > 0:
            return np.random.choice(valid_actions)
        
        # Fallback (should never happen)
        return self.action_space.sample()
    
    def __repr__(self) -> str:
        return "RandomAgent(2-tool)"


# Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from envs.subfinder_httpx_env import SubfinderHttpxEnv
    
    print("🧪 Testing RandomAgent (2-tool)...\n")
    
    # Create environment and agent
    env = SubfinderHttpxEnv(scenarios_path="data/scenarios/phase1_training.json")
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
        print(f"Episode {ep+1}: {episode_reward:.2f} reward, "
              f"{info['total_subdomains_found']} subdomains, "
              f"{info['total_live_found']} live")
    
    avg_reward = np.mean(total_rewards)
    std_reward = np.std(total_rewards)
    
    print(f"\n✅ Random Baseline (2-tool): {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min: {min(total_rewards):.2f}")
    print(f"   Max: {max(total_rewards):.2f}")
    
    print("\n🎉 RandomAgent test complete!")
