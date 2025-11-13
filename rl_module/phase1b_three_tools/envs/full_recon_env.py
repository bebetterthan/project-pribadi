"""
PHASE 1B ENVIRONMENT: Subfinder + HTTPX + Nmap Full Reconnaissance
====================================================================

3-TOOL SEQUENTIAL environment for teaching RL agent to:
1. Choose optimal subfinder mode (subdomain discovery)
2. Choose optimal HTTPX mode (endpoint probing)
3. CONDITIONALLY choose nmap mode (service detection) - WHEN to use!

KEY LEARNING: "WHEN should I use nmap?" (not just "how")

DESIGN PHILOSOPHY (Lessons from Phase 1A Success):
- Reward V2: POSITIVE-DOMINANT (encourage trying!)
- NO harsh penalties, NO time punishment
- Timeout = 0 (not negative!)
- Clear reward signals (discovery, completion, strategic, efficiency)
- Rich state (40 dims) - agent sees full context
- Action masking (sequential workflow)

EPISODE FLOW:
reset() → Subfinder → HTTPX → Nmap (conditional) → Terminated
   ↓        ↓          ↓         ↓
State[40] Action 0-2  Action 3-5  Action 6-8
         (discovery)  (probing)   (services)

STATE SPACE: 40 dimensions (vs 22 in Phase 1A)
ACTION SPACE: 9 discrete (3+3+3 tools)
REWARD: V2 positive-dominant (4 components)

Author: Agent-P RL Team  
Date: 2025-11-13
Phase: 1B (3-tool conditional learning)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path


class FullReconEnv(gym.Env):
    """
    Phase 1B: 3-tool sequential reconnaissance with conditional nmap usage.
    
    Goal: Teach agent WHEN to use nmap (conditional tool intelligence).
    
    STATE SPACE (40 dimensions):
    
        Group 1 - Target Characteristics (8 dims):
        [0] domain_complexity: 0-1 (normalized subdomain count)
        [1] subdomain_count: 0-1 (normalized current subdomains)
        [2] live_endpoint_count: 0-1 (normalized live endpoints found)
        [3] scan_coverage: 0-1 (estimated coverage %)
        [4] time_elapsed: 0-1 (normalized time usage)
        [5] critical_found: 0-1 (found high-value targets?)
        [6] current_phase: 0/1/2 (subfinder/httpx/nmap)
        [7] phase_progress: 0-1 (progress in current phase)
        
        Group 2 - Tool Usage History (12 dims):
        [8] subfinder_passive_used: 0/1
        [9] subfinder_active_used: 0/1
        [10] subfinder_comprehensive_used: 0/1
        [11] httpx_quick_used: 0/1
        [12] httpx_thorough_used: 0/1
        [13] httpx_comprehensive_used: 0/1
        [14] nmap_quick_used: 0/1
        [15] nmap_full_used: 0/1
        [16] nmap_service_used: 0/1
        [17] total_tools_used: 0-1 (normalized count)
        [18] subfinder_time: 0-1 (normalized time spent)
        [19] httpx_time: 0-1 (normalized time spent)
        
        Group 3 - Discovery Metrics (10 dims):
        [20] total_subdomains: 0-1 (normalized)
        [21] high_value_subdomains: 0-1 (normalized)
        [22] live_endpoints: 0-1 (normalized)
        [23] technologies_found: 0-1 (normalized tech count)
        [24] open_ports: 0-1 (normalized port count)
        [25] critical_services: 0-1 (normalized critical count)
        [26] service_versions: 0-1 (normalized version count)
        [27] discovery_rate: 0-1 (finds per second)
        [28] high_value_ratio: 0-1 (critical / total)
        [29] httpx_accuracy: 0-1 (live / checked)
        
        Group 4 - Nmap-Specific Context (10 dims):
        [30] has_infrastructure_ports: 0/1 (DB/SSH/mail present?)
        [31] has_custom_ports: 0/1 (4000+ range?)
        [32] port_diversity: 0-1 (unique ports / potential)
        [33] nmap_value_estimate: 0-1 (estimated nmap usefulness)
        [34] web_only_target: 0/1 (only 80/443/8080?)
        [35] database_ports_found: 0/1 (3306/5432/6379?)
        [36] admin_ports_found: 0/1 (8443/9090?)
        [37] scannable_ports: 0-1 (normalized count)
        [38] nmap_time: 0-1 (normalized time if used)
        [39] nmap_expected_value: 0-1 (reward estimate if scan)
    
    ACTION SPACE (9 discrete):
    
        Phase 1 - Subfinder (Subdomain Discovery):
        0: subfinder_passive (fast, ~5-10s, low coverage)
        1: subfinder_active (medium, ~15-30s, good coverage)
        2: subfinder_comprehensive (slow, ~30-60s, best coverage)
        
        Phase 2 - HTTPX (Endpoint Probing):
        3: httpx_basic (fast, ~10-20s, basic info)
        4: httpx_thorough (medium, ~30-60s, detailed info)
        5: httpx_comprehensive (slow, ~60-120s, all info)
        
        Phase 3 - Nmap (Service Detection) - CONDITIONAL!:
        6: nmap_quick (fast, ~30-60s, basic ports)
        7: nmap_full (medium, ~60-120s, all ports)
        8: nmap_service (slow, ~120-300s, versions+scripts)
    
    ACTION MASKING (Sequential Workflow):
        Initial: Only 0-2 available (subfinder)
        After subfinder: Only 3-5 available (httpx)
        After httpx: Only 6-8 available (nmap)
        After nmap OR timeout: Episode ends
    
    REWARD FUNCTION V2 (POSITIVE-DOMINANT - Learned from Phase 1A!):
    
        Component 1: Discovery Rewards (ALL POSITIVE):
        - +20 per new subdomain
        - +40 per high-value subdomain (admin/api/db)
        - +15 per new live endpoint
        - +30 per new open port
        - +50 per critical service (SSH/DB/mail)
        - +25 per service version detected (nmap!)
        - +10 per technology detected
        
        Component 2: Completion Bonus (GOAL INCENTIVE):
        - +300 if >80% coverage achieved
        - +200 if >70% coverage
        - +150 if >60% coverage
        - +100 if >50% coverage
        - 0 otherwise (NO PENALTY!)
        
        Component 3: Strategic Bonus (INTELLIGENT DECISIONS):
        - +80 if used nmap on infrastructure (HIGH value decision!)
        - +40 if SKIPPED nmap on web-only (smart efficiency!)
        - +60 if correct sequential tool usage
        - +50 if high efficiency (many finds per time)
        - 0 if suboptimal (NO PENALTY!)
        
        Component 4: Efficiency Bonus (OPTIONAL REWARD):
        - +100 if total time <90s
        - +60 if total time <120s
        - +30 if total time <180s
        - 0 if >180s (NO TIME PENALTY!)
        
        CRITICAL: Timeout = 0 reward (not negative!)
        Philosophy: Encourage exploration, NOT punish trying!
    
    EXAMPLE SCENARIOS:
    
        Web-Only Target (e.g., SaaS startup):
        - Ports: 80, 443, 8080
        - Optimal: Subfinder comprehensive → HTTPX full → SKIP nmap
        - Reward: 480 (efficient)
        - If use nmap: 320 (wasted time, no gain)
        
        Infrastructure Target (e.g., database cluster):
        - Ports: 80, 443, 3306, 5432, 6379
        - Optimal: Subfinder active → HTTPX thorough → Nmap service
        - Reward: 820 (comprehensive + versions!)
        - If skip nmap: 320 (missed critical services)
        
        Hybrid Target (e.g., web + monitoring):
        - Ports: 80, 443, 9090
        - Optimal: Subfinder comprehensive → HTTPX full → Nmap quick
        - Reward: 580 (balanced)
        - Strategic decision: Quick scan on Prometheus worth it!
    """
    
    metadata = {"render_modes": ["human"], "render_fps": 1}
    
    def __init__(
        self,
        scenarios_path: str = "data/phase1b_train.json",
        time_budget: float = 300.0,  # 5 min for 3 tools
        max_steps: int = 3,  # Subfinder + HTTPX + Nmap
        render_mode: Optional[str] = None,
    ):
        """
        Initialize Phase 1B environment.
        
        Args:
            scenarios_path: Path to scenario JSON file
            time_budget: Maximum episode duration (seconds)
            max_steps: Maximum actions per episode (3 for 3 tools)
            render_mode: Rendering mode for visualization
        """
        super().__init__()
        
        self.scenarios_path = Path(scenarios_path)
        self.time_budget = time_budget
        self.max_steps = max_steps
        self.render_mode = render_mode
        
        # State space: 40 dimensions (continuous)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(40,),
            dtype=np.float32
        )
        
        # Action space: 10 discrete actions (3 tools × 3 modes + SKIP)
        self.action_space = spaces.Discrete(10)
        
        # Action definitions
        self.action_names = [
            "subfinder_passive",      # 0
            "subfinder_active",       # 1
            "subfinder_comprehensive", # 2
            "httpx_basic",            # 3
            "httpx_thorough",         # 4
            "httpx_comprehensive",    # 5
            "nmap_quick",             # 6
            "nmap_full",              # 7
            "nmap_service",           # 8
            "skip_nmap",              # 9 - TERMINATE without nmap (conditional!)
        ]
        
        # Load scenarios
        self._load_scenarios()
        
        # Episode state
        self.current_scenario = None
        self.current_scenario_idx = None
        self.step_count = 0
        self.time_elapsed = 0.0
        self.current_phase = 0  # 0=subfinder, 1=httpx, 2=nmap
        self.terminated = False
        self.truncated = False
        
        # Tool results tracking
        self.tools_used = {
            'subfinder': {'used': False, 'mode': None, 'time': 0, 'results': {}},
            'httpx': {'used': False, 'mode': None, 'time': 0, 'results': {}},
            'nmap': {'used': False, 'mode': None, 'time': 0, 'results': {}},
        }
        
        # Discovery tracking
        self.discovered = {
            'subdomains': set(),
            'high_value_subdomains': set(),
            'live_endpoints': set(),
            'technologies': set(),
            'open_ports': set(),
            'critical_services': set(),
            'service_versions': {},
        }
        
        # Reward tracking
        self.total_reward = 0.0
        self.reward_breakdown = {
            'discovery': 0.0,
            'completion': 0.0,
            'strategic': 0.0,
            'efficiency': 0.0,
        }
        
    def _load_scenarios(self):
        """Load scenarios from JSON file"""
        if not self.scenarios_path.exists():
            raise FileNotFoundError(f"Scenarios file not found: {self.scenarios_path}")
        
        with open(self.scenarios_path, 'r') as f:
            data = json.load(f)
        
        self.scenarios = data['scenarios']
        self.num_scenarios = len(self.scenarios)
        
        print(f"[LOADED] {self.num_scenarios} scenarios from {self.scenarios_path}")
    
    def action_masks(self) -> np.ndarray:
        """
        Get valid action mask for current phase (sequential workflow).
        
        Returns:
            Boolean mask: 1=allowed, 0=blocked
        """
        mask = np.zeros(10, dtype=np.int8)
        
        if self.current_phase == 0:
            # Subfinder phase: Only actions 0-2
            mask[0:3] = 1
        elif self.current_phase == 1:
            # HTTPX phase: Only actions 3-5
            mask[3:6] = 1
        elif self.current_phase == 2:
            # Nmap phase: Actions 6-8 OR skip (action 9)
            mask[6:10] = 1  # Allow nmap_quick, nmap_full, nmap_service, skip_nmap
        
        return mask
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment for new episode.
        
        Args:
            seed: Random seed
            options: Optional reset parameters
        
        Returns:
            observation: Initial state (40-dim)
            info: Episode metadata
        """
        super().reset(seed=seed)
        
        # Select random scenario
        self.current_scenario_idx = self.np_random.integers(0, self.num_scenarios)
        self.current_scenario = self.scenarios[self.current_scenario_idx]
        
        # Reset episode state
        self.step_count = 0
        self.time_elapsed = 0.0
        self.current_phase = 0  # Start with subfinder
        self.terminated = False
        self.truncated = False
        
        # Reset tool tracking
        self.tools_used = {
            'subfinder': {'used': False, 'mode': None, 'time': 0, 'results': {}},
            'httpx': {'used': False, 'mode': None, 'time': 0, 'results': {}},
            'nmap': {'used': False, 'mode': None, 'time': 0, 'results': {}},
        }
        
        # Reset discovery
        self.discovered = {
            'subdomains': set(),
            'high_value_subdomains': set(),
            'live_endpoints': set(),
            'technologies': set(),
            'open_ports': set(),
            'critical_services': set(),
            'service_versions': {},
        }
        
        # Reset rewards
        self.total_reward = 0.0
        self.reward_breakdown = {
            'discovery': 0.0,
            'completion': 0.0,
            'strategic': 0.0,
            'efficiency': 0.0,
        }
        
        # Get initial observation
        obs = self._get_observation()
        
        info = {
            'scenario_id': self.current_scenario['id'],
            'scenario_name': self.current_scenario['name'],
            'scenario_type': self.current_scenario['scenario_type'],
            'optimal_reward': self.current_scenario['rewards']['optimal'],
            'action_masks': self.action_masks(),
        }
        
        return obs, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute action and return results.
        
        Args:
            action: Action index (0-8)
        
        Returns:
            observation: New state (40-dim)
            reward: Reward for this action
            terminated: Episode finished successfully
            truncated: Episode ended early (timeout/error)
            info: Step metadata
        """
        # Handle numpy array actions from PPO
        if isinstance(action, np.ndarray):
            action = int(action.item())
        else:
            action = int(action)
        
        # Validate action
        action_mask = self.action_masks()
        if not action_mask[action]:
            # Invalid action for current phase
            return (
                self._get_observation(),
                -10.0,  # Small penalty for invalid action
                True,  # Terminate
                False,
                {'error': 'Invalid action for current phase'}
            )
        
        self.step_count += 1
        action_name = self.action_names[action]
        
        # Execute tool action
        reward, tool_results = self._execute_action(action, action_name)
        
        # Check termination conditions
        self._check_termination()
        
        # Get new observation
        obs = self._get_observation()
        
        # Build info dict
        info = {
            'step': self.step_count,
            'action': action_name,
            'phase': ['subfinder', 'httpx', 'nmap'][self.current_phase],
            'time_elapsed': self.time_elapsed,
            'reward_breakdown': self.reward_breakdown.copy(),
            'total_reward': self.total_reward,
            'action_masks': self.action_masks(),
        }
        
        if self.terminated or self.truncated:
            info['episode'] = {
                'total_reward': self.total_reward,
                'steps': self.step_count,
                'time': self.time_elapsed,
                'discoveries': {
                    'subdomains': len(self.discovered['subdomains']),
                    'live_endpoints': len(self.discovered['live_endpoints']),
                    'open_ports': len(self.discovered['open_ports']),
                    'services': len(self.discovered['critical_services']),
                },
            }
            
            # Add metrics expected by training script (at top level for vectorized env access)
            info['total_subdomains'] = len(self.discovered['subdomains'])
            info['total_live'] = len(self.discovered['live_endpoints'])
            info['total_ports'] = len(self.discovered['open_ports'])
            info['total_services'] = len(self.discovered['critical_services'])
            info['nmap_used'] = 1 if self.tools_used['nmap']['used'] else 0
        
        return obs, reward, self.terminated, self.truncated, info
    
    def _execute_action(self, action: int, action_name: str) -> Tuple[float, Dict]:
        """
        Execute tool action and calculate reward.
        
        Args:
            action: Action index
            action_name: Action name
        
        Returns:
            reward: Reward for this action
            results: Tool execution results
        """
        results = {}
        
        # Determine which tool
        if action <= 2:
            # Subfinder
            tool = 'subfinder'
            mode = ['passive', 'active', 'comprehensive'][action]
            results = self._execute_subfinder(mode)
            self.current_phase = 1  # Move to HTTPX phase
            
        elif action <= 5:
            # HTTPX
            tool = 'httpx'
            mode = ['basic', 'thorough', 'comprehensive'][action - 3]
            results = self._execute_httpx(mode)
            self.current_phase = 2  # Move to Nmap phase
            
        elif action <= 8:
            # Nmap
            tool = 'nmap'
            mode = ['quick', 'full', 'service'][action - 6]
            results = self._execute_nmap(mode)
            self.terminated = True  # End after nmap
            
        else:  # action == 9
            # Skip Nmap - CONDITIONAL TERMINATION!
            tool = 'skip'
            mode = 'terminate'
            results = {
                'time': 0,  # No time cost for skipping
                'decision': 'skip_nmap',
                'reason': 'Agent decided to skip nmap phase'
            }
            self.terminated = True  # End without nmap
        
        # Update tool tracking (skip doesn't have tools_used entry)
        if tool != 'skip':
            self.tools_used[tool]['used'] = True
            self.tools_used[tool]['mode'] = mode
            self.tools_used[tool]['time'] = results.get('time', 0)
            self.tools_used[tool]['results'] = results
        
        self.time_elapsed += results.get('time', 0)
        
        # Calculate reward
        reward = self._calculate_reward(tool, mode, results)
        self.total_reward += reward
        
        return reward, results
    
    def _execute_subfinder(self, mode: str) -> Dict:
        """Execute subfinder scan (from pre-computed results)"""
        scenario_results = self.current_scenario['tool_results']['subfinder']
        
        # Get subdomains based on mode
        all_subdomains = scenario_results['subdomains']
        
        if mode == 'passive':
            # Get 40-60% of subdomains
            ratio = np.random.uniform(0.4, 0.6)
            count = int(len(all_subdomains) * ratio)
            subdomains = all_subdomains[:count]
            time_taken = scenario_results['execution_time_seconds'] * 0.3
            
        elif mode == 'active':
            # Get 70-85% of subdomains
            ratio = np.random.uniform(0.7, 0.85)
            count = int(len(all_subdomains) * ratio)
            subdomains = all_subdomains[:count]
            time_taken = scenario_results['execution_time_seconds'] * 0.6
            
        else:  # comprehensive
            # Get 95-100% of subdomains
            ratio = np.random.uniform(0.95, 1.0)
            count = int(len(all_subdomains) * ratio)
            subdomains = all_subdomains[:count]
            time_taken = scenario_results['execution_time_seconds']
        
        # Update discoveries
        self.discovered['subdomains'].update(subdomains)
        
        # Identify high-value subdomains
        high_value_keywords = ['admin', 'api', 'db', 'database', 'mysql', 'postgres', 
                               'redis', 'mail', 'smtp', 'vpn', 'backup', 'panel']
        for subdomain in subdomains:
            if any(kw in subdomain.lower() for kw in high_value_keywords):
                self.discovered['high_value_subdomains'].add(subdomain)
        
        return {
            'subdomains_found': len(subdomains),
            'high_value_found': len([s for s in subdomains 
                                    if any(kw in s.lower() for kw in high_value_keywords)]),
            'time': time_taken,
            'mode': mode,
        }
    
    def _execute_httpx(self, mode: str) -> Dict:
        """Execute HTTPX probe (from pre-computed results)"""
        scenario_results = self.current_scenario['tool_results']['httpx']
        
        # Get endpoints based on mode
        all_endpoints = scenario_results['endpoints']
        
        if mode == 'basic':
            # Quick probe, 80-90% of live endpoints
            ratio = np.random.uniform(0.8, 0.9)
            count = int(len(all_endpoints) * ratio)
            endpoints = all_endpoints[:count]
            time_taken = scenario_results['execution_time_seconds'] * 0.4
            tech_detail = 0.5  # Basic tech detection
            
        elif mode == 'thorough':
            # Thorough probe, 90-95% accuracy
            ratio = np.random.uniform(0.9, 0.95)
            count = int(len(all_endpoints) * ratio)
            endpoints = all_endpoints[:count]
            time_taken = scenario_results['execution_time_seconds'] * 0.7
            tech_detail = 0.8  # Good tech detection
            
        else:  # comprehensive
            # Full probe, 95-100% accuracy
            ratio = np.random.uniform(0.95, 1.0)
            count = int(len(all_endpoints) * ratio)
            endpoints = all_endpoints[:count]
            time_taken = scenario_results['execution_time_seconds']
            tech_detail = 1.0  # All tech detected
        
        # Update discoveries
        for endpoint in endpoints:
            self.discovered['live_endpoints'].add(endpoint['url'])
            # Add technologies
            if 'tech_stack' in endpoint:
                tech_count = int(len(endpoint['tech_stack']) * tech_detail)
                self.discovered['technologies'].update(endpoint['tech_stack'][:tech_count])
        
        return {
            'live_endpoints_found': len(endpoints),
            'technologies_found': len(self.discovered['technologies']),
            'time': time_taken,
            'mode': mode,
        }
    
    def _execute_nmap(self, mode: str) -> Dict:
        """Execute nmap scan (from pre-computed results)"""
        scenario_results = self.current_scenario['tool_results']['nmap']
        
        # Get services based on mode
        all_services = scenario_results['services']
        
        if mode == 'quick':
            # Quick scan: top 100 ports, no versions
            ports_found = min(len(all_services), int(len(all_services) * 0.6))
            services = all_services[:ports_found]
            time_taken = scenario_results['execution_time_seconds'] * 0.3
            get_versions = False
            
        elif mode == 'full':
            # Full scan: all 1000 ports, some versions
            ports_found = int(len(all_services) * 0.9)
            services = all_services[:ports_found]
            time_taken = scenario_results['execution_time_seconds'] * 0.6
            get_versions = True
            version_rate = 0.5
            
        else:  # service
            # Service detection: all ports + versions + scripts
            services = all_services
            time_taken = scenario_results['execution_time_seconds']
            get_versions = True
            version_rate = 0.95
        
        # Update discoveries
        critical_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017]
        
        for service in services:
            port = service['port']
            self.discovered['open_ports'].add(port)
            
            # Critical services
            if port in critical_ports:
                service_name = service.get('service', 'unknown')
                self.discovered['critical_services'].add(f"{service_name}:{port}")
                
                # Service versions
                if get_versions and service.get('version') and np.random.random() < version_rate:
                    self.discovered['service_versions'][port] = service['version']
        
        return {
            'ports_found': len(services),
            'ports_list': [s['port'] for s in services],  # Add port list for reward calculation
            'critical_services': len([s for s in services if s['port'] in critical_ports]),
            'versions_detected': len(self.discovered['service_versions']),
            'time': time_taken,
            'mode': mode,
        }
    
    def _calculate_reward(self, tool: str, mode: str, results: Dict) -> float:
        """
        Calculate reward using V2 positive-dominant philosophy.
        
        Learned from Phase 1A success:
        - ALL components positive or zero
        - NO harsh penalties
        - Timeout = 0 (not negative!)
        - Encourage exploration!
        
        Args:
            tool: Tool name
            mode: Tool mode
            results: Execution results
        
        Returns:
            Total reward for this action
        """
        reward = 0.0
        
        # Component 1: Discovery Rewards - V16 ULTIMATE (V13 EXACT + high-value amplification)
        if tool == 'subfinder':
            subdomains_found = results.get('subdomains_found', 0)
            high_value_found = results.get('high_value_found', 0)
            
            reward += subdomains_found * 43  # V13 EXACT value - proven optimal
            reward += high_value_found * 95  # BOOST high-value for quality focus
            
            self.reward_breakdown['discovery'] += reward
            
        elif tool == 'httpx':
            live_found = results.get('live_endpoints_found', 0)
            tech_found = results.get('technologies_found', 0)
            
            reward += live_found * 32  # V13 EXACT - proven optimal
            reward += tech_found * 22  # V13 EXACT - proven optimal
            
            self.reward_breakdown['discovery'] += reward
            
        elif tool == 'nmap':
            ports_found = results.get('ports_found', 0)
            critical_services = results.get('critical_services', 0)
            versions = results.get('versions_detected', 0)
            
            # CONDITIONAL REWARDS - V16 ULTIMATE (V13 base + SERVICE AMPLIFICATION)
            # This makes skipping nmap more attractive on web-only targets
            web_ports = [80, 443, 8080, 8443, 3000, 5000]
            ports_list = results.get('ports_list', [])
            web_port_count = len([p for p in ports_list if p in web_ports])
            infra_port_count = ports_found - web_port_count
            
            # V13 EXACT for ports, BOOST for services (key differentiator!)
            reward += web_port_count * 22  # V13 EXACT
            reward += infra_port_count * 65  # V13 EXACT  
            reward += critical_services * 125  # BOOSTED! Services are gold!
            reward += versions * 60  # BOOSTED! Version detection valuable!
            
            self.reward_breakdown['discovery'] += reward
            
        elif tool == 'skip':
            # Skip nmap = 0 discovery reward (no new findings)
            # But strategic bonus will reward if this was right decision!
            pass
        
        # Component 2: Completion Bonus - AMPLIFIED 1.8x (ONLY after nmap - force 3-tool workflow!)
        if tool == 'nmap':
            coverage = self._calculate_coverage()
            
            if coverage > 0.8:
                bonus = 540  # 300 × 1.8
            elif coverage > 0.7:
                bonus = 360  # 200 × 1.8
            elif coverage > 0.6:
                bonus = 270  # 150 × 1.8
            elif coverage > 0.5:
                bonus = 180  # 100 × 1.8
            else:
                bonus = 0  # NO PENALTY!
            
            reward += bonus
            self.reward_breakdown['completion'] += bonus
        elif self.terminated and not self.tools_used['nmap']['used']:
            # Terminated without nmap = NO completion bonus!
            # This encourages completing all 3 tools
            pass
        
        # Component 3: Strategic Bonus (ONLY at episode end!)
        # Strategic decisions only matter when workflow is complete
        if tool == 'nmap' or self.terminated:
            strategic_bonus = self._calculate_strategic_bonus()
            reward += strategic_bonus
            self.reward_breakdown['strategic'] += strategic_bonus
        
        # Component 4: Efficiency Bonus - V15 HYBRID (V13 base)
        if tool == 'nmap':
            if self.time_elapsed < 90:
                efficiency_bonus = 227  # V13: 216, slight boost
            elif self.time_elapsed < 120:
                efficiency_bonus = 60
            elif self.time_elapsed < 180:
                efficiency_bonus = 30
            else:
                efficiency_bonus = 0  # NO PENALTY!
            
            reward += efficiency_bonus
            self.reward_breakdown['efficiency'] += efficiency_bonus
        elif self.terminated and not self.tools_used['nmap']['used']:
            # Terminated without nmap = NO efficiency bonus!
            # This encourages completing all 3 tools
            pass
        
        return reward
    
    def _calculate_strategic_bonus(self) -> float:
        """
        Calculate strategic decision bonus - VERSION 3 (AMPLIFIED BONUSES)
        
        PROBLEM IDENTIFIED:
        Previous bonuses (+40 to +80) were too small compared to discovery rewards (~250-300).
        Agent couldn't learn conditional tool usage because signal-to-noise ratio was too low.
        
        SOLUTION:
        Amplify strategic bonuses by 5-10x to make them DOMINANT learning signal.
        Strategic bonuses should now be 40-70% of total episode reward.
        
        NEW STRATEGIC BONUS VALUES:
        
        Infrastructure targets (many services, databases, admin ports):
        - Service mode (action 8): +400 (was +80) - CRITICAL for infrastructure!
        - Full mode (action 7): +300 (was 0) - Also valuable
        - Quick mode (action 6): +100 (was 0) - Acceptable compromise
        
        Web-only targets (only HTTP/HTTPS, no backend services):
        - Skip nmap: +200 (was +40) - Smart efficiency!
        - Quick mode: +50 (was 0) - Fast at least
        - Service/Full mode: 0 bonus - Waste of time but no penalty
        
        Hybrid targets (mix of web and backend):
        - Selective nmap on high-value: +300 (NEW!) - Smart selective scanning!
        - Service mode on all: +150 (was +80) - Thorough but not efficient
        - Quick mode: +100 (was 0) - Acceptable compromise
        
        EXPECTED RESULTS:
        - Quick mode everywhere: ~300 total (discovery only)
        - Smart conditional usage: ~700 total (discovery + strategic)
        - Difference: 133% improvement (CRYSTAL CLEAR signal!)
        """
        bonus = 0.0
        
        # Check if nmap was used and what mode
        nmap_used = self.tools_used['nmap']['used']
        nmap_mode = self.tools_used['nmap']['mode'] if nmap_used else None
        
        # Get scenario metadata
        metadata = self.current_scenario['metadata']
        port_list = metadata['port_list']
        
        # Identify target type based on ports
        web_ports = [80, 443, 8080, 8443, 3000, 5000]
        infrastructure_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017, 9200, 9092]
        
        has_web = any(p in web_ports for p in port_list)
        has_infra = any(p in infrastructure_ports for p in port_list)
        infra_count = len([p for p in port_list if p in infrastructure_ports])
        web_only = has_web and not has_infra
        infra_heavy = infra_count >= 2  # 2+ infrastructure ports = infrastructure target
        
        # SCENARIO TYPE 1: INFRASTRUCTURE HEAVY - V16 ULTIMATE (Maximize nmap value!)
        if infra_heavy:
            if nmap_used:
                if nmap_mode == 'service':
                    # OPTIMAL: Service detection on infrastructure! ✅
                    bonus += 1500  # V13 proven value
                    # EXTRA: Perfect mode selection bonus!
                    if infra_count >= 3:
                        bonus += 400  # Reward optimal decision on complex targets!
                elif nmap_mode == 'full':
                    # GOOD: Full scan also valuable on infrastructure
                    bonus += 1200  # V13 proven value
                elif nmap_mode == 'quick':
                    # ACCEPTABLE: Quick mode is okay compromise
                    bonus += 600  # Increased from 360
            else:
                # BAD: Skipping nmap on infrastructure is WRONG decision!
                # Stronger penalty to discourage skipping
                bonus -= 400  # Increased from 270 - Stronger signal
                
        # SCENARIO TYPE 2: WEB ONLY - REBALANCED V12 (Nmap LOW value!)
        elif web_only:
            if not nmap_used:
                # OPTIMAL: Smart skip on web-only target! ✅
                # HIGH REWARD: Clear signal that skipping is correct decision!
                bonus += 1000  # Reduced from 1260 - Still optimal but less dominant
            elif nmap_mode == 'quick':
                # ACCEPTABLE: Quick mode is fast at least
                bonus += 120  # Increased from 90 - Slightly more acceptable
            else:
                # WASTE: Using service/full mode on web-only is inefficient
                # Add time cost as implicit penalty (no positive bonus)
                bonus += 0  # No bonus for wasteful scanning
                
        # SCENARIO TYPE 3: HYBRID - REBALANCED V12 (Conditional nmap usage!)
        elif has_infra and nmap_used:
            # Check if agent was selective (focused on high-value subdomains)
            high_value_count = len(self.discovered['high_value_subdomains'])
            total_subdomains = len(self.discovered['subdomains'])
            
            if high_value_count > 0 and total_subdomains > 0:
                selectivity_ratio = high_value_count / total_subdomains
                
                if selectivity_ratio > 0.3 and nmap_mode == 'service':
                    # OPTIMAL: Selective service scanning on high-value targets! ✅
                    bonus += 1200  # Increased from 720 - Encourage hybrid nmap
                elif nmap_mode == 'service':
                    # GOOD: Service mode on hybrid target
                    bonus += 750  # Increased from 450
                elif nmap_mode == 'quick':
                    # ACCEPTABLE: Quick mode is okay compromise
                    bonus += 450  # Increased from 270
            else:
                # Default: Used nmap on mixed target (GOOD)
                bonus += 600  # Increased from 360
        
        # ADDITIONAL BONUSES (smaller, secondary signals)
        
        # 3-TOOL WORKFLOW COMPLETION BONUS - V16 ULTIMATE (MASSIVE BOOST!)
        # CONDITIONAL: Only give bonus if nmap was APPROPRIATE!
        # Don't force 3 tools on web-only targets!
        if (self.tools_used['subfinder']['used'] and 
            self.tools_used['httpx']['used'] and 
            self.tools_used['nmap']['used'] and
            infra_heavy):  # Only on infrastructure targets!
            bonus += 2600  # MASSIVE! V13=2000, V14=2300, V16=2600 BREAKTHROUGH!
        
        # Efficiency bonus (high discovery rate) - V16 ULTIMATE - ONLY if nmap used!
        if nmap_used and len(self.discovered['subdomains']) > 0:
            finds_per_second = len(self.discovered['subdomains']) / max(self.time_elapsed, 1)
            if finds_per_second > 1.0:
                bonus += 144  # V13 EXACT
            
            # NEW: Consistency bonus for balanced discoveries
            if (len(self.discovered['subdomains']) > 8 and 
                len(self.discovered['live_endpoints']) > 5 and
                len(self.discovered['open_ports']) > 2):
                bonus += 250  # BALANCE bonus - reward comprehensive recon!
        
        return bonus
    
    def _calculate_coverage(self) -> float:
        """Calculate discovery coverage (0-1)"""
        metadata = self.current_scenario['metadata']
        
        # Calculate coverage components
        subdomain_coverage = len(self.discovered['subdomains']) / max(metadata['total_subdomains'], 1)
        endpoint_coverage = len(self.discovered['live_endpoints']) / max(metadata['live_endpoints'], 1)
        port_coverage = len(self.discovered['open_ports']) / max(metadata['open_ports'], 1)
        
        # Weighted average
        coverage = (subdomain_coverage * 0.4 + 
                   endpoint_coverage * 0.3 + 
                   port_coverage * 0.3)
        
        return min(coverage, 1.0)
    
    def _check_termination(self):
        """Check if episode should terminate"""
        # Terminate after nmap (3 steps total)
        if self.step_count >= self.max_steps:
            self.terminated = True
        
        # Truncate on timeout
        if self.time_elapsed >= self.time_budget:
            self.truncated = True
    
    def _get_observation(self) -> np.ndarray:
        """
        Build 40-dimensional observation vector.
        
        Returns:
            40-dim numpy array (all values 0-1)
        """
        obs = np.zeros(40, dtype=np.float32)
        
        metadata = self.current_scenario['metadata']
        
        # Group 1: Target Characteristics (8 dims)
        obs[0] = min(metadata['total_subdomains'] / 30.0, 1.0)  # domain_complexity
        obs[1] = min(len(self.discovered['subdomains']) / 30.0, 1.0)  # subdomain_count
        obs[2] = min(len(self.discovered['live_endpoints']) / 25.0, 1.0)  # live_endpoint_count
        obs[3] = self._calculate_coverage()  # scan_coverage
        obs[4] = min(self.time_elapsed / self.time_budget, 1.0)  # time_elapsed
        obs[5] = 1.0 if len(self.discovered['high_value_subdomains']) > 0 else 0.0  # critical_found
        obs[6] = self.current_phase / 2.0  # current_phase (0/1/2 → 0/0.5/1.0)
        obs[7] = self.step_count / self.max_steps  # phase_progress
        
        # Group 2: Tool Usage History (12 dims)
        obs[8] = 1.0 if self.tools_used['subfinder']['used'] and self.tools_used['subfinder']['mode'] == 'passive' else 0.0
        obs[9] = 1.0 if self.tools_used['subfinder']['used'] and self.tools_used['subfinder']['mode'] == 'active' else 0.0
        obs[10] = 1.0 if self.tools_used['subfinder']['used'] and self.tools_used['subfinder']['mode'] == 'comprehensive' else 0.0
        obs[11] = 1.0 if self.tools_used['httpx']['used'] and self.tools_used['httpx']['mode'] == 'basic' else 0.0
        obs[12] = 1.0 if self.tools_used['httpx']['used'] and self.tools_used['httpx']['mode'] == 'thorough' else 0.0
        obs[13] = 1.0 if self.tools_used['httpx']['used'] and self.tools_used['httpx']['mode'] == 'comprehensive' else 0.0
        obs[14] = 1.0 if self.tools_used['nmap']['used'] and self.tools_used['nmap']['mode'] == 'quick' else 0.0
        obs[15] = 1.0 if self.tools_used['nmap']['used'] and self.tools_used['nmap']['mode'] == 'full' else 0.0
        obs[16] = 1.0 if self.tools_used['nmap']['used'] and self.tools_used['nmap']['mode'] == 'service' else 0.0
        obs[17] = min(sum(1 for t in self.tools_used.values() if t['used']) / 3.0, 1.0)  # total_tools_used
        obs[18] = min(self.tools_used['subfinder']['time'] / 60.0, 1.0)  # subfinder_time
        obs[19] = min(self.tools_used['httpx']['time'] / 120.0, 1.0)  # httpx_time
        
        # Group 3: Discovery Metrics (10 dims)
        obs[20] = min(len(self.discovered['subdomains']) / 30.0, 1.0)  # total_subdomains
        obs[21] = min(len(self.discovered['high_value_subdomains']) / 10.0, 1.0)  # high_value_subdomains
        obs[22] = min(len(self.discovered['live_endpoints']) / 25.0, 1.0)  # live_endpoints
        obs[23] = min(len(self.discovered['technologies']) / 10.0, 1.0)  # technologies_found
        obs[24] = min(len(self.discovered['open_ports']) / 20.0, 1.0)  # open_ports
        obs[25] = min(len(self.discovered['critical_services']) / 10.0, 1.0)  # critical_services
        obs[26] = min(len(self.discovered['service_versions']) / 10.0, 1.0)  # service_versions
        obs[27] = min(len(self.discovered['subdomains']) / max(self.time_elapsed, 1) / 5.0, 1.0)  # discovery_rate
        obs[28] = len(self.discovered['high_value_subdomains']) / max(len(self.discovered['subdomains']), 1)  # high_value_ratio
        obs[29] = len(self.discovered['live_endpoints']) / max(len(self.discovered['subdomains']), 1)  # httpx_accuracy
        
        # Group 4: Nmap-Specific Context (10 dims)
        port_list = metadata['port_list']
        infrastructure_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017]
        web_ports = [80, 443, 8080, 8443, 3000]
        
        obs[30] = 1.0 if any(p in infrastructure_ports for p in port_list) else 0.0  # has_infrastructure_ports
        obs[31] = 1.0 if any(p >= 4000 for p in port_list) else 0.0  # has_custom_ports
        obs[32] = min(len(set(port_list)) / 20.0, 1.0)  # port_diversity
        
        # Estimate nmap value based on port types
        infra_count = sum(1 for p in port_list if p in infrastructure_ports)
        nmap_value = min(infra_count / 5.0, 1.0)
        obs[33] = nmap_value  # nmap_value_estimate
        
        obs[34] = 1.0 if all(p in web_ports for p in port_list) else 0.0  # web_only_target
        obs[35] = 1.0 if any(p in [3306, 5432, 6379, 27017] for p in port_list) else 0.0  # database_ports_found
        obs[36] = 1.0 if any(p in [8443, 9090, 9000] for p in port_list) else 0.0  # admin_ports_found
        obs[37] = min(len(port_list) / 20.0, 1.0)  # scannable_ports
        obs[38] = min(self.tools_used['nmap']['time'] / 300.0, 1.0)  # nmap_time
        obs[39] = nmap_value * 0.8  # nmap_expected_value (slightly lower than estimate)
        
        return obs
    
    def render(self):
        """Render environment (optional)"""
        if self.render_mode == "human":
            print(f"\n=== Step {self.step_count} ===")
            print(f"Phase: {['Subfinder', 'HTTPX', 'Nmap'][self.current_phase]}")
            print(f"Time: {self.time_elapsed:.1f}s / {self.time_budget}s")
            print(f"Discovered: {len(self.discovered['subdomains'])} subdomains, "
                  f"{len(self.discovered['live_endpoints'])} endpoints, "
                  f"{len(self.discovered['open_ports'])} ports")
            print(f"Reward: {self.total_reward:.1f}")


# For backwards compatibility
FullReconEnvironment = FullReconEnv
