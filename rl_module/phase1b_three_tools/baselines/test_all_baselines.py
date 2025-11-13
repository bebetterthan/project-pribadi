"""
Test All Baseline Agents for Phase 1B
=======================================

Evaluates all three baseline agents on training scenarios:
1. RandomAgent: Lower bound (~250-350)
2. HardcodedAgent: Mid-level (~300-450)
3. Phase1AWrapperAgent: Upper bound (~400-500)

This provides performance baselines for comparison with the trained RL agent.
"""

import sys
import numpy as np
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent.parent / "envs"))
sys.path.append(str(Path(__file__).parent))

from full_recon_env import FullReconEnv
from random_agent import evaluate_random_agent
from hardcoded_agent import evaluate_hardcoded_agent
from phase1a_wrapper_agent import evaluate_phase1a_wrapper_agent


def test_all_baselines(
    scenarios_path: str = "../data/phase1b_train.json",
    num_episodes: int = 20,
    seed: int = 42
) -> dict:
    """
    Test all baseline agents and compare results.
    
    Args:
        scenarios_path: Path to training scenarios
        num_episodes: Number of episodes per agent
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with all results
    """
    print("\n" + "="*70)
    print("PHASE 1B BASELINE AGENTS EVALUATION")
    print("="*70)
    print(f"Scenarios: {scenarios_path}")
    print(f"Episodes per agent: {num_episodes}")
    print(f"Random seed: {seed}")
    print("="*70)
    
    # Create environment
    env = FullReconEnv(scenarios_path=scenarios_path)
    
    # Test 1: Random Agent
    print("\n\n" + "🎲 " + "="*65)
    print("BASELINE 1: RANDOM AGENT")
    print("="*70)
    random_results = evaluate_random_agent(env, num_episodes, seed, verbose=True)
    
    # Test 2: Hardcoded Agent
    print("\n\n" + "🔧 " + "="*65)
    print("BASELINE 2: HARDCODED AGENT (Always Comprehensive)")
    print("="*70)
    hardcoded_results = evaluate_hardcoded_agent(env, num_episodes, verbose=True)
    
    # Test 3: Phase 1A Wrapper Agent
    print("\n\n" + "🧠 " + "="*65)
    print("BASELINE 3: PHASE 1A WRAPPER AGENT")
    print("="*70)
    phase1a_results = evaluate_phase1a_wrapper_agent(env, num_episodes, verbose=True)
    
    # Compare results
    print("\n\n" + "="*70)
    print("BASELINE COMPARISON")
    print("="*70)
    
    results_table = [
        ["Agent", "Mean", "Std", "Min", "Max", "Range"],
        ["-"*20, "-"*8, "-"*8, "-"*8, "-"*8, "-"*15],
        [
            "Random",
            f"{random_results['mean']:.1f}",
            f"{random_results['std']:.1f}",
            f"{random_results['min']:.1f}",
            f"{random_results['max']:.1f}",
            f"{random_results['min']:.1f}-{random_results['max']:.1f}"
        ],
        [
            "Hardcoded",
            f"{hardcoded_results['mean']:.1f}",
            f"{hardcoded_results['std']:.1f}",
            f"{hardcoded_results['min']:.1f}",
            f"{hardcoded_results['max']:.1f}",
            f"{hardcoded_results['min']:.1f}-{hardcoded_results['max']:.1f}"
        ],
        [
            "Phase1A Wrapper",
            f"{phase1a_results['mean']:.1f}",
            f"{phase1a_results['std']:.1f}",
            f"{phase1a_results['min']:.1f}",
            f"{phase1a_results['max']:.1f}",
            f"{phase1a_results['min']:.1f}-{phase1a_results['max']:.1f}"
        ]
    ]
    
    for row in results_table:
        print(f"{row[0]:<20} {row[1]:>8} {row[2]:>8} {row[3]:>8} {row[4]:>8} {row[5]:>15}")
    
    print("="*70)
    
    # Performance ranking
    agents = [
        ("Random", random_results['mean']),
        ("Hardcoded", hardcoded_results['mean']),
        ("Phase1A Wrapper", phase1a_results['mean'])
    ]
    agents_sorted = sorted(agents, key=lambda x: x[1], reverse=True)
    
    print("\n📊 Performance Ranking:")
    for i, (name, score) in enumerate(agents_sorted, 1):
        print(f"  {i}. {name}: {score:.1f}")
    
    # Expected vs actual
    print("\n✅ Expected Performance:")
    print("  Random:         250-350 (lower bound)")
    print("  Hardcoded:      300-450 (mid-level)")
    print("  Phase1A Wrapper: 400-500 (upper bound)")
    
    print("\n📈 Actual Performance:")
    print(f"  Random:          {random_results['mean']:.1f} ± {random_results['std']:.1f}")
    print(f"  Hardcoded:       {hardcoded_results['mean']:.1f} ± {hardcoded_results['std']:.1f}")
    print(f"  Phase1A Wrapper: {phase1a_results['mean']:.1f} ± {phase1a_results['std']:.1f}")
    
    # Training target
    print("\n🎯 Training Target:")
    best_baseline = agents_sorted[0][1]
    target_30pct = best_baseline * 1.30
    target_50pct = best_baseline * 1.50
    print(f"  Best Baseline: {best_baseline:.1f}")
    print(f"  Target (+30%): {target_30pct:.1f}")
    print(f"  Target (+50%): {target_50pct:.1f}")
    print(f"  Ultimate Goal: 600+ (observable intelligent nmap usage)")
    
    print("="*70)
    print("✅ Baseline evaluation complete!")
    print("="*70)
    
    return {
        'random': random_results,
        'hardcoded': hardcoded_results,
        'phase1a_wrapper': phase1a_results,
        'best_baseline_mean': best_baseline,
        'target_30pct': target_30pct,
        'target_50pct': target_50pct
    }


if __name__ == "__main__":
    # Run baseline tests
    results = test_all_baselines(
        scenarios_path="../data/phase1b_train.json",
        num_episodes=20,
        seed=42
    )
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. ✅ Baselines established")
    print("2. 📝 Day 6: Create training script (train_phase1b_local.py)")
    print("3. 🏃 Day 7: Run training overnight (150k timesteps)")
    print("4. 📊 Day 8: Evaluate vs baselines on test scenarios")
    print("="*70)
