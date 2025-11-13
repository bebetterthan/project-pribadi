"""
Phase 1A Wrapper Agent Baseline for Phase 1B
==============================================

Agent that uses the trained Phase 1A model for subfinder/httpx decisions
and adds a default nmap strategy (service scan for infrastructure, skip for web-only).

This represents "Phase 1A knowledge + basic nmap heuristic".

Expected Performance:
- Mean reward: ~400-500
- Phase 1A was strong at subfinder/httpx (365±98 reward)
- Adding intelligent nmap should boost to ~450-500
- Better than random/hardcoded but not optimal

Note: This baseline requires a trained Phase 1A model to exist.
      If no model exists, will fall back to a smart heuristic strategy.
"""

import numpy as np
from typing import Any, Dict, Optional
from pathlib import Path
import warnings


class Phase1AWrapperAgent:
    """
    Baseline agent that wraps Phase 1A model + default nmap strategy.
    
    Strategy:
    - Phase 0-1 (Subfinder/HTTPX): Use Phase 1A trained model decisions
    - Phase 2 (Nmap): Use heuristic:
        * If infrastructure ports detected (22, 3306, etc.) → action 8 (service scan)
        * If only web ports (80, 443, 8080) → action 6 (quick scan)
        * Default → action 7 (full scan)
    
    If Phase 1A model not available, uses smart heuristic for all phases.
    """
    
    def __init__(
        self, 
        env: Any = None,
        phase1a_model_path: Optional[str] = None,
        fallback_to_heuristic: bool = True
    ):
        """
        Initialize Phase 1A wrapper agent.
        
        Args:
            env: Environment instance
            phase1a_model_path: Path to trained Phase 1A model (.zip)
            fallback_to_heuristic: If True, use heuristic if model not found
        """
        self.env = env
        self.phase1a_model = None
        self.use_heuristic = False
        
        # Try to load Phase 1A model
        if phase1a_model_path and Path(phase1a_model_path).exists():
            try:
                from stable_baselines3 import PPO
                self.phase1a_model = PPO.load(phase1a_model_path)
                print(f"✅ Loaded Phase 1A model from {phase1a_model_path}")
            except Exception as e:
                warnings.warn(f"Failed to load Phase 1A model: {e}")
                if fallback_to_heuristic:
                    self.use_heuristic = True
                    print("[WARNING] Falling back to smart heuristic strategy")
        else:
            if fallback_to_heuristic:
                self.use_heuristic = True
                print("[WARNING] No Phase 1A model found, using smart heuristic strategy")
            else:
                raise FileNotFoundError(f"Phase 1A model not found: {phase1a_model_path}")
    
    def predict(
        self, 
        observation: np.ndarray, 
        state: Any = None, 
        episode_start: np.ndarray = None,
        deterministic: bool = True
    ) -> tuple[np.ndarray, Any]:
        """
        Select action based on Phase 1A model (phases 0-1) or heuristic (phase 2).
        
        Args:
            observation: Current state (40-dim)
            state: Internal state
            episode_start: Episode start flag
            deterministic: Use deterministic policy
            
        Returns:
            Tuple of (action, state)
        """
        # Get current phase
        if hasattr(self.env, 'current_phase'):
            phase = self.env.current_phase
        else:
            # Infer from action mask
            mask = self.env.action_masks()
            if mask[0] == 1:
                phase = 0
            elif mask[3] == 1:
                phase = 1
            else:
                phase = 2
        
        # Phase 0-1: Use Phase 1A model or heuristic
        if phase in [0, 1]:
            if self.phase1a_model and not self.use_heuristic:
                # Use Phase 1A model (map 6-action to 9-action space)
                obs_phase1a = observation[:22]  # Phase 1A used 22-dim state
                action_phase1a, state = self.phase1a_model.predict(
                    obs_phase1a, 
                    state=state, 
                    deterministic=deterministic
                )
                # Map Phase 1A actions to Phase 1B
                # Phase 1A: 0-2 (subfinder), 3-5 (httpx)
                # Phase 1B: 0-2 (subfinder), 3-5 (httpx), 6-8 (nmap)
                action = action_phase1a[0]
            else:
                # Heuristic for subfinder/httpx
                action = self._heuristic_subfinder_httpx(observation, phase)
        
        # Phase 2: Nmap heuristic
        else:
            action = self._heuristic_nmap(observation)
        
        return np.array([action]), state
    
    def _heuristic_subfinder_httpx(self, observation: np.ndarray, phase: int) -> int:
        """
        Smart heuristic for subfinder/httpx decisions.
        
        Strategy:
        - If domain complexity high (>0.6) → comprehensive
        - If domain complexity medium (>0.3) → active/thorough
        - If domain complexity low → passive/basic
        
        Args:
            observation: Current state
            phase: Current phase (0 or 1)
            
        Returns:
            Action index
        """
        domain_complexity = observation[0]
        
        if phase == 0:  # Subfinder
            if domain_complexity > 0.6:
                return 2  # Comprehensive
            elif domain_complexity > 0.3:
                return 1  # Active
            else:
                return 0  # Passive
        else:  # HTTPX (phase == 1)
            if domain_complexity > 0.6:
                return 5  # Comprehensive
            elif domain_complexity > 0.3:
                return 4  # Thorough
            else:
                return 3  # Basic
    
    def _heuristic_nmap(self, observation: np.ndarray) -> int:
        """
        Smart heuristic for nmap decisions based on discovered context.
        
        Strategy:
        - If has_infrastructure_ports (state[30] > 0.5) → action 8 (service scan)
        - If web_only_target (state[34] > 0.5) → action 6 (quick scan)
        - If high port diversity (state[32] > 0.5) → action 8 (service scan)
        - Default → action 7 (full scan)
        
        Args:
            observation: Current state (40-dim)
            
        Returns:
            Action index (6-8)
        """
        has_infrastructure_ports = observation[30]
        port_diversity = observation[32]
        web_only_target = observation[34]
        
        # Infrastructure or diverse ports → thorough service scan
        if has_infrastructure_ports > 0.5 or port_diversity > 0.5:
            return 8  # Service scan (most thorough)
        
        # Web-only target → quick scan (efficient)
        if web_only_target > 0.5:
            return 6  # Quick scan
        
        # Default → full scan (balanced)
        return 7  # Full scan
    
    def set_random_seed(self, seed: int) -> None:
        """Set random seed (for Phase 1A model if loaded)."""
        if self.phase1a_model and hasattr(self.phase1a_model, 'set_random_seed'):
            self.phase1a_model.set_random_seed(seed)


