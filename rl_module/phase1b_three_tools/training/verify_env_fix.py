#!/usr/bin/env python3
"""Verify that environment fix is applied"""

import sys
from pathlib import Path
import inspect

# Add envs path
sys.path.insert(0, str(Path(__file__).parent.parent / "envs"))

from full_recon_env import FullReconEnv

# Load environment
env_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
env = FullReconEnv(str(env_path))

# Get reward calculation method source
reward_src = inspect.getsource(env._calculate_reward)

print("=" * 70)
print("ENVIRONMENT REWARD FIX VERIFICATION")
print("=" * 70)
print()

# Check if completion bonus is ONLY after nmap
completion_check = "if tool == 'nmap'" in reward_src and "completion" in reward_src

print(f"✓ Completion bonus conditional check: {'YES' if completion_check else 'NO'}")
print()

# Find the completion bonus section
if "Component 2" in reward_src:
    comp_start = reward_src.find("Component 2")
    comp_end = comp_start + 500
    comp_section = reward_src[comp_start:comp_end]
    
    print("Component 2: Completion Bonus section:")
    print("-" * 70)
    for line in comp_section.split('\n')[:15]:
        print(line)
    print()

# Check if 3-tool bonus exists
three_tool_check = "3-TOOL WORKFLOW" in reward_src or "all 3 tools" in reward_src.lower()
print(f"✓ 3-tool workflow bonus: {'YES' if three_tool_check else 'NO'}")
print()

if not completion_check:
    print("❌ FIX NOT APPLIED! Completion bonus still given without nmap!")
elif not three_tool_check:
    print("⚠️  3-tool bonus missing - agent may still skip nmap")
else:
    print("✅ Environment fixes APPLIED correctly!")

print("=" * 70)
