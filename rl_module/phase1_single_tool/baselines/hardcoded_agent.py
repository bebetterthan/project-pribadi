"""
BASELINE AGENT: Hardcoded "Always Comprehensive" Strategy (2-TOOL)
===================================================================

Simple baseline that always chooses comprehensive mode for both tools.

Represents the "safe but slow" approach - always use most thorough scans.
Used for comparison to measure RL agent efficiency improvement.
Target: RL agent should beat hardcoded by >30%
"""

import numpy as np
from typing import Any


class HardcodedAgent:
    """Always choose comprehensive for both subfinder and httpx"""
    
    def __init__(self, env: Any):
        """
        Args:
            env: Gymnasium environment with action_space and action_masks()
        """
        self.env = env
        self.action_space = env.action_space
    
    def select_action(self, observation: np.ndarray) -> int:
        """
        Select action: Always prefer comprehensive, fallback if not valid.
        
        Strategy:
        - Subfinder phase: comprehensive (2) > active (1) > passive (0)
        - HTTPX phase: comprehensive (5) > thorough (4) > quick (3)
        
        Args:
            observation: Current environment observation (unused)
        
        Returns:
            Action index (0-5)
        """
        # Get valid actions and current phase
        # Use unwrapped to access action_masks() if env is wrapped by Monitor
        env_unwrapped = getattr(self.env, 'unwrapped', self.env)
        action_mask = env_unwrapped.action_masks()
        
        # Determine phase from mask
        if any(action_mask[0:3]):  # Subfinder phase
            # Preference: comprehensive > active > passive
            preference_order = [2, 1, 0]
        else:  # HTTPX phase
            # Preference: comprehensive > thorough > quick
            preference_order = [5, 4, 3]
        
        for action in preference_order:
            if action_mask[action]:
                return action
        
        # Fallback (should never happen if action_masks() works correctly)
        valid_actions = np.where(action_mask)[0]
        return valid_actions[0] if len(valid_actions) > 0 else 0
    
    def __repr__(self) -> str:
        return "HardcodedAgent(strategy='always_comprehensive', 2-tool)"


# Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from envs.subfinder_httpx_env import SubfinderHttpxEnv
    
    print("🧪 Testing HardcodedAgent (2-tool)...\n")
    
    # Create environment and agent
    env = SubfinderHttpxEnv(scenarios_path="data/scenarios/phase1_training.json")
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
        print(f"Episode {ep+1}: {episode_reward:.2f} reward, "
              f"{info['total_subdomains_found']} subdomains, "
              f"{info['total_live_found']} live")
    
    avg_reward = np.mean(total_rewards)
    std_reward = np.std(total_rewards)
    
    print(f"\n✅ Hardcoded Baseline (2-tool): {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min: {min(total_rewards):.2f}")
    print(f"   Max: {max(total_rewards):.2f}")
    
    print("\n🎉 HardcodedAgent test complete!")
