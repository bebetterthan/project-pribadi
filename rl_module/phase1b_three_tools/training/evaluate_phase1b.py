"""
PHASE 1B EVALUATION SCRIPT
===========================

Evaluate trained Phase 1B agent on test scenarios (S21-S25).
Final gate decision: PASS → Phase 2 OR ITERATE.

USAGE:
    python evaluate_phase1b.py --model outputs/phase1b_run_TIMESTAMP/best_model/best_model.zip

REQUIREMENTS:
    - Trained model (.zip file)
    - VecNormalize stats (.pkl file)
    - Test scenarios (phase1b_test.json)

SUCCESS CRITERIA:
    1. Beat best baseline by >30% (>1580)
    2. Beat hardcoded by >30% (>1580)
    3. Variance <200 (stable)
    4. Intelligent nmap usage (50-90%)
    5. Observable patterns:
       - Uses nmap on infrastructure targets
       - Skips nmap on web-only targets
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import json
from typing import Dict, List

# Add paths
sys.path.append(str(Path(__file__).parent.parent / "envs"))
sys.path.append(str(Path(__file__).parent.parent / "baselines"))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

from full_recon_env import FullReconEnv
from random_agent import RandomAgent
from hardcoded_agent import HardcodedAgent
from phase1a_wrapper_agent import Phase1AWrapperAgent


def make_env(scenarios_path: str):
    """Create monitored environment"""
    env = FullReconEnv(scenarios_path=scenarios_path)
    env = Monitor(env)
    return env


def evaluate_baseline_on_test(agent_name: str, agent, eval_env, n_episodes=5) -> Dict:
    """
    Evaluate baseline agent on test scenarios.
    
    Args:
        agent_name: Name of agent (for display)
        agent: Agent instance
        eval_env: Test environment
        n_episodes: Number of test episodes
    
    Returns:
        Evaluation results dictionary
    """
    print(f"\n{agent_name}...")
    rewards = []
    episode_details = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        step_count = 0
        
        while not done:
            if hasattr(agent, 'predict'):
                action, _ = agent.predict(obs[0])
            else:
                action = agent.select_action(obs[0])
            
            obs, reward, done_vec, info = eval_env.step([action] if isinstance(action, (int, np.integer)) else action)
            episode_reward += reward[0]
            done = done_vec[0]
            step_count += 1
            
            if done and len(info) > 0:
                episode_details.append({
                    "episode": ep + 1,
                    "reward": float(episode_reward),
                    "scenario": info[0].get("scenario_name", "Unknown"),
                    "scenario_type": info[0].get("scenario_type", "Unknown")
                })
        
        rewards.append(episode_reward)
        print(f"   Episode {ep+1}/{n_episodes}: {episode_reward:.1f} - {episode_details[-1]['scenario']}")
    
    results = {
        "mean": float(np.mean(rewards)),
        "std": float(np.std(rewards)),
        "min": float(np.min(rewards)),
        "max": float(np.max(rewards)),
        "episodes": episode_details
    }
    
    print(f"   Mean: {results['mean']:.1f} ± {results['std']:.1f}")
    return results


def evaluate_trained_agent_detailed(model, eval_env, n_episodes=5) -> Dict:
    """
    Detailed evaluation of trained agent with nmap usage analysis.
    
    Args:
        model: Trained PPO model
        eval_env: Test environment
        n_episodes: Number of test episodes
    
    Returns:
        Detailed evaluation results
    """
    print("\n🤖 Trained RL Agent (Detailed Analysis)...")
    
    rewards = []
    episode_details = []
    
    # Nmap intelligence tracking
    nmap_decisions = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        step_count = 0
        actions_taken = []
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            actions_taken.append(int(action[0]))
            
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]
            done = done_vec[0]
            step_count += 1
            
            if done and len(info) > 0:
                scenario_info = info[0]
                
                # Analyze nmap decision
                nmap_used = scenario_info.get("nmap_used", False)
                scenario_type = scenario_info.get("scenario_type", "Unknown")
                scenario_name = scenario_info.get("scenario_name", "Unknown")
                
                # Determine optimal nmap strategy
                is_infrastructure = "infrastructure" in scenario_type.lower()
                is_web_only = "web" in scenario_type.lower() and not is_infrastructure
                
                nmap_decision = {
                    "episode": ep + 1,
                    "scenario": scenario_name,
                    "type": scenario_type,
                    "nmap_used": nmap_used,
                    "is_infrastructure": is_infrastructure,
                    "is_web_only": is_web_only,
                    "correct_decision": None
                }
                
                # Evaluate correctness
                if is_infrastructure:
                    nmap_decision["correct_decision"] = nmap_used  # Should use
                elif is_web_only:
                    nmap_decision["correct_decision"] = not nmap_used  # Should skip
                else:
                    nmap_decision["correct_decision"] = True  # Hybrid: either ok
                
                nmap_decisions.append(nmap_decision)
                
                episode_details.append({
                    "episode": ep + 1,
                    "reward": float(episode_reward),
                    "scenario": scenario_name,
                    "scenario_type": scenario_type,
                    "actions": actions_taken,
                    "nmap_used": nmap_used,
                    "correct_nmap": nmap_decision["correct_decision"],
                    "subdomains": scenario_info.get("total_subdomains", 0),
                    "endpoints": scenario_info.get("total_live", 0),
                    "ports": scenario_info.get("total_ports", 0),
                    "services": scenario_info.get("total_services", 0)
                })
        
        rewards.append(episode_reward)
        
        # Print episode summary
        ep_detail = episode_details[-1]
        nmap_status = "✅" if ep_detail["correct_nmap"] else "❌"
        print(f"   Episode {ep+1}/{n_episodes}: {episode_reward:.1f} | "
              f"{ep_detail['scenario']} | Nmap: {nmap_status}")
    
    # Calculate nmap intelligence metrics
    nmap_usage_rate = sum(1 for d in nmap_decisions if d["nmap_used"]) / len(nmap_decisions)
    nmap_correct_rate = sum(1 for d in nmap_decisions if d["correct_decision"]) / len(nmap_decisions)
    
    # Infrastructure accuracy
    infra_decisions = [d for d in nmap_decisions if d["is_infrastructure"]]
    infra_correct = sum(1 for d in infra_decisions if d["nmap_used"]) if infra_decisions else 0
    infra_accuracy = infra_correct / len(infra_decisions) if infra_decisions else 0
    
    # Web-only accuracy
    web_decisions = [d for d in nmap_decisions if d["is_web_only"]]
    web_correct = sum(1 for d in web_decisions if not d["nmap_used"]) if web_decisions else 0
    web_accuracy = web_correct / len(web_decisions) if web_decisions else 0
    
    results = {
        "mean": float(np.mean(rewards)),
        "std": float(np.std(rewards)),
        "min": float(np.min(rewards)),
        "max": float(np.max(rewards)),
        "nmap_usage_rate": float(nmap_usage_rate),
        "nmap_correct_rate": float(nmap_correct_rate),
        "nmap_infra_accuracy": float(infra_accuracy),
        "nmap_web_skip_accuracy": float(web_accuracy),
        "episodes": episode_details,
        "nmap_decisions": nmap_decisions
    }
    
    print(f"\n   📊 Summary:")
    print(f"   Mean Reward: {results['mean']:.1f} ± {results['std']:.1f}")
    print(f"   Nmap Usage: {nmap_usage_rate*100:.1f}%")
    print(f"   Nmap Correct: {nmap_correct_rate*100:.1f}%")
    print(f"   Infrastructure (use nmap): {infra_accuracy*100:.1f}%")
    print(f"   Web-only (skip nmap): {web_accuracy*100:.1f}%")
    
    return results


def analyze_gate_decision(baseline_results: Dict, agent_results: Dict) -> Dict:
    """
    Analyze all success criteria and make gate decision.
    
    Args:
        baseline_results: All baseline results
        agent_results: Trained agent results
    
    Returns:
        Gate decision dictionary
    """
    print("\n" + "="*70)
    print("🎯 PHASE 1B GATE DECISION")
    print("="*70)
    
    # Find best baseline
    best_baseline_mean = max(
        baseline_results["random"]["mean"],
        baseline_results["hardcoded"]["mean"],
        baseline_results["phase1a_wrapper"]["mean"]
    )
    
    agent_mean = agent_results["mean"]
    agent_std = agent_results["std"]
    hardcoded_mean = baseline_results["hardcoded"]["mean"]
    
    criteria = {}
    
    # Criterion 1: Beat best baseline by >30%
    target_30pct = best_baseline_mean * 1.30
    vs_best = (agent_mean / best_baseline_mean) if best_baseline_mean > 0 else 0
    criteria["beat_best_baseline"] = {
        "pass": agent_mean >= target_30pct,
        "target": float(target_30pct),
        "actual": float(agent_mean),
        "ratio": float(vs_best)
    }
    
    print(f"\n✓ Criterion 1: Beat Best Baseline (+30%)")
    print(f"   Best Baseline: {best_baseline_mean:.1f}")
    print(f"   Target: {target_30pct:.1f}")
    print(f"   Agent: {agent_mean:.1f}")
    print(f"   Status: {'✅ PASS' if criteria['beat_best_baseline']['pass'] else '❌ FAIL'}")
    
    # Criterion 2: Beat hardcoded by >30%
    vs_hardcoded = (agent_mean / hardcoded_mean) if hardcoded_mean > 0 else 0
    criteria["beat_hardcoded"] = {
        "pass": vs_hardcoded > 1.30,
        "target": float(hardcoded_mean * 1.30),
        "actual": float(agent_mean),
        "ratio": float(vs_hardcoded)
    }
    
    print(f"\n✓ Criterion 2: Beat Hardcoded (+30%)")
    print(f"   Hardcoded: {hardcoded_mean:.1f}")
    print(f"   Target: {hardcoded_mean * 1.30:.1f}")
    print(f"   Agent: {agent_mean:.1f}")
    print(f"   Status: {'✅ PASS' if criteria['beat_hardcoded']['pass'] else '❌ FAIL'}")
    
    # Criterion 3: Stable performance (variance <200)
    criteria["stable_performance"] = {
        "pass": agent_std < 200,
        "target": 200,
        "actual": float(agent_std)
    }
    
    print(f"\n✓ Criterion 3: Stable Performance (std <200)")
    print(f"   Agent Std: {agent_std:.1f}")
    print(f"   Status: {'✅ PASS' if criteria['stable_performance']['pass'] else '❌ FAIL'}")
    
    # Criterion 4: Intelligent nmap usage (50-90%)
    nmap_usage = agent_results.get("nmap_usage_rate", 0)
    criteria["nmap_usage"] = {
        "pass": 0.5 <= nmap_usage <= 0.9,
        "target_range": "50-90%",
        "actual": float(nmap_usage * 100)
    }
    
    print(f"\n✓ Criterion 4: Nmap Usage (50-90%)")
    print(f"   Usage Rate: {nmap_usage*100:.1f}%")
    print(f"   Status: {'✅ PASS' if criteria['nmap_usage']['pass'] else '❌ FAIL'}")
    
    # Criterion 5: Correct nmap decisions (>70%)
    nmap_correct = agent_results.get("nmap_correct_rate", 0)
    criteria["nmap_correctness"] = {
        "pass": nmap_correct > 0.7,
        "target": 0.7,
        "actual": float(nmap_correct)
    }
    
    print(f"\n✓ Criterion 5: Nmap Correctness (>70%)")
    print(f"   Correct Rate: {nmap_correct*100:.1f}%")
    print(f"   Infrastructure: {agent_results.get('nmap_infra_accuracy', 0)*100:.1f}%")
    print(f"   Web Skip: {agent_results.get('nmap_web_skip_accuracy', 0)*100:.1f}%")
    print(f"   Status: {'✅ PASS' if criteria['nmap_correctness']['pass'] else '❌ FAIL'}")
    
    # Gate decision
    all_pass = all(c["pass"] for c in criteria.values())
    
    gate_decision = {
        "pass": all_pass,
        "criteria": criteria,
        "recommendation": "PROCEED_TO_PHASE_2" if all_pass else "ITERATE"
    }
    
    print("\n" + "="*70)
    if all_pass:
        print("✅ GATE DECISION: PASS")
        print("\n🎉 PHASE 1B COMPLETE!")
        print("   All success criteria met")
        print("   Observable intelligent nmap usage")
        print("   Stable performance on test scenarios")
        print("\n➡️  PROCEED TO PHASE 2")
    else:
        print("❌ GATE DECISION: ITERATE")
        print("\n🔄 ITERATION NEEDED:")
        
        if not criteria["beat_best_baseline"]["pass"]:
            print(f"   - Improve reward (need +{target_30pct - agent_mean:.0f})")
        if not criteria["beat_hardcoded"]["pass"]:
            print("   - Beat hardcoded baseline")
        if not criteria["stable_performance"]["pass"]:
            print("   - Reduce variance (more training)")
        if not criteria["nmap_usage"]["pass"]:
            print("   - Adjust nmap usage pattern")
        if not criteria["nmap_correctness"]["pass"]:
            print("   - Improve nmap decision accuracy")
        
        print("\n📋 Options:")
        print("   1. Continue training (more timesteps)")
        print("   2. Adjust strategic bonus weights")
        print("   3. Tune hyperparameters (ent_coef, lr)")
        print("   4. Generate more diverse scenarios")
    
    print("="*70)
    
    return gate_decision


def main():
    parser = argparse.ArgumentParser(description="Evaluate Phase 1B trained agent")
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model (.zip file)"
    )
    parser.add_argument(
        "--norm-stats",
        type=str,
        default=None,
        help="Path to VecNormalize stats (.pkl file). If not provided, will look in model directory."
    )
    parser.add_argument(
        "--test-scenarios",
        type=str,
        default="../data/phase1b_test.json",
        help="Path to test scenarios"
    )
    parser.add_argument(
        "--n-episodes",
        type=int,
        default=5,
        help="Number of test episodes (default: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file for results"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("📊 PHASE 1B TEST EVALUATION")
    print("="*70)
    
    # Verify model exists
    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Find VecNormalize stats
    if args.norm_stats:
        norm_stats_path = Path(args.norm_stats)
    else:
        # Look in parent directory of model
        norm_stats_path = model_path.parent.parent / "vec_normalize_stats.pkl"
    
    if not norm_stats_path.exists():
        print(f"⚠️  VecNormalize stats not found: {norm_stats_path}")
        print("   Evaluation may be inaccurate without normalization!")
        norm_stats_path = None
    
    # Verify test scenarios
    test_scenarios_path = Path(args.test_scenarios)
    if not test_scenarios_path.exists():
        raise FileNotFoundError(f"Test scenarios not found: {test_scenarios_path}")
    
    print(f"\n📁 Model: {model_path}")
    print(f"📁 Norm Stats: {norm_stats_path if norm_stats_path else 'Not loaded'}")
    print(f"📁 Test Scenarios: {test_scenarios_path}")
    print(f"📊 Episodes: {args.n_episodes}")
    
    # Create test environment
    print("\n🏗️  Creating test environment...")
    test_env = DummyVecEnv([lambda: make_env(str(test_scenarios_path))])
    
    # Load VecNormalize stats if available
    if norm_stats_path:
        test_env = VecNormalize.load(str(norm_stats_path), test_env)
        test_env.training = False
        test_env.norm_reward = False
        print("   ✓ VecNormalize loaded")
    
    # Load trained model
    print("\n🤖 Loading trained model...")
    model = PPO.load(str(model_path))
    print("   ✓ Model loaded")
    
    # Get unwrapped env for baselines
    unwrapped_env = test_env.envs[0].unwrapped if hasattr(test_env, 'envs') else test_env.unwrapped
    
    # Evaluate baselines
    print("\n" + "="*70)
    print("📊 EVALUATING BASELINES ON TEST SCENARIOS")
    print("="*70)
    
    baseline_results = {}
    
    # Random
    print("\n🎲 Random Agent")
    random_agent = RandomAgent(unwrapped_env, seed=42)
    baseline_results["random"] = evaluate_baseline_on_test(
        "Random", random_agent, test_env, args.n_episodes
    )
    
    # Hardcoded
    print("\n🔧 Hardcoded Agent")
    hardcoded_agent = HardcodedAgent(unwrapped_env)
    baseline_results["hardcoded"] = evaluate_baseline_on_test(
        "Hardcoded", hardcoded_agent, test_env, args.n_episodes
    )
    
    # Phase 1A Wrapper
    print("\n🧠 Phase 1A Wrapper Agent")
    phase1a_agent = Phase1AWrapperAgent(unwrapped_env)
    baseline_results["phase1a_wrapper"] = evaluate_baseline_on_test(
        "Phase1A Wrapper", phase1a_agent, test_env, args.n_episodes
    )
    
    # Evaluate trained agent
    print("\n" + "="*70)
    print("📊 EVALUATING TRAINED AGENT ON TEST SCENARIOS")
    print("="*70)
    
    agent_results = evaluate_trained_agent_detailed(model, test_env, args.n_episodes)
    
    # Gate decision analysis
    gate_decision = analyze_gate_decision(baseline_results, agent_results)
    
    # Save results if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            "model_path": str(model_path),
            "test_scenarios": str(test_scenarios_path),
            "n_episodes": args.n_episodes,
            "baselines": baseline_results,
            "agent": agent_results,
            "gate_decision": gate_decision
        }
        
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved: {output_path}")
    
    print("\n" + "="*70)
    print("✅ EVALUATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
