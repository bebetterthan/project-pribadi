"""
Gymnasium environment for reconnaissance workflow training.

COPILOT PROMPT:
Create a Gym-compatible environment that simulates pentesting reconnaissance.
Agent controls 3 core tools: subfinder, httpx, nmap with different execution modes.

STATE SPACE (50 dimensions):
- subdomains_found: int (0-100) - Number of subdomains discovered
- endpoints_found: int (0-500) - Number of web endpoints found
- open_ports: binary vector [100] - Top 100 most common ports (simplified from 65535)
- tools_used: binary [9] - Which tools have been executed
- time_elapsed: float (0-1, normalized from 0-600s)
- current_subdomain_index: int (0-99) - Which subdomain is in focus
- scan_phase: one-hot [3] - [discovery, probing, scanning]
- findings_by_severity: vector [4] - Count of [critical, high, medium, low] findings

ACTION SPACE (9 discrete actions):
0: run_subfinder_passive  - Fast subdomain enumeration (60% coverage, 10s)
1: run_subfinder_active   - Thorough subdomain enumeration (90% coverage, 20s)
2: run_httpx_basic        - Basic HTTP probing (status codes, 3s/domain)
3: run_httpx_detailed     - Detailed HTTP probing + tech detection (7s/domain)
4: run_nmap_quick         - Quick port scan (top 100 ports, 20s)
5: run_nmap_full          - Full port scan (all 65535 ports, 180s)
6: run_nmap_service       - Service detection on known ports (40s)
7: focus_next_subdomain   - Move to next subdomain for detailed scanning
8: finish_scan            - Complete episode (only valid after minimum coverage)

REWARD FUNCTION:
+15 per new subdomain discovered
+25 per new endpoint discovered
+10 per new port discovered
-0.05 per second elapsed (efficiency penalty)
-20 for redundant scan (scanning same target twice)
+100 bonus for successfully completing scan
-50 penalty for finishing before minimum coverage (30%)

ACTION MASKING:
- Can't run httpx before subfinder (need subdomains first)
- Can't run nmap before httpx (need endpoints first)
- Can't scan same target twice (prevent redundancy)
- Can't finish_scan if coverage < 30%
- Can't focus_next_subdomain if no subdomains available

EPISODE TERMINATION:
- Agent calls finish_scan (done=True)
- Time limit reached (600 seconds, truncated=True)
- All possible actions exhausted (done=True)

SIMULATION:
All tool executions are instant lookups from pre-generated scenarios (no real execution).
This allows training at >1000 steps/second.

Performance target: >1000 env steps per second on CPU

Usage:
    env = ReconEnv(scenarios_path="data/scenarios/training.json")
    obs, info = env.reset()
    action = env.action_space.sample()
    obs, reward, done, truncated, info = env.step(action)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path


class ReconEnv(gym.Env):
    """
    Custom Gymnasium environment for reconnaissance workflow training.
    
    Simulates pentesting reconnaissance with subfinder, httpx, and nmap tools.
    """
    
    metadata = {"render_modes": ["human", "ansi"], "render_fps": 4}
    
    # Tool execution time (seconds)
    TOOL_TIMES = {
        'subfinder_passive': 10,
        'subfinder_active': 20,
        'httpx_basic': 3,  # per domain
        'httpx_detailed': 7,  # per domain
        'nmap_quick': 20,
        'nmap_full': 180,
        'nmap_service': 40
    }
    
    # Tool coverage (what % of ground truth it discovers)
    TOOL_COVERAGE = {
        'subfinder_passive': 0.6,  # 60% of subdomains
        'subfinder_active': 0.9,   # 90% of subdomains
        'httpx_basic': 0.8,        # 80% of endpoints
        'httpx_detailed': 1.0,     # 100% of endpoints + tech
        'nmap_quick': 0.7,         # 70% of ports (top 100)
        'nmap_full': 1.0,          # 100% of ports (all)
        'nmap_service': 0.9        # 90% service detection
    }
    
    def __init__(
        self,
        scenarios_path: str = "data/scenarios/training.json",
        max_episode_steps: int = 50,
        time_limit: int = 600,
        render_mode: Optional[str] = None
    ):
        """
        Initialize ReconEnv
        
        Args:
            scenarios_path: Path to JSON file with pre-generated scenarios
            max_episode_steps: Maximum number of actions per episode
            time_limit: Maximum time in seconds for episode
            render_mode: Rendering mode ("human" or "ansi")
        """
        super().__init__()
        
        self.render_mode = render_mode
        self.max_episode_steps = max_episode_steps
        self.time_limit = time_limit
        
        # Load scenarios
        self.scenarios = self._load_scenarios(scenarios_path)
        self.current_scenario = None
        self.current_scenario_idx = 0
        
        # Define action space (9 discrete actions)
        self.action_space = spaces.Discrete(9)
        
        # Define observation space (50-dimensional state)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(50,),
            dtype=np.float32
        )
        
        # Episode state
        self.step_count = 0
        self.time_elapsed = 0.0
        self.subdomains_found = set()
        self.endpoints_found = set()
        self.ports_found = set()
        self.tools_used = set()
        self.scanned_targets = set()  # Track to prevent redundancy
        self.current_subdomain_idx = 0
        self.scan_phase = 0  # 0=discovery, 1=probing, 2=scanning
        
        # Reward tracking
        self.episode_reward = 0.0
        self.redundant_scans = 0
    
    def _load_scenarios(self, scenarios_path: str) -> List[Dict[str, Any]]:
        """
        Load pre-generated scenarios from JSON file.
        
        TODO for Copilot:
        - Load JSON file
        - Validate structure
        - Return list of scenario dicts
        - Handle file not found gracefully
        """
        pass
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment to initial state.
        
        TODO for Copilot:
        - Call super().reset(seed=seed)
        - Select random scenario from self.scenarios
        - Reset all episode state variables
        - Return initial observation and info dict
        """
        super().reset(seed=seed)
        
        # TODO: Implement reset logic
        # Select random scenario
        # Reset counters
        # Return observation
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(
        self,
        action: int
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (0-8)
        
        Returns:
            observation: New state
            reward: Reward for this step
            done: Whether episode is complete
            truncated: Whether episode was truncated (time limit)
            info: Additional information
        
        TODO for Copilot:
        - Validate action is valid (check action mask)
        - Execute tool simulation
        - Update state (subdomains_found, endpoints_found, etc.)
        - Calculate reward
        - Check termination conditions
        - Return (obs, reward, done, truncated, info)
        """
        # Check if action is valid
        if not self.action_masks()[action]:
            # Invalid action, return negative reward
            reward = -20
            done = False
            truncated = False
            obs = self._get_observation()
            info = self._get_info()
            info['invalid_action'] = True
            return obs, reward, done, truncated, info
        
        # Execute action
        reward = 0.0
        done = False
        truncated = False
        
        # TODO: Implement action execution logic
        # Map action ID to tool execution
        # Update state based on tool results
        # Calculate rewards
        
        # Update step count and time
        self.step_count += 1
        
        # Check truncation (time limit or max steps)
        if self.step_count >= self.max_episode_steps:
            truncated = True
        if self.time_elapsed >= self.time_limit:
            truncated = True
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, done, truncated, info
    
    def _simulate_subfinder(self, mode: str) -> Dict[str, Any]:
        """
        Simulate subfinder execution with instant lookup.
        
        Args:
            mode: "passive" or "active"
        
        Returns:
            Dict with discovered subdomains
        
        TODO for Copilot:
        - Lookup subdomains from self.current_scenario
        - Apply coverage based on mode (60% passive, 90% active)
        - Return sampled subdomains
        - Update time_elapsed
        """
        pass
    
    def _simulate_httpx(self, mode: str, target_subdomains: List[str]) -> Dict[str, Any]:
        """
        Simulate httpx execution on target subdomains.
        
        Args:
            mode: "basic" or "detailed"
            target_subdomains: List of subdomains to scan
        
        Returns:
            Dict with discovered endpoints and technologies
        
        TODO for Copilot:
        - Lookup endpoints from scenario for each subdomain
        - Apply coverage based on mode (80% basic, 100% detailed)
        - For detailed mode, include technology detection
        - Calculate time: TOOL_TIMES[mode] * len(target_subdomains)
        - Return results
        """
        pass
    
    def _simulate_nmap(self, mode: str, target_endpoints: List[str]) -> Dict[str, Any]:
        """
        Simulate nmap execution on target endpoints.
        
        Args:
            mode: "quick", "full", or "service"
            target_endpoints: List of endpoints to scan
        
        Returns:
            Dict with discovered ports and services
        
        TODO for Copilot:
        - Lookup ports from scenario for each endpoint
        - Apply coverage based on mode
        - For service mode, include service detection
        - Calculate time based on mode
        - Return results
        """
        pass
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation (state representation).
        
        Returns:
            50-dimensional numpy array
        
        TODO for Copilot:
        - Create observation vector with:
          * subdomains_found (normalized)
          * endpoints_found (normalized)
          * open_ports (binary vector, top 100 ports)
          * tools_used (binary vector, 9 tools)
          * time_elapsed (normalized 0-1)
          * current_subdomain_idx (normalized)
          * scan_phase (one-hot encoded)
        - Ensure shape is (50,) and dtype is float32
        - All values should be in range [0, 1]
        """
        pass
    
    def _get_info(self) -> Dict[str, Any]:
        """
        Get additional information about current state.
        
        Returns:
            Info dictionary
        """
        return {
            'step': self.step_count,
            'time_elapsed': self.time_elapsed,
            'subdomains_found': len(self.subdomains_found),
            'endpoints_found': len(self.endpoints_found),
            'ports_found': len(self.ports_found),
            'tools_used': len(self.tools_used),
            'redundant_scans': self.redundant_scans,
            'scan_phase': ['discovery', 'probing', 'scanning'][self.scan_phase]
        }
    
    def action_masks(self) -> np.ndarray:
        """
        Get action mask (which actions are currently valid).
        
        Returns:
            Boolean array of shape (9,) where True = valid action
        
        TODO for Copilot:
        Implement action masking rules:
        1. Can't run httpx if no subdomains found
        2. Can't run nmap if no endpoints found
        3. Can't scan same target twice
        4. Can't finish_scan if coverage < 30%
        5. Can't focus_next_subdomain if no subdomains available
        6. Can't run expensive scans if insufficient time budget
        
        Return boolean numpy array
        """
        pass
    
    def render(self):
        """
        Render current environment state.
        
        TODO for Copilot:
        - If render_mode == "human", print formatted state
        - If render_mode == "ansi", return string representation
        - Show: step, time, findings, tools used, current phase
        """
        if self.render_mode == "human":
            print(f"\n{'='*60}")
            print(f"Step: {self.step_count}/{self.max_episode_steps}")
            print(f"Time: {self.time_elapsed:.1f}s/{self.time_limit}s")
            print(f"Subdomains: {len(self.subdomains_found)}")
            print(f"Endpoints: {len(self.endpoints_found)}")
            print(f"Ports: {len(self.ports_found)}")
            print(f"Tools used: {len(self.tools_used)}")
            print(f"Phase: {['Discovery', 'Probing', 'Scanning'][self.scan_phase]}")
            print(f"{'='*60}")
    
    def close(self):
        """Clean up resources"""
        pass
