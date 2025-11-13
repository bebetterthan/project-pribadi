"""
PHASE 1 ENVIRONMENT: Subfinder Strategy Learning
================================================

Single-tool environment for teaching RL agent to choose optimal
subfinder mode (passive/active/comprehensive) based on target characteristics.

DESIGN PHILOSOPHY (Gemini Insights):
- Rich state representation (15 dims) - agent "sees" meaningful features
- Shaped reward function - no reward hacking!
- Realistic action consequences - tradeoffs matter
- Fast sandbox - instant lookup, >1000 steps/sec

Author: Agent-P RL Team
Date: 2025-11-13
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path


class SubfinderEnv(gym.Env):
    """
    Phase 1: Single-tool strategy learning environment.
    
    Goal: Teach agent to choose right subfinder mode for target scenario.
    
    STATE SPACE (15 dimensions):
        Group 1 - Target Characteristics (5 dims):
        [0] domain_complexity: 0-1 (normalized subdomain count)
        [1] known_subdomains: 0-100 (subdomains found so far)
        [2] high_value_found: 0-1 (found critical subdomains?)
        [3] scan_coverage: 0-1 (estimated % of total found)
        [4] time_elapsed: 0-1 (normalized time budget usage)
        
        Group 2 - Tool Usage History (5 dims):
        [5] passive_used: 0/1 (boolean)
        [6] active_used: 0/1 (boolean)
        [7] comprehensive_used: 0/1 (boolean)
        [8] total_scans: 0-10 (scan count)
        [9] last_scan_success: 0-1 (did last scan find new?)
        
        Group 3 - Strategic Metrics (5 dims):
        [10] subdomains_per_second: 0-1 (efficiency rate)
        [11] high_value_ratio: 0-1 (% critical found)
        [12] budget_remaining: 0-1 (time left)
        [13] estimated_completeness: 0-1 (how close to all?)
        [14] current_strategy_success: 0-1 (is approach working?)
    
    ACTION SPACE (3 discrete):
        0: subfinder_passive (fast, cheap, low coverage)
        1: subfinder_active (medium speed/cost/coverage)
        2: subfinder_comprehensive (slow, expensive, high coverage)
    
    REWARD FUNCTION (4 components):
        1. Discovery Rewards: +15 per subdomain, +30 per high-value
        2. Efficiency Penalties: -0.05/sec, -20 redundant, -10 wrong tool
        3. Strategic Bonuses: +50 coverage, +30 efficiency, +40 critical
        4. Completion Rewards: +100 success, ×1.5 under budget
    """
    
    metadata = {"render_modes": ["human"], "render_fps": 1}
    
    def __init__(
        self,
        scenarios_path: str = "data/scenarios/phase1_training.json",
        time_budget: float = 120.0,
        render_mode: Optional[str] = None
    ):
        super().__init__()
        
        # Load pre-generated scenarios
        # Handle both absolute and relative paths
        if Path(scenarios_path).is_absolute():
            scenarios_file = Path(scenarios_path)
        else:
            # Relative to rl_module root
            scenarios_file = Path(__file__).parent.parent.parent / scenarios_path
        
        with open(scenarios_file, 'r') as f:
            self.scenarios = json.load(f)
        
        # State space: 15 dimensions (rich, informative)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(15,),
            dtype=np.float32
        )
        
        # Action space: 3 discrete actions (subfinder modes)
        self.action_space = spaces.Discrete(3)
        
        # Environment parameters
        self.time_budget = time_budget
        self.render_mode = render_mode
        
        # Episode state (initialized in reset)
        self.current_scenario: Optional[Dict] = None
        self.found_subdomains: List[str] = []
        self.modes_used: List[int] = []
        self.time_elapsed: float = 0.0
        self.total_scans: int = 0
        self.last_scan_success: float = 0.0
        self.episode_reward: float = 0.0
        self.step_count: int = 0
        
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset environment for new episode"""
        super().reset(seed=seed)
        
        # Choose random scenario
        self.current_scenario = self.scenarios[
            self.np_random.integers(0, len(self.scenarios))
        ]
        
        # Reset episode state
        self.found_subdomains = []
        self.modes_used = []
        self.time_elapsed = 0.0
        self.total_scans = 0
        self.last_scan_success = 0.0
        self.episode_reward = 0.0
        self.step_count = 0
        
        observation = self._get_observation()
        info = {
            "scenario_id": self.current_scenario["scenario_id"],
            "scenario_type": self.current_scenario["type"],
            "optimal_strategy": self.current_scenario["optimal_strategy"]
        }
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute action and return results"""
        self.step_count += 1
        self.total_scans += 1
        
        # Map action to subfinder mode
        mode_names = ["passive", "active", "comprehensive"]
        mode_name = mode_names[action]
        
        # Check if mode already used (redundancy)
        is_redundant = action in self.modes_used
        self.modes_used.append(action)
        
        # Simulate subfinder execution (instant lookup!)
        results = self._simulate_subfinder(mode_name)
        new_subdomains = [s for s in results["finds"] if s not in self.found_subdomains]
        
        # Update state
        self.found_subdomains.extend(new_subdomains)
        self.time_elapsed += results["time_cost"]
        self.last_scan_success = len(new_subdomains) / max(1, len(results["finds"]))
        
        # Calculate reward (ALL components!)
        reward, reward_breakdown = self._calculate_reward(
            action=action,
            mode_name=mode_name,
            new_subdomains=new_subdomains,
            is_redundant=is_redundant
        )
        
        self.episode_reward += reward
        
        # Check termination
        terminated, truncated = self._check_termination()
        
        # Build observation and info
        observation = self._get_observation()
        info = {
            "mode_used": mode_name,
            "new_subdomains_found": len(new_subdomains),
            "total_subdomains_found": len(self.found_subdomains),
            "time_elapsed": self.time_elapsed,
            "episode_reward": self.episode_reward,
            "reward_breakdown": reward_breakdown,
            "is_redundant": is_redundant,
            "terminated": terminated,
            "truncated": truncated
        }
        
        return observation, reward, terminated, truncated, info
    
    def _simulate_subfinder(self, mode: str) -> Dict[str, Any]:
        """
        Simulate subfinder execution via instant lookup.
        NO actual tool execution - pre-computed results!
        
        Target: >1000 steps/second (Gemini insight: speed > GPU)
        """
        return self.current_scenario["subfinder_results"][mode]
    
    def _calculate_reward(
        self,
        action: int,
        mode_name: str,
        new_subdomains: List[str],
        is_redundant: bool
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive reward with anti-reward-hacking measures.
        
        4 COMPONENTS:
        1. Discovery Rewards (encourage finding)
        2. Efficiency Penalties (prevent waste)
        3. Strategic Bonuses (reward smart decisions)
        4. Completion Rewards (incentivize success)
        """
        
        reward_breakdown = {}
        total_reward = 0.0
        
        # Get ground truth
        ground_truth = self.current_scenario["ground_truth"]["subdomains"]
        total_possible = self.current_scenario["ground_truth"]["total_subdomains"]
        
        # ============================================
        # COMPONENT 1: DISCOVERY REWARDS
        # ============================================
        
        # +15 per new subdomain found
        subdomain_reward = len(new_subdomains) * 15
        reward_breakdown["subdomain_discovery"] = subdomain_reward
        total_reward += subdomain_reward
        
        # +30 per HIGH-VALUE subdomain (critical priority)
        high_value_count = sum(
            1 for sub in new_subdomains
            if sub in ground_truth and ground_truth[sub]["priority"] == "critical"
        )
        high_value_reward = high_value_count * 30
        reward_breakdown["high_value_bonus"] = high_value_reward
        total_reward += high_value_reward
        
        # +10 per new technology identified
        tech_reward = len(set(
            ground_truth[sub]["tech"] for sub in new_subdomains if sub in ground_truth
        )) * 10
        reward_breakdown["tech_discovery"] = tech_reward
        total_reward += tech_reward
        
        # ============================================
        # COMPONENT 2: EFFICIENCY PENALTIES
        # ============================================
        
        # -0.05 per second elapsed (encourages speed)
        time_penalty = -0.05 * self.time_elapsed
        reward_breakdown["time_penalty"] = time_penalty
        total_reward += time_penalty
        
        # -20 for redundant scan (using same mode twice)
        if is_redundant:
            redundancy_penalty = -20
            reward_breakdown["redundancy_penalty"] = redundancy_penalty
            total_reward += redundancy_penalty
        else:
            reward_breakdown["redundancy_penalty"] = 0
        
        # -10 for wrong tool choice
        # (comprehensive on tiny target, passive on large target)
        wrong_tool_penalty = 0
        if self.current_scenario["type"] == "small_business" and mode_name == "comprehensive":
            wrong_tool_penalty = -10  # Overkill for small target
        elif self.current_scenario["type"] == "large_corporate" and mode_name == "passive":
            wrong_tool_penalty = -10  # Insufficient for large target
        reward_breakdown["wrong_tool_penalty"] = wrong_tool_penalty
        total_reward += wrong_tool_penalty
        
        # ============================================
        # COMPONENT 3: STRATEGIC BONUSES
        # ============================================
        
        # +50 if >80% coverage achieved
        coverage = len(self.found_subdomains) / total_possible
        if coverage >= 0.8:
            coverage_bonus = 50
            reward_breakdown["coverage_bonus"] = coverage_bonus
            total_reward += coverage_bonus
        else:
            reward_breakdown["coverage_bonus"] = 0
        
        # +30 if high efficiency (coverage / time ratio)
        efficiency = coverage / max(0.1, self.time_elapsed / self.time_budget)
        if efficiency > 0.7:
            efficiency_bonus = 30
            reward_breakdown["efficiency_bonus"] = efficiency_bonus
            total_reward += efficiency_bonus
        else:
            reward_breakdown["efficiency_bonus"] = 0
        
        # +40 if found all critical subdomains
        critical_subdomains = [
            name for name, info in ground_truth.items()
            if info["priority"] == "critical"
        ]
        found_critical = [s for s in critical_subdomains if s in self.found_subdomains]
        if len(found_critical) == len(critical_subdomains) and len(critical_subdomains) > 0:
            critical_bonus = 40
            reward_breakdown["critical_complete_bonus"] = critical_bonus
            total_reward += critical_bonus
        else:
            reward_breakdown["critical_complete_bonus"] = 0
        
        # +20 for choosing optimal mode for scenario type
        if mode_name == self.current_scenario["optimal_strategy"]:
            optimal_bonus = 20
            reward_breakdown["optimal_choice_bonus"] = optimal_bonus
            total_reward += optimal_bonus
        else:
            reward_breakdown["optimal_choice_bonus"] = 0
        
        # ============================================
        # COMPONENT 4: COMPLETION REWARDS
        # ============================================
        
        # +100 for successfully completing reconnaissance
        if coverage >= 0.9:
            completion_bonus = 100
            reward_breakdown["completion_bonus"] = completion_bonus
            total_reward += completion_bonus
            
            # Multiplier ×1.5 if done under time budget
            if self.time_elapsed < self.time_budget:
                budget_multiplier = 1.5
                reward_breakdown["budget_multiplier"] = budget_multiplier
                total_reward *= budget_multiplier
            else:
                reward_breakdown["budget_multiplier"] = 1.0
        else:
            reward_breakdown["completion_bonus"] = 0
            reward_breakdown["budget_multiplier"] = 1.0
        
        return total_reward, reward_breakdown
    
    def _get_observation(self) -> np.ndarray:
        """
        Convert episode state to 15-dimensional observation vector.
        All values normalized to [0, 1].
        """
        
        ground_truth = self.current_scenario["ground_truth"]
        total_possible = ground_truth["total_subdomains"]
        subdomains = ground_truth["subdomains"]
        
        # Group 1: Target Characteristics (5 dims)
        domain_complexity = min(1.0, total_possible / 25.0)  # Normalized by max expected (25)
        known_subdomains = min(1.0, len(self.found_subdomains) / 100.0)
        
        critical_subdomains = [
            name for name, info in subdomains.items()
            if info["priority"] == "critical"
        ]
        high_value_found = float(any(s in self.found_subdomains for s in critical_subdomains))
        
        scan_coverage = len(self.found_subdomains) / max(1, total_possible)
        time_elapsed_norm = min(1.0, self.time_elapsed / self.time_budget)
        
        # Group 2: Tool Usage History (5 dims)
        passive_used = float(0 in self.modes_used)
        active_used = float(1 in self.modes_used)
        comprehensive_used = float(2 in self.modes_used)
        total_scans_norm = min(1.0, self.total_scans / 10.0)
        last_scan_success_norm = self.last_scan_success
        
        # Group 3: Strategic Metrics (5 dims)
        subdomains_per_second = (
            len(self.found_subdomains) / max(0.1, self.time_elapsed)
        ) / 10.0  # Normalized by expected max rate
        
        high_value_found_count = sum(
            1 for s in self.found_subdomains
            if s in subdomains and subdomains[s]["priority"] == "critical"
        )
        high_value_ratio = (
            high_value_found_count / max(1, len(self.found_subdomains))
            if self.found_subdomains else 0.0
        )
        
        budget_remaining = max(0.0, 1.0 - time_elapsed_norm)
        estimated_completeness = scan_coverage
        
        # Current strategy success: did recent scans find new subdomains?
        current_strategy_success = self.last_scan_success
        
        # Combine into observation vector
        observation = np.array([
            # Group 1: Target Characteristics
            domain_complexity,
            known_subdomains,
            high_value_found,
            scan_coverage,
            time_elapsed_norm,
            
            # Group 2: Tool Usage History
            passive_used,
            active_used,
            comprehensive_used,
            total_scans_norm,
            last_scan_success_norm,
            
            # Group 3: Strategic Metrics
            min(1.0, subdomains_per_second),
            high_value_ratio,
            budget_remaining,
            estimated_completeness,
            current_strategy_success
        ], dtype=np.float32)
        
        return observation
    
    def _check_termination(self) -> Tuple[bool, bool]:
        """
        Check termination conditions.
        
        Returns:
            terminated: Episode completed successfully
            truncated: Episode ended due to constraints
        """
        
        total_possible = self.current_scenario["ground_truth"]["total_subdomains"]
        coverage = len(self.found_subdomains) / total_possible
        
        # Terminated: >90% coverage achieved (success!)
        terminated = coverage >= 0.9
        
        # Truncated: time budget exhausted OR max scans reached
        truncated = (
            self.time_elapsed >= self.time_budget or
            self.total_scans >= 3 or  # Max 3 modes
            self.step_count >= 10  # Safety: max 10 steps
        )
        
        return terminated, truncated
    
    def action_masks(self) -> np.ndarray:
        """
        Return valid actions mask.
        Prevents redundant scans and checks budget constraints.
        
        Returns:
            Boolean array: [can_passive, can_active, can_comprehensive]
        """
        
        # Check which modes have been used
        mask = np.array([
            0 not in self.modes_used,  # Can use passive if not used
            1 not in self.modes_used,  # Can use active if not used
            2 not in self.modes_used   # Can use comprehensive if not used
        ], dtype=bool)
        
        # Check budget constraints for each mode
        mode_costs = {"passive": 10, "active": 25, "comprehensive": 60}
        mode_names = ["passive", "active", "comprehensive"]
        
        for i, mode_name in enumerate(mode_names):
            if self.time_elapsed + mode_costs[mode_name] > self.time_budget:
                mask[i] = False
        
        # Ensure at least one action is valid (safety)
        if not mask.any():
            mask[0] = True  # Allow passive as last resort
        
        return mask
    
    def render(self):
        """Render environment state (human-readable)"""
        if self.render_mode == "human":
            print("\n" + "="*60)
            print(f"SUBFINDER ENVIRONMENT - Step {self.step_count}")
            print("="*60)
            print(f"Scenario: {self.current_scenario['domain']} ({self.current_scenario['type']})")
            print(f"Optimal Strategy: {self.current_scenario['optimal_strategy']}")
            print(f"\nFound Subdomains: {len(self.found_subdomains)}/{self.current_scenario['ground_truth']['total_subdomains']}")
            print(f"Time Elapsed: {self.time_elapsed:.1f}s / {self.time_budget:.1f}s")
            print(f"Modes Used: {[['passive', 'active', 'comprehensive'][m] for m in self.modes_used]}")
            print(f"Episode Reward: {self.episode_reward:.2f}")
            print("="*60 + "\n")