def evaluate_phase1a_wrapper_agent(
    env: Any,
    num_episodes: int = 20,
    phase1a_model_path: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, float]:
    """
    Evaluate Phase 1A wrapper agent over multiple episodes.
    
    Args:
        env: Environment to evaluate on
        num_episodes: Number of episodes to run
        phase1a_model_path: Path to Phase 1A model (if available)
        verbose: Print episode details
        
    Returns:
        Dictionary with mean, std, min, max rewards
    """
    agent = Phase1AWrapperAgent(env, phase1a_model_path=phase1a_model_path)
    rewards = []
    
    strategy = "Phase 1A Model + Heuristic" if agent.phase1a_model else "Smart Heuristic"
    
    if verbose:
        print("\n" + "="*60)
        print(f"EVALUATING PHASE 1A WRAPPER AGENT ({strategy})")
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
        'rewards': rewards,
        'strategy': strategy
    }
    
    if verbose:
        print("="*60)
        print(f"Phase 1A Wrapper Agent Results:")
        print(f"  Strategy: {strategy}")
        print(f"  Mean:  {results['mean']:.1f}")
        print(f"  Std:   {results['std']:.1f}")
        print(f"  Min:   {results['min']:.1f}")
        print(f"  Max:   {results['max']:.1f}")
        print(f"  Range: {results['min']:.1f} to {results['max']:.1f}")
        print("="*60)
        print("\n💡 Note: Should outperform random/hardcoded baselines")
        print("   Uses learned subfinder/httpx + intelligent nmap heuristic")
    
    return results


if __name__ == "__main__":
    # Test Phase 1A wrapper agent
    import sys
    sys.path.append("../envs")
    from full_recon_env import FullReconEnv
    
    # Create environment
    env = FullReconEnv(scenarios_path="../data/phase1b_train.json")
    
    # Evaluate (will use heuristic if no Phase 1A model)
    results = evaluate_phase1a_wrapper_agent(
        env, 
        num_episodes=20, 
        verbose=True
    )
    
    print(f"\n✅ Phase 1A Wrapper Baseline: {results['mean']:.1f} ± {results['std']:.1f}")
