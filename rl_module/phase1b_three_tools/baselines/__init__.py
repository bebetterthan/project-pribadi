"""
Baseline Agents for Phase 1B (3-Tool Sequential)
=================================================

This module provides baseline agents for comparison against the trained RL agent:

1. RandomAgent: Randomly selects valid actions from available action mask
2. HardcodedAgent: Always chooses comprehensive mode for all tools
3. Phase1AWrapperAgent: Uses Phase 1A trained model + default nmap strategy

Expected Performance Ranges (on training scenarios):
- RandomAgent: ~250-350 reward (random exploration)
- HardcodedAgent: ~300-400 reward (always comprehensive)
- Phase1AWrapperAgent: ~400-500 reward (good subfinder/httpx, default nmap)
"""

from .random_agent import RandomAgent
from .hardcoded_agent import HardcodedAgent
from .phase1a_wrapper_agent import Phase1AWrapperAgent

__all__ = [
    'RandomAgent',
    'HardcodedAgent',
    'Phase1AWrapperAgent',
]