# ============================================
# QUICK TEST
# ============================================

if __name__ == "__main__":
    print("🧪 Testing SubfinderEnv...\n")
    
    # Create environment
    env = SubfinderEnv(
        scenarios_path="data/scenarios/phase1_training.json"
    )
    
    print(f"✅ Environment created")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")
    print(f"   Loaded scenarios: {len(env.scenarios)}")
    
    # Test episode
    print("\n🎮 Running test episode...\n")
    obs, info = env.reset()
    print(f"Reset: scenario_id={info['scenario_id']}, type={info['scenario_type']}")
    print(f"Observation shape: {obs.shape}")
    print(f"Optimal strategy: {info['optimal_strategy']}")
    
    done = False
    step = 0
    while not done and step < 3:
        # Get valid actions
        action_mask = env.action_masks()
        valid_actions = np.where(action_mask)[0]
        
        # Choose random valid action
        action = env.np_random.choice(valid_actions)
        
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        step += 1
        
        print(f"\nStep {step}:")
        print(f"  Action: {['passive', 'active', 'comprehensive'][action]}")
        print(f"  Reward: {reward:.2f}")
        print(f"  New subdomains: {info['new_subdomains_found']}")
        print(f"  Total found: {info['total_subdomains_found']}")
        print(f"  Time: {info['time_elapsed']:.1f}s")
        print(f"  Terminated: {terminated}, Truncated: {truncated}")
    
    print(f"\n✅ Episode finished!")
    print(f"   Total reward: {info['episode_reward']:.2f}")
    print(f"   Subdomains found: {info['total_subdomains_found']}")
    
    print("\n🎉 SubfinderEnv test complete!")
