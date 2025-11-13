"""
PHASE 1 ENVIRONMENT: Subfinder + HTTPX Sequential Strategy
===========================================================

2-TOOL SEQUENTIAL environment for teaching RL agent to:
1. Choose optimal subfinder mode (discovery phase)
2. Choose optimal HTTPX mode (probing phase)

DESIGN PHILOSOPHY (Gemini Insights):
- Rich state representation (22 dims) - agent "sees" both phases
- Shaped reward function - no reward hacking!
- Realistic action consequences - tradeoffs matter
- Fast sandbox - instant lookup, >1000 steps/sec

EPISODE FLOW:
reset() → Subfinder Phase → HTTPX Phase → Terminated
   ↓           ↓                 ↓
State[22]   Action 0-2      Action 3-5
           (discovery)      (probing)

Author: Agent-P RL Team
Date: 2025-11-13 (Updated: Subfinder+HTTPX)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path


class SubfinderHttpxEnv(gym.Env):
    """
    Phase 1: 2-tool sequential strategy learning environment.
    
    Goal: Teach agent optimal tool selection for recon+probing workflow.
    
    STATE SPACE (22 dimensions):
        Group 1 - Target Characteristics (5 dims):
        [0] domain_complexity: 0-1 (normalized subdomain count)
        [1] known_subdomains: 0-100 (subdomains found so far)
        [2] high_value_found: 0-1 (found critical subdomains?)
        [3] scan_coverage: 0-1 (estimated % of total found)
        [4] time_elapsed: 0-1 (normalized time budget usage)
        
        Group 2 - Subfinder History (5 dims):
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
        
        Group 4 - HTTPX Phase (7 dims):
        [15] httpx_probed_count: 0-1 (normalized probed hosts)
        [16] httpx_live_found: 0-1 (normalized live hosts)
        [17] httpx_accuracy: 0-1 (live_found / probed)
        [18] httpx_time_spent: 0-1 (normalized httpx time)
        [19] httpx_quick_used: 0/1 (boolean)
        [20] httpx_thorough_used: 0/1 (boolean)
        [21] httpx_comprehensive_used: 0/1 (boolean)
    
    ACTION SPACE (6 discrete):
        PHASE 1 - Subfinder (Discovery):
        0: subfinder_passive (fast, cheap, low coverage)
        1: subfinder_active (medium speed/cost/coverage)
        2: subfinder_comprehensive (slow, expensive, high coverage)
        
        PHASE 2 - HTTPX (Probing):
        3: httpx_quick (fast probe, 90% accuracy)
        4: httpx_thorough (balanced, 95% accuracy)
        5: httpx_comprehensive (slow, 99% accuracy)
    
    REWARD FUNCTION (5 components):
        1. Discovery Rewards: +15/subdomain, +30/critical
        2. Live Discovery: +20/live host, +40/critical live
        3. Efficiency Penalties: -0.05/sec subfinder, -0.03/sec httpx
        4. Strategic Bonuses: +50 coverage, +30 accuracy, +40 all-critical-live
        5. Completion Rewards: +150 success, ×1.5 under budget
    
    PHASES:
        - Subfinder: Actions 0-2 allowed, discover subdomains
        - HTTPX: Actions 3-5 allowed, probe discovered hosts
        - Auto-transition after first subfinder action
        - Episode ends after HTTPX action or timeout
    """
    
    metadata = {"render_modes": ["human"], "render_fps": 1}
    
    def __init__(
        self,
        scenarios_path: str = "data/scenarios/phase1_training.json",
        time_budget: float = 180.0,  # Increased for 2 tools
        render_mode: Optional[str] = None
    ):
        super().__init__()
        
        # Load pre-generated scenarios
        if Path(scenarios_path).is_absolute():
            scenarios_file = Path(scenarios_path)
        else:
            # Try relative to rl_module root
            rl_module_root = Path(__file__).parent.parent.parent
            scenarios_file = rl_module_root / scenarios_path
        
        with open(scenarios_file, "r") as f:
            data = json.load(f)
            self.scenarios = data if isinstance(data, list) else data.get("scenarios", [])
        
        # Environment configuration
        self.time_budget = time_budget
        self.render_mode = render_mode
        
        # Gymnasium spaces
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(22,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(6)  # 3 subfinder + 3 httpx
        
        # Episode state (initialized in reset)
        self.current_scenario: Dict[str, Any] = {}
        self.current_phase: str = "subfinder"  # "subfinder" or "httpx"
        self.found_subdomains: List[str] = []
        self.live_hosts: List[str] = []
        self.modes_used: List[int] = []
        self.httpx_modes_used: List[int] = []
        self.time_elapsed: float = 0.0
        self.episode_reward: float = 0.0
        self.total_scans: int = 0
        self.httpx_total_probed: int = 0
        self.httpx_total_live: int = 0
        self.last_scan_success: float = 0.0
        self.step_count: int = 0
    
    def reset(
        self, 
        seed: Optional[int] = None, 
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment to random scenario.
        
        Returns:
            observation: Initial state (22-dim vector)
            info: Metadata dict
        """
        super().reset(seed=seed)
        
        # Choose random scenario
        self.current_scenario = self.np_random.choice(self.scenarios)
        
        # Reset episode state
        self.current_phase = "subfinder"
        self.found_subdomains = []
        self.live_hosts = []
        self.modes_used = []
        self.httpx_modes_used = []
        self.time_elapsed = 0.0
        self.episode_reward = 0.0
        self.total_scans = 0
        self.httpx_total_probed = 0
        self.httpx_total_live = 0
        self.last_scan_success = 0.0
        self.step_count = 0
        
        observation = self._get_observation()
        info = {
            "scenario_id": self.current_scenario["scenario_id"],
            "type": self.current_scenario["type"],
            "phase": self.current_phase,
            "optimal_subfinder": self.current_scenario["optimal_strategy"],
            "optimal_httpx": self.current_scenario["optimal_httpx_strategy"]
        }
        
        return observation, info
    
    def step(
        self, 
        action: int
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute action and return transition.
        
        Args:
            action: 0-2 (subfinder), 3-5 (httpx)
        
        Returns:
            observation: New state
            reward: Reward for this step
            terminated: Episode completed successfully
            truncated: Episode ended due to constraints
            info: Metadata dict
        """
        
        # Convert action to int (PPO returns numpy array)
        action = int(action)
        
        self.step_count += 1
        
        # Validate action for current phase
        if self.current_phase == "subfinder" and action not in [0, 1, 2]:
            # Invalid action for phase
            return self._get_observation(), -50.0, False, True, {
                "error": "Invalid action for subfinder phase"
            }
        elif self.current_phase == "httpx" and action not in [3, 4, 5]:
            # Invalid action for phase
            return self._get_observation(), -50.0, False, True, {
                "error": "Invalid action for httpx phase"
            }
        
        # Execute action based on phase
        if self.current_phase == "subfinder":
            reward, info = self._execute_subfinder(action)
            # Auto-transition to HTTPX phase
            self.current_phase = "httpx"
        else:  # httpx phase
            reward, info = self._execute_httpx(action)
        
        self.episode_reward += reward
        
        # Check termination
        terminated, truncated = self._check_termination()
        
        # Build observation and info
        observation = self._get_observation()
        info.update({
            "phase": self.current_phase,
            "time_elapsed": self.time_elapsed,
            "episode_reward": self.episode_reward,
            "total_subdomains_found": len(self.found_subdomains),
            "total_live_found": len(self.live_hosts),
            "terminated": terminated,
            "truncated": truncated
        })
        
        return observation, reward, terminated, truncated, info
    
    def _execute_subfinder(self, action: int) -> Tuple[float, Dict[str, Any]]:
        """
        Execute subfinder action (Phase 1).
        
        Args:
            action: 0 (passive), 1 (active), 2 (comprehensive)
        
        Returns:
            reward: Step reward
            info: Action metadata
        """
        
        mode_names = ["passive", "active", "comprehensive"]
        mode_name = mode_names[action]
        
        # Check if redundant scan
        is_redundant = action in self.modes_used
        self.modes_used.append(action)
        self.total_scans += 1
        
        # Simulate subfinder execution (instant lookup!)
        results = self.current_scenario["subfinder_results"][mode_name]
        new_subdomains = [s for s in results["finds"] if s not in self.found_subdomains]
        
        # Update state
        self.found_subdomains.extend(new_subdomains)
        self.time_elapsed += results["time_cost"]
        self.last_scan_success = len(new_subdomains) / max(1, len(results["finds"]))
        
        # Calculate reward
        reward, reward_breakdown = self._calculate_subfinder_reward(
            action=action,
            mode_name=mode_name,
            new_subdomains=new_subdomains,
            is_redundant=is_redundant
        )
        
        info = {
            "action": "subfinder_" + mode_name,
            "new_subdomains": len(new_subdomains),
            "reward_breakdown": reward_breakdown,
            "is_redundant": is_redundant
        }
        
        return reward, info
    
    def _execute_httpx(self, action: int) -> Tuple[float, Dict[str, Any]]:
        """
        Execute HTTPX action (Phase 2).
        
        Args:
            action: 3 (quick), 4 (thorough), 5 (comprehensive)
        
        Returns:
            reward: Step reward
            info: Action metadata
        """
        
        # Map action to httpx mode
        httpx_mode_map = {3: "quick", 4: "thorough", 5: "comprehensive"}
        mode_name = httpx_mode_map[action]
        
        # Check if redundant
        httpx_action_index = action - 3  # 0, 1, 2
        is_redundant = httpx_action_index in self.httpx_modes_used
        self.httpx_modes_used.append(httpx_action_index)
        
        # Get httpx results for discovered subdomains
        # Use results from the subfinder mode we chose
        subfinder_mode = ["passive", "active", "comprehensive"][self.modes_used[0]]
        httpx_results = self.current_scenario["httpx_results"][subfinder_mode][mode_name]
        
        # Update state
        new_live = [h for h in httpx_results["live_hosts"] if h not in self.live_hosts]
        self.live_hosts.extend(new_live)
        self.httpx_total_probed = httpx_results["probed"]
        self.httpx_total_live = httpx_results["live"]
        self.time_elapsed += httpx_results["time_cost"]
        
        # Calculate reward
        reward, reward_breakdown = self._calculate_httpx_reward(
            mode_name=mode_name,
            httpx_results=httpx_results,
            new_live=new_live,
            is_redundant=is_redundant
        )
        
        info = {
            "action": "httpx_" + mode_name,
            "probed": httpx_results["probed"],
            "live_found": httpx_results["live"],
            "new_live": len(new_live),
            "reward_breakdown": reward_breakdown,
            "is_redundant": is_redundant
        }
        
        return reward, info
    
    def _calculate_subfinder_reward(
        self,
        action: int,
        mode_name: str,
        new_subdomains: List[str],
        is_redundant: bool
    ) -> Tuple[float, Dict[str, float]]:
        """
        REWARD FUNCTION V2 - SIMPLIFIED (Subfinder Phase)
        
        DESIGN PHILOSOPHY (from failure analysis):
        - POSITIVE-dominant (encourage action!)
        - SIMPLE (discovery only in subfinder phase)
        - NO harsh time penalties (was killing agent)
        - NO wrong tool penalties (too confusing)
        
        COMPONENTS FOR SUBFINDER:
        1. Discovery Rewards ONLY
           +20 per new subdomain
           +40 per high-value subdomain (critical)
        
        REMOVED from V1:
        - Time penalty per second ❌ TOO HARSH
        - Redundancy penalty ❌ Let action masking handle
        - Wrong tool penalty ❌ Too complex
        - Strategic bonuses ❌ Too confusing
        
        Subfinder phase = just discover, HTTPX evaluates quality!
        """
        
        reward_breakdown = {}
        total_reward = 0.0
        
        ground_truth = self.current_scenario["ground_truth"]["subdomains"]
        
        # ============================================
        # DISCOVERY REWARDS (Main signal)
        # ============================================
        
        # Base discovery: +20 per new subdomain
        subdomain_reward = len(new_subdomains) * 20
        reward_breakdown["subdomain_discovery"] = subdomain_reward
        total_reward += subdomain_reward
        
        # High-value bonus: +40 per critical subdomain
        high_value_count = sum(
            1 for name in new_subdomains
            if name in ground_truth and ground_truth[name]["priority"] == "critical"
        )
        high_value_bonus = high_value_count * 40
        reward_breakdown["high_value_bonus"] = high_value_bonus
        total_reward += high_value_bonus
        
        # No penalties in subfinder phase!
        # Agent learns: "More discovery = better"
        
        return total_reward, reward_breakdown
    
    def _calculate_httpx_reward(
        self,
        mode_name: str,
        httpx_results: Dict[str, Any],
        new_live: List[str],
        is_redundant: bool
    ) -> Tuple[float, Dict[str, float]]:
        """
        REWARD FUNCTION V2 - SIMPLIFIED (HTTPX Phase)
        
        DESIGN PHILOSOPHY:
        - POSITIVE-dominant (encourage verification!)
        - SIMPLE (3 components only)
        - NO harsh time penalties
        - Timeout = missed opportunity (not punishment)
        
        COMPONENTS FOR HTTPX:
        1. Live Discovery Rewards:
           +20 per new live host confirmed
           +40 per critical live host
        
        2. Completion Bonus (Goal incentive):
           +200 if >80% live coverage
           +100 if >60% live coverage
           +50 if >40% live coverage
           0 otherwise
        
        3. Efficiency Bonus (Optional reward, not penalty!):
           +50 if TOTAL episode time <60s
           +30 if TOTAL episode time <90s
           0 if >90s (NO PENALTY!)
        
        REMOVED from V1:
        - Time penalty per second ❌ TOO HARSH
        - Redundancy penalty ❌ Action masking handles this
        - Accuracy bonus ❌ Too confusing
        - Optimal choice bonus ❌ Let agent learn naturally
        
        KEY CHANGE:
        - If agent times out without finding anything: reward = 0 (not negative!)
        - This encourages trying vs giving up!
        """
        
        reward_breakdown = {}
        total_reward = 0.0
        
        ground_truth = self.current_scenario["ground_truth"]["subdomains"]
        total_live_in_ground_truth = self.current_scenario["ground_truth"]["total_live"]
        
        # ============================================
        # COMPONENT 1: LIVE DISCOVERY REWARDS
        # ============================================
        
        # Base live discovery: +20 per live host
        live_reward = len(new_live) * 20
        reward_breakdown["live_discovery"] = live_reward
        total_reward += live_reward
        
        # Critical live bonus: +40 per critical live host
        critical_live = sum(
            1 for host in new_live
            if host in ground_truth and ground_truth[host]["priority"] == "critical"
        )
        critical_live_bonus = critical_live * 40
        reward_breakdown["critical_live_bonus"] = critical_live_bonus
        total_reward += critical_live_bonus
        
        # ============================================
        # COMPONENT 2: COMPLETION BONUS
        # ============================================
        
        # Calculate live coverage (how many real live hosts we found)
        live_coverage = len(self.live_hosts) / max(1, total_live_in_ground_truth)
        
        if live_coverage >= 0.8:
            completion_bonus = 200
        elif live_coverage >= 0.6:
            completion_bonus = 100
        elif live_coverage >= 0.4:
            completion_bonus = 50
        else:
            completion_bonus = 0
        
        reward_breakdown["completion_bonus"] = completion_bonus
        total_reward += completion_bonus
        
        # ============================================
        # COMPONENT 3: EFFICIENCY BONUS (Optional!)
        # ============================================
        
        # Only give bonus if episode completed (not timeout)
        # And only based on TOTAL episode time (subfinder + httpx)
        if self.time_elapsed < 60:
            efficiency_bonus = 50
        elif self.time_elapsed < 90:
            efficiency_bonus = 30
        else:
            efficiency_bonus = 0  # NO PENALTY for being slow!
        
        reward_breakdown["efficiency_bonus"] = efficiency_bonus
        total_reward += efficiency_bonus
        
        # NOTE: If timeout with 0 discovery, total_reward = 0 (not negative!)
        # This is CRITICAL - encourages trying vs giving up!
        
        return total_reward, reward_breakdown
    
    def _get_observation(self) -> np.ndarray:
        """
        Convert episode state to 22-dimensional observation vector.
        All values normalized to [0, 1].
        """
        
        ground_truth = self.current_scenario["ground_truth"]
        total_possible = ground_truth["total_subdomains"]
        total_live = ground_truth["total_live"]
        subdomains = ground_truth["subdomains"]
        
        # Group 1: Target Characteristics (5 dims)
        domain_complexity = min(1.0, total_possible / 25.0)
        known_subdomains = min(1.0, len(self.found_subdomains) / 100.0)
        
        critical_subdomains = [
            name for name, info in subdomains.items()
            if info["priority"] == "critical"
        ]
        high_value_found = float(any(s in self.found_subdomains for s in critical_subdomains))
        
        scan_coverage = len(self.found_subdomains) / max(1, total_possible)
        time_elapsed_norm = min(1.0, self.time_elapsed / self.time_budget)
        
        # Group 2: Subfinder History (5 dims)
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
        high_value_ratio = high_value_found_count / max(1, len(critical_subdomains))
        
        budget_remaining = max(0.0, 1.0 - time_elapsed_norm)
        estimated_completeness = scan_coverage
        
        # Strategy success (recent findings)
        current_strategy_success = self.last_scan_success
        
        # Group 4: HTTPX Phase (7 dims)
        if self.current_phase == "httpx" or len(self.live_hosts) > 0:
            httpx_probed_norm = min(1.0, self.httpx_total_probed / max(1, len(self.found_subdomains)))
            httpx_live_norm = min(1.0, len(self.live_hosts) / max(1, total_live))
            httpx_accuracy = len(self.live_hosts) / max(1, self.httpx_total_probed)
            
            # Estimate httpx time (not perfect but close)
            httpx_time = max(0, self.time_elapsed - sum(
                self.current_scenario["subfinder_results"][["passive", "active", "comprehensive"][m]]["time_cost"]
                for m in self.modes_used if m < 3
            ))
            httpx_time_norm = min(1.0, httpx_time / 60.0)
            
            httpx_quick_used = float(0 in self.httpx_modes_used)
            httpx_thorough_used = float(1 in self.httpx_modes_used)
            httpx_comprehensive_used = float(2 in self.httpx_modes_used)
        else:
            # Subfinder phase - httpx dims are 0
            httpx_probed_norm = 0.0
            httpx_live_norm = 0.0
            httpx_accuracy = 0.0
            httpx_time_norm = 0.0
            httpx_quick_used = 0.0
            httpx_thorough_used = 0.0
            httpx_comprehensive_used = 0.0
        
        # Construct observation vector (22 dims)
        observation = np.array([
            # Group 1
            domain_complexity,
            known_subdomains,
            high_value_found,
            scan_coverage,
            time_elapsed_norm,
            # Group 2
            passive_used,
            active_used,
            comprehensive_used,
            total_scans_norm,
            last_scan_success_norm,
            # Group 3
            subdomains_per_second,
            high_value_ratio,
            budget_remaining,
            estimated_completeness,
            current_strategy_success,
            # Group 4
            httpx_probed_norm,
            httpx_live_norm,
            httpx_accuracy,
            httpx_time_norm,
            httpx_quick_used,
            httpx_thorough_used,
            httpx_comprehensive_used
        ], dtype=np.float32)
        
        # Clip to [0, 1] (safety)
        observation = np.clip(observation, 0.0, 1.0)
        
        return observation
    
    def _check_termination(self) -> Tuple[bool, bool]:
        """
        Check if episode should terminate.
        
        Returns:
            terminated: Episode completed successfully
            truncated: Episode ended due to constraints
        """
        
        # SIMPLIFIED TERMINATION (Reward V2):
        # Episode ends after completing BOTH phases (1 subfinder + 1 httpx)
        # This is cleaner than complex coverage checks
        
        # Terminated: Completed both phases
        terminated = (
            self.current_phase == "httpx" and
            len(self.httpx_modes_used) >= 1  # At least one httpx action done
        )
        
        # Truncated: time budget exhausted (safety)
        truncated = (
            self.time_elapsed >= self.time_budget or
            self.step_count >= 10  # Safety: max 10 steps (should not reach)
        )
        
        return terminated, truncated
    
    def action_masks(self) -> np.ndarray:
        """
        Return valid actions mask for current phase.
        
        Returns:
            Boolean array: [can_passive, can_active, can_comprehensive,
                           can_quick, can_thorough, can_httpx_comprehensive]
        """
        
        mask = np.zeros(6, dtype=bool)
        
        if self.current_phase == "subfinder":
            # Subfinder phase: actions 0-2 valid if not used
            mask[0] = 0 not in self.modes_used
            mask[1] = 1 not in self.modes_used
            mask[2] = 2 not in self.modes_used
        else:  # httpx phase
            # HTTPX phase: actions 3-5 valid if not used
            mask[3] = 0 not in self.httpx_modes_used  # quick
            mask[4] = 1 not in self.httpx_modes_used  # thorough
            mask[5] = 2 not in self.httpx_modes_used  # comprehensive
        
        # If no valid actions, allow all for current phase (safety)
        if not np.any(mask):
            if self.current_phase == "subfinder":
                mask[0:3] = True
            else:
                mask[3:6] = True
        
        return mask
    
    def render(self):
        """Render environment state (console output)"""
        if self.render_mode == "human":
            print(f"\n=== Step {self.step_count} ===")
            print(f"Phase: {self.current_phase}")
            print(f"Subdomains: {len(self.found_subdomains)}")
            print(f"Live Hosts: {len(self.live_hosts)}")
            print(f"Time: {self.time_elapsed:.1f}s / {self.time_budget:.1f}s")
            print(f"Reward: {self.episode_reward:.2f}")


# Test
if __name__ == "__main__":
    print("🧪 Testing SubfinderHttpxEnv...\n")
    
    # Create environment
    env = SubfinderHttpxEnv(scenarios_path="data/scenarios/phase1_training.json")
    
    print(f"✅ Environment created")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")
    print(f"   Loaded scenarios: {len(env.scenarios)}")
    
    # Run test episode
    print("\n🎮 Running test episode...\n")
    
    obs, info = env.reset()
    print(f"Reset: scenario_id={info['scenario_id']}, type={info['type']}")
    print(f"Observation shape: {obs.shape}")
    print(f"Optimal: {info['optimal_subfinder']} (subfinder) + {info['optimal_httpx']} (httpx)")
    
    # Subfinder phase
    print(f"\n--- SUBFINDER PHASE ---")
    action = 2  # comprehensive
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Action: {info['action']}")
    print(f"Reward: {reward:.2f}")
    print(f"New subdomains: {info['new_subdomains']}")
    print(f"Total found: {info['total_subdomains_found']}")
    print(f"Phase: {info['phase']}")
    
    # HTTPX phase
    print(f"\n--- HTTPX PHASE ---")
    action = 5  # comprehensive
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Action: {info['action']}")
    print(f"Reward: {reward:.2f}")
    print(f"Probed: {info['probed']}")
    print(f"Live: {info['live_found']}")
    print(f"Total live: {info['total_live_found']}")
    print(f"Terminated: {terminated}, Truncated: {truncated}")
    
    print(f"\n✅ Episode finished!")
    print(f"   Total reward: {info['episode_reward']:.2f}")
    print(f"   Time: {info['time_elapsed']:.1f}s")
    print(f"   Subdomains: {info['total_subdomains_found']}")
    print(f"   Live: {info['total_live_found']}")
    
    print("\n🎉 SubfinderHttpxEnv test complete!")
