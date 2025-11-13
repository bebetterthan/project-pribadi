"""
Hardcoded Agent Baseline for Phase 1B
=======================================

Agent that always selects comprehensive mode for all tools:
- Subfinder: comprehensive (action 2)
- HTTPX: comprehensive (action 5)
- Nmap: service (action 8) - most thorough nmap scan

This represents a "always maximum effort" strategy.

Expected Performance:
- Mean reward: ~300-450
- Low variance (deterministic strategy)
- Good discovery but sometimes inefficient (overkill on simple targets)
"""

import numpy as np
from typing import Any, Dict


class HardcodedAgent:
    """
    Baseline agent that always selects comprehensive/max mode for all tools.
    
    Strategy:
    - Phase 0 (Subfinder): Always action 2 (comprehensive)
    - Phase 1 (HTTPX): Always action 5 (comprehensive)
    - Phase 2 (Nmap): Always action 8 (service scan)
    
    Provides mid-level baseline. Good on complex targets, inefficient on simple ones.
    """
    
    def __init__(self, env: Any = None):
        """
        Initialize hardcoded agent.
        
        Args:
            env: Environment instance (for tracking phases)
        """
        self.env = env
        # Map phase to comprehensive action
        self.action_map = {
            0: 2,  # Subfinder comprehensive
            1: 5,  # HTTPX comprehensive
            2: 8   # Nmap service
        }
    
    def predict(
        self, 
        observation: np.ndarray, 
        state: Any = None, 
        episode_start: np.ndarray = None,
        deterministic: bool = True
    ) -> tuple[np.ndarray, Any]:
        """
        Select hardcoded comprehensive action for current phase.
        
        Args:
            observation: Current state (not used)
            state: Internal state (not used)
            episode_start: Episode start flag (not used)
            deterministic: Always True for hardcoded agent
            
        Returns:
            Tuple of (action, state)
        """
        # Get current phase from environment
        if hasattr(self.env, 'current_phase'):
            phase = self.env.current_phase
        else:
            # Fallback: infer from action mask
            mask = self.env.action_masks()
            if mask[0] == 1:
                phase = 0  # Subfinder
            elif mask[3] == 1:
                phase = 1  # HTTPX
            else:
                phase = 2  # Nmap
        
        # Select comprehensive action for this phase
        action = self.action_map[phase]
        
        return np.array([action]), state
    
    def set_random_seed(self, seed: int) -> None:
        """No randomness in hardcoded agent."""
        pass


def evaluate_hardcoded_agent(
    env: Any,
    num_episodes: int = 20,
    verbose: bool = True
) -> Dict[str, float]:
    """
    Evaluate hardcoded agent over multiple episodes.
    
    Args:
        env: Environment to evaluate on
        num_episodes: Number of episodes to run
        verbose: Print episode details
        
    Returns:
        Dictionary with mean, std, min, max rewards
    """
    agent = HardcodedAgent(env)
    rewards = []
    
    if verbose:
        print("\n" + "="*60)
        print("EVALUATING HARDCODED AGENT (Always Comprehensive)")
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
            scenario_type = info.get('scenario_type', 'Unknown')
            print(f"Episode {episode+1:2d}/{num_episodes}: {episode_reward:6.1f} | "
                  f"Steps: {step} | {scenario} ({scenario_type})")
    
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
        print(f"Hardcoded Agent Results:")
        print(f"  Mean:  {results['mean']:.1f}")
        print(f"  Std:   {results['std']:.1f}")
        print(f"  Min:   {results['min']:.1f}")
        print(f"  Max:   {results['max']:.1f}")
        print(f"  Range: {results['min']:.1f} to {results['max']:.1f}")
        print("="*60)
        print("\n💡 Note: Low variance expected (deterministic strategy)")
        print("   Good on complex targets, inefficient on simple targets")
    
    return results


if __name__ == "__main__":
    # Test hardcoded agent
    import sys
    sys.path.append("../envs")
    from full_recon_env import FullReconEnv
    
    # Create environment
    env = FullReconEnv(scenarios_path="../data/phase1b_train.json")
    
    # Evaluate
    results = evaluate_hardcoded_agent(env, num_episodes=20, verbose=True)
    
    print(f"\n✅ Hardcoded Agent Baseline: {results['mean']:.1f} ± {results['std']:.1f}")
