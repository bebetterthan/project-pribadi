#!/usr/bin/env python3
"""Quick verification that environment has amplified bonuses"""

import sys
from pathlib import Path
import inspect

# Add envs path
sys.path.insert(0, str(Path(__file__).parent.parent / "envs"))

from full_recon_env import FullReconEnv

# Load environment
env_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
env = FullReconEnv(str(env_path))

# Get strategic bonus method source
src = inspect.getsource(env._calculate_strategic_bonus)

print("=" * 70)
print("ENVIRONMENT BONUS VERIFICATION")
print("=" * 70)
print()
print("[CHECK] Strategic bonus method contains:")
print(f"  bonus += 400: {'YES ✓' if 'bonus += 400' in src else 'NO ✗'}")
print(f"  bonus += 300: {'YES ✓' if 'bonus += 300' in src else 'NO ✗'}")
print(f"  bonus += 200: {'YES ✓' if 'bonus += 200' in src else 'NO ✗'}")
print(f"  bonus += 150: {'YES ✓' if 'bonus += 150' in src else 'NO ✗'}")
print(f"  VERSION 3: {'YES ✓' if 'VERSION 3' in src else 'NO ✗'}")
print()

if 'bonus += 400' in src and 'VERSION 3' in src:
    print("[RESULT] Amplified bonuses LOADED correctly! ✓")
    print()
    print("Expected behavior:")
    print("  - Infrastructure + service mode: ~400 strategic bonus")
    print("  - Web-only + skip nmap: ~200 strategic bonus")
    print("  - Quick mode everywhere: ~50-100 strategic bonus")
    print()
    print("Ready to train!")
else:
    print("[ERROR] Still using old bonuses! ✗")
    print()
    print("Solution: Delete __pycache__ and reimport")
    
print("=" * 70)
