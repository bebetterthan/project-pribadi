"""
Random Agent Baseline for Phase 1B
====================================

Agent that selects random valid actions from the action mask.
This provides a lower bound on expected performance.

Expected Performance:
- Mean reward: ~250-350
- High variance due to randomness
- Approximately 1/3 chance of good tool combinations
"""

import numpy as np
from typing import Any, Dict


class RandomAgent:
    """
    Baseline agent that randomly selects valid actions.
    
    Provides a lower-bound performance baseline. Random exploration
    means sometimes good combinations (comprehensive × 3), sometimes
    poor combinations (passive × 3).
    """
    
    def __init__(self, env: Any = None, seed: int = None):
        """
        Initialize random agent.
        
        Args:
            env: Environment instance (for action space info)
            seed: Random seed for reproducibility
        """
        self.env = env
        self.rng = np.random.default_rng(seed)
        
    def predict(
        self, 
        observation: np.ndarray, 
        state: Any = None, 
        episode_start: np.ndarray = None,
        deterministic: bool = False
    ) -> tuple[np.ndarray, Any]:
        """
        Select random valid action from action mask.
        
        Args:
            observation: Current state (not used)
            state: Internal state (not used)
            episode_start: Episode start flag (not used)
            deterministic: Deterministic mode (not used for random)
            
        Returns:
            Tuple of (action, state)
        """
        # Get valid actions from action mask
        if hasattr(self.env, 'action_masks'):
            mask = self.env.action_masks()
            valid_actions = np.where(mask == 1)[0]
        else:
            # Fallback: all actions valid
            valid_actions = np.arange(self.env.action_space.n)
        
        # Select random valid action
        action = self.rng.choice(valid_actions)
        
        return np.array([action]), state
    
    def set_random_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        self.rng = np.random.default_rng(seed)


def evaluate_random_agent(
    env: Any,
    num_episodes: int = 20,
    seed: int = 42,
    verbose: bool = True
) -> Dict[str, float]:
    """
    Evaluate random agent over multiple episodes.
    
    Args:
        env: Environment to evaluate on
        num_episodes: Number of episodes to run
        seed: Random seed
        verbose: Print episode details
        
    Returns:
        Dictionary with mean, std, min, max rewards
    """
    agent = RandomAgent(env, seed)
    rewards = []
    
    if verbose:
        print("\n" + "="*60)
        print("EVALUATING RANDOM AGENT")
        print("="*60)
    
    for episode in range(num_episodes):
        obs, info = env.reset()
        done = False
        episode_reward = 0.0
        step = 0
        
        while not done:
            action, _ = agent.predict(obs)
            obs, reward, terminated, truncated, info = env.step(action[0])
            episode_reward += reward
            done = terminated or truncated
            step += 1
        
        rewards.append(episode_reward)
        
        if verbose:
            scenario = info.get('scenario_name', 'Unknown')
            print(f"Episode {episode+1:2d}/{num_episodes}: {episode_reward:6.1f} | "
                  f"Steps: {step} | {scenario}")
    
    # Calculate statistics
    results = {
        'mean': np.mean(rewards),
        'std': np.std(rewards),
        'min': np.min(rewards),
        'max': np.max(rewards),
        'episodes': num_episodes,
        'rewards': rewards
    }
    
    if verbose:
        print("="*60)
        print(f"Random Agent Results:")
        print(f"  Mean:  {results['mean']:.1f}")
        print(f"  Std:   {results['std']:.1f}")
        print(f"  Min:   {results['min']:.1f}")
        print(f"  Max:   {results['max']:.1f}")
        print(f"  Range: {results['min']:.1f} to {results['max']:.1f}")
        print("="*60)
    
    return results


if __name__ == "__main__":
    # Test random agent
    import sys
    sys.path.append("../envs")
    from full_recon_env import FullReconEnv
    
    # Create environment
    env = FullReconEnv(scenarios_path="../data/phase1b_train.json")
    
    # Evaluate
    results = evaluate_random_agent(env, num_episodes=20, verbose=True)
    
    print(f"\n✅ Random Agent Baseline: {results['mean']:.1f} ± {results['std']:.1f}")
