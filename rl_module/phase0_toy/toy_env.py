"""
PHASE 0: Toy Environment - Proof of Concept

ULTRA-MINIMAL Environment untuk validate RL fundamentals work.

Complexity: MINIMAL
├── 1 scenario only (fixed target)
├── 2 actions (quick_scan vs thorough_scan)
├── 5-dimensional state
├── Simple reward (+10 discovery, -0.1 time)
└── Training: 10,000 steps (30 minutes)

Learning Goal: "Use thorough when time permits, quick when rushed"

Success Criteria:
✅ Environment runs without errors
✅ Training completes in <1 hour
✅ Agent beats random baseline by >60%
✅ Reward improves over time (TensorBoard)
✅ Can explain agent's learned pattern

COPILOT PROMPT:
Implement ultra-simple gymnasium environment with:
- Observation space: Box(5,) - [info_discovered, time_elapsed, scans_performed, 
                                 last_action_worked, budget_remaining]
- Action space: Discrete(2) - [0=quick_scan, 1=thorough_scan]
- Reward: +10 for info discovery, -0.1 per second
- Episode: Terminates when info_discovered >= 0.9 or time_elapsed >= 1.0

Quick scan: Discovers 30-50% info, takes 0.1-0.2 time
Thorough scan: Discovers 60-90% info, takes 0.3-0.5 time

Agent should learn: Use thorough early, switch to quick if running out of time
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, Optional


class ToyReconEnv(gym.Env):
    """
    Ultra-minimal environment for RL proof of concept.
    
    This is intentionally simple to validate:
    1. Gymnasium setup works
    2. RL training loop functional
    3. Agent can learn basic pattern
    4. Reward function influences behavior
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, render_mode: Optional[str] = None):
        """
        Initialize toy environment.
        
        COPILOT: Set up observation and action spaces
        """
        super().__init__()
        
        self.render_mode = render_mode
        
        # Observation space: 5 dimensions, all normalized [0, 1]
        # [info_discovered, time_elapsed, scans_performed/10, last_action_worked, budget_remaining]
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(5,),
            dtype=np.float32
        )
        
        # Action space: 2 discrete actions
        # 0 = quick_scan (fast, less info)
        # 1 = thorough_scan (slow, more info)
        self.action_space = spaces.Discrete(2)
        
        # Episode state
        self.info_discovered = 0.0
        self.time_elapsed = 0.0
        self.scans_performed = 0
        self.last_action_worked = 0
        self.budget_remaining = 1.0
        
        # Episode tracking
        self.step_count = 0
        self.total_reward = 0.0
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment to initial state.
        
        COPILOT: Reset all state variables and return initial observation
        """
        super().reset(seed=seed)
        
        # Reset state
        self.info_discovered = 0.0
        self.time_elapsed = 0.0
        self.scans_performed = 0
        self.last_action_worked = 0
        self.budget_remaining = 1.0
        
        # Reset tracking
        self.step_count = 0
        self.total_reward = 0.0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in environment.
        
        Args:
            action: 0 (quick_scan) or 1 (thorough_scan)
        
        Returns:
            observation, reward, done, truncated, info
        
        COPILOT: Implement step logic:
        1. Execute scan (simulate info discovery and time consumption)
        2. Calculate reward (+10 per 0.1 info discovered, -0.1 per 0.1 time)
        3. Update state
        4. Check termination (info >= 0.9 or time >= 1.0)
        5. Return results
        """
        self.step_count += 1
        self.scans_performed += 1
        
        # Execute action
        if action == 0:
            # Quick scan: Fast but less info
            info_gain = np.random.uniform(0.3, 0.5)  # 30-50% info
            time_cost = np.random.uniform(0.1, 0.2)  # 10-20% time
        else:
            # Thorough scan: Slow but more info
            info_gain = np.random.uniform(0.6, 0.9)  # 60-90% info
            time_cost = np.random.uniform(0.3, 0.5)  # 30-50% time
        
        # Update state
        prev_info = self.info_discovered
        self.info_discovered = min(1.0, self.info_discovered + info_gain)
        self.time_elapsed = min(1.0, self.time_elapsed + time_cost)
        self.budget_remaining = max(0.0, 1.0 - self.time_elapsed)
        
        # Check if scan was successful
        actual_info_gain = self.info_discovered - prev_info
        self.last_action_worked = 1 if actual_info_gain > 0.2 else 0
        
        # Calculate reward
        # +10 per 0.1 info discovered (so +100 for full info)
        # -0.1 per second elapsed (normalized)
        reward = (actual_info_gain * 100) - (time_cost * 1.0)
        
        self.total_reward += reward
        
        # Check termination
        done = False
        truncated = False
        
        if self.info_discovered >= 0.9:
            # Success! Discovered enough info
            done = True
            reward += 50  # Completion bonus
        elif self.time_elapsed >= 1.0:
            # Time's up
            truncated = True
            # Penalty if didn't discover enough
            if self.info_discovered < 0.7:
                reward -= 20
        elif self.step_count >= 20:
            # Max steps reached
            truncated = True
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, done, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation.
        
        Returns:
            5D numpy array [info_discovered, time_elapsed, scans_performed/10,
                           last_action_worked, budget_remaining]
        """
        return np.array([
            self.info_discovered,
            self.time_elapsed,
            min(1.0, self.scans_performed / 10.0),  # Normalize to [0, 1]
            float(self.last_action_worked),
            self.budget_remaining
        ], dtype=np.float32)
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional info"""
        return {
            'step': self.step_count,
            'info_discovered': self.info_discovered,
            'time_elapsed': self.time_elapsed,
            'scans_performed': self.scans_performed,
            'total_reward': self.total_reward
        }
    
    def render(self):
        """Render current state"""
        if self.render_mode == "human":
            print(f"\n{'='*50}")
            print(f"Step: {self.step_count}")
            print(f"Info Discovered: {self.info_discovered:.2%}")
            print(f"Time Elapsed: {self.time_elapsed:.2%}")
            print(f"Scans Performed: {self.scans_performed}")
            print(f"Budget Remaining: {self.budget_remaining:.2%}")
            print(f"Total Reward: {self.total_reward:.2f}")
            print(f"{'='*50}")
    
    def close(self):
        """Clean up"""
        pass


# Quick test
if __name__ == "__main__":
    print("🧪 Testing ToyReconEnv...")
    
    env = ToyReconEnv(render_mode="human")
    
    # Test reset
    obs, info = env.reset()
    print(f"Initial observation: {obs}")
    print(f"Observation shape: {obs.shape}")
    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")
    
    # Test episode
    print("\n🎮 Running test episode with random actions...")
    done = False
    truncated = False
    step = 0
    
    while not done and not truncated and step < 10:
        action = env.action_space.sample()
        action_name = "quick_scan" if action == 0 else "thorough_scan"
        print(f"\nStep {step+1}: Action = {action_name}")
        
        obs, reward, done, truncated, info = env.step(action)
        print(f"  Reward: {reward:.2f}")
        print(f"  Info discovered: {info['info_discovered']:.2%}")
        print(f"  Time elapsed: {info['time_elapsed']:.2%}")
        print(f"  Done: {done}, Truncated: {truncated}")
        
        step += 1
    
    print(f"\n✅ Episode finished after {step} steps")
    print(f"   Final info discovered: {info['info_discovered']:.2%}")
    print(f"   Total reward: {info['total_reward']:.2f}")
    
    env.close()
    print("\n✅ ToyReconEnv test complete!")
