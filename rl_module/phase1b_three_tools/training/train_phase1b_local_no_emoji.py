"""
PHASE 1B LOCAL TRAINING - 3-TOOL SEQUENTIAL WORKFLOW
======================================================

Train PPO agent for intelligent 3-tool workflow (Subfinder → HTTPX → Nmap).
Key learning: WHEN to use nmap (conditional tool intelligence).

USAGE:
    python train_phase1b_local.py

MONITORING:
    tensorboard --logdir=outputs/run_TIMESTAMP/tensorboard
    Open browser: http://localhost:6006
    
TARGET PERFORMANCE:
    - Baseline Best (Hardcoded): 1215±187
    - Training Target (+30%): 1580
    - Ultimate Goal (+50%): 1823 with intelligent nmap usage

EXPECTED TRAINING TIME:
    - 150k timesteps
    - ~6-10 hours (local machine)
    - ~4997 steps/sec (measured)
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime
import json

# Add paths
sys.path.append(str(Path(__file__).parent.parent / "envs"))
sys.path.append(str(Path(__file__).parent.parent / "baselines"))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback, 
    EvalCallback, 
    CheckpointCallback,
    CallbackList
)
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

from full_recon_env import FullReconEnv
from random_agent import RandomAgent
from hardcoded_agent import HardcodedAgent
from phase1a_wrapper_agent import Phase1AWrapperAgent


class Phase1BMetricsCallback(BaseCallback):
    """
    Custom callback for logging Phase 1B metrics to TensorBoard.
    
    Tracks:
    - Episode rewards and lengths
    - Discovery metrics (subdomains, endpoints, ports, services, versions)
    - Tool usage patterns (which tools, which modes)
    - Nmap intelligence (skip on web-only, use on infrastructure)
    - Efficiency metrics
    """
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        
        # Discovery tracking
        self.episode_subdomains = []
        self.episode_endpoints = []
        self.episode_ports = []
        self.episode_services = []
        
        # Nmap intelligence tracking
        self.nmap_used_count = 0
        self.nmap_on_infrastructure_count = 0
        self.nmap_on_web_only_count = 0
        self.nmap_skipped_on_web_count = 0
        
    def _on_step(self) -> bool:
        # Get info from all environments
        for info in self.locals.get("infos", []):
            if "episode" in info:
                ep_reward = info["episode"]["r"]
                ep_length = info["episode"]["l"]
                
                self.episode_rewards.append(ep_reward)
                self.episode_lengths.append(ep_length)
                
                # Log basic metrics
                self.logger.record("phase1b/episode_reward", ep_reward)
                self.logger.record("phase1b/episode_length", ep_length)
                
                # Log discovery metrics
                if "total_subdomains" in info:
                    subdomains = info["total_subdomains"]
                    self.logger.record("phase1b/subdomains_found", subdomains)
                    self.episode_subdomains.append(subdomains)
                
                if "total_live" in info:
                    endpoints = info["total_live"]
                    self.logger.record("phase1b/endpoints_found", endpoints)
                    self.episode_endpoints.append(endpoints)
                
                if "total_ports" in info:
                    ports = info["total_ports"]
                    self.logger.record("phase1b/ports_found", ports)
                    self.episode_ports.append(ports)
                
                if "total_services" in info:
                    services = info["total_services"]
                    self.logger.record("phase1b/services_found", services)
                    self.episode_services.append(services)
                
                # Log nmap intelligence
                if "nmap_used" in info:
                    if info["nmap_used"]:
                        self.nmap_used_count += 1
                        
                        # Check if used on appropriate target
                        scenario_type = info.get("scenario_type", "")
                        if "infrastructure" in scenario_type.lower():
                            self.nmap_on_infrastructure_count += 1
                        elif "web" in scenario_type.lower():
                            self.nmap_on_web_only_count += 1
                    else:
                        # Nmap skipped
                        scenario_type = info.get("scenario_type", "")
                        if "web" in scenario_type.lower():
                            self.nmap_skipped_on_web_count += 1
                    
                    # Log nmap usage stats
                    total_episodes = len(self.episode_rewards)
                    if total_episodes > 0:
                        nmap_usage_rate = self.nmap_used_count / total_episodes
                        self.logger.record("phase1b/nmap_usage_rate", nmap_usage_rate)
                        
                        if self.nmap_used_count > 0:
                            infra_accuracy = self.nmap_on_infrastructure_count / self.nmap_used_count
                            self.logger.record("phase1b/nmap_on_infra_accuracy", infra_accuracy)
                        
                        if self.nmap_skipped_on_web_count > 0:
                            skip_intelligence = self.nmap_skipped_on_web_count / total_episodes
                            self.logger.record("phase1b/nmap_skip_intelligence", skip_intelligence)
                
                # Log efficiency
                if ep_length > 0:
                    efficiency = ep_reward / ep_length
                    self.logger.record("phase1b/efficiency", efficiency)
        
        return True


def make_env(scenarios_path: str):
    """
    Create and wrap environment with Monitor.
    
    Args:
        scenarios_path: Path to scenarios JSON
    
    Returns:
        Wrapped environment
    """
    env = FullReconEnv(scenarios_path=scenarios_path)
    env = Monitor(env)
    return env


def evaluate_baselines(eval_env, n_episodes=20, verbose=True):
    """
    Evaluate all baseline agents.
    
    Args:
        eval_env: Evaluation environment (VecEnv with VecNormalize)
        n_episodes: Number of episodes per agent
        verbose: Print detailed results
    
    Returns:
        Dictionary with baseline results
    """
    if verbose:
        print("\n" + "="*70)
        print(" EVALUATING BASELINE AGENTS")
        print("="*70)
    
    results = {}
    
    # Get unwrapped env for agent access
    unwrapped_env = eval_env.envs[0].unwrapped if hasattr(eval_env, 'envs') else eval_env.unwrapped
    
    # 1. Random Agent
    if verbose:
        print("\n Random Agent...")
    random_agent = RandomAgent(unwrapped_env, seed=42)
    random_rewards = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = random_agent.predict(obs[0])
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]
            done = done_vec[0]
        
        random_rewards.append(episode_reward)
    
    results["random"] = {
        "mean": np.mean(random_rewards),
        "std": np.std(random_rewards),
        "min": np.min(random_rewards),
        "max": np.max(random_rewards)
    }
    
    if verbose:
        print(f"   Mean: {results['random']['mean']:.1f} ± {results['random']['std']:.1f}")
        print(f"   Range: [{results['random']['min']:.1f}, {results['random']['max']:.1f}]")
    
    # 2. Hardcoded Agent
    if verbose:
        print("\n Hardcoded Agent (always comprehensive)...")
    hardcoded_agent = HardcodedAgent(unwrapped_env)
    hardcoded_rewards = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = hardcoded_agent.predict(obs[0])
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]
            done = done_vec[0]
        
        hardcoded_rewards.append(episode_reward)
    
    results["hardcoded"] = {
        "mean": np.mean(hardcoded_rewards),
        "std": np.std(hardcoded_rewards),
        "min": np.min(hardcoded_rewards),
        "max": np.max(hardcoded_rewards)
    }
    
    if verbose:
        print(f"   Mean: {results['hardcoded']['mean']:.1f} ± {results['hardcoded']['std']:.1f}")
        print(f"   Range: [{results['hardcoded']['min']:.1f}, {results['hardcoded']['max']:.1f}]")
    
    # 3. Phase 1A Wrapper Agent (smart heuristic)
    if verbose:
        print("\n Phase 1A Wrapper Agent (smart heuristic)...")
    phase1a_agent = Phase1AWrapperAgent(unwrapped_env)
    phase1a_rewards = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = phase1a_agent.predict(obs[0])
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]
            done = done_vec[0]
        
        phase1a_rewards.append(episode_reward)
    
    results["phase1a_wrapper"] = {
        "mean": np.mean(phase1a_rewards),
        "std": np.std(phase1a_rewards),
        "min": np.min(phase1a_rewards),
        "max": np.max(phase1a_rewards)
    }
    
    if verbose:
        print(f"   Mean: {results['phase1a_wrapper']['mean']:.1f} ± {results['phase1a_wrapper']['std']:.1f}")
        print(f"   Range: [{results['phase1a_wrapper']['min']:.1f}, {results['phase1a_wrapper']['max']:.1f}]")
    
    # Summary
    if verbose:
        print("\n" + "="*70)
        print(" BASELINE SUMMARY")
        print("="*70)
        best_baseline = max(
            results["random"]["mean"],
            results["hardcoded"]["mean"],
            results["phase1a_wrapper"]["mean"]
        )
        print(f"Best Baseline: {best_baseline:.1f}")
        print(f"Target (+30%): {best_baseline * 1.30:.1f}")
        print(f"Target (+50%): {best_baseline * 1.50:.1f}")
        print("="*70)
    
    return results


def evaluate_agent(model, eval_env, n_episodes=20, verbose=True):
    """
    Evaluate trained RL agent.
    
    Args:
        model: Trained PPO model
        eval_env: Evaluation environment (VecEnv)
        n_episodes: Number of episodes
        verbose: Print results
    
    Returns:
        Dictionary with evaluation results
    """
    if verbose:
        print("\n Trained RL Agent...")
    
    rewards = []
    lengths = []
    discoveries = {
        "subdomains": [],
        "endpoints": [],
        "ports": [],
        "services": []
    }
    nmap_usage = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()
        episode_reward = 0
        episode_length = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]
            episode_length += 1
            done = done_vec[0]
            
            # Collect metrics
            if done and len(info) > 0:
                if "total_subdomains" in info[0]:
                    discoveries["subdomains"].append(info[0]["total_subdomains"])
                if "total_live" in info[0]:
                    discoveries["endpoints"].append(info[0]["total_live"])
                if "total_ports" in info[0]:
                    discoveries["ports"].append(info[0]["total_ports"])
                if "total_services" in info[0]:
                    discoveries["services"].append(info[0]["total_services"])
                if "nmap_used" in info[0]:
                    nmap_usage.append(info[0]["nmap_used"])
        
        rewards.append(episode_reward)
        lengths.append(episode_length)
    
    results = {
        "mean": np.mean(rewards),
        "std": np.std(rewards),
        "min": np.min(rewards),
        "max": np.max(rewards),
        "mean_length": np.mean(lengths),
        "mean_subdomains": np.mean(discoveries["subdomains"]) if discoveries["subdomains"] else 0,
        "mean_endpoints": np.mean(discoveries["endpoints"]) if discoveries["endpoints"] else 0,
        "mean_ports": np.mean(discoveries["ports"]) if discoveries["ports"] else 0,
        "mean_services": np.mean(discoveries["services"]) if discoveries["services"] else 0,
        "nmap_usage_rate": np.mean(nmap_usage) if nmap_usage else 0
    }
    
    if verbose:
        print(f"   Mean Reward: {results['mean']:.1f} ± {results['std']:.1f}")
        print(f"   Range: [{results['min']:.1f}, {results['max']:.1f}]")
        print(f"   Mean Length: {results['mean_length']:.1f}")
        print(f"   Discoveries: {results['mean_subdomains']:.1f} subdomains, "
              f"{results['mean_endpoints']:.1f} endpoints, "
              f"{results['mean_ports']:.1f} ports")
        print(f"   Nmap Usage: {results['nmap_usage_rate']*100:.1f}%")
    
    return results


def check_success_criteria(baseline_results, agent_results, verbose=True):
    """
    Check Phase 1B success criteria.
    
    Criteria:
    1. Beat best baseline by >30% (target: 1580+)
    2. Beat hardcoded by >30% (1.3x)
    3. Observable intelligent nmap usage patterns
    4. Variance <200 (stable performance)
    
    Args:
        baseline_results: Dictionary with baseline results
        agent_results: Dictionary with agent results
        verbose: Print detailed analysis
    
    Returns:
        Boolean indicating success
    """
    if verbose:
        print("\n" + "="*70)
        print(" PHASE 1B SUCCESS CRITERIA CHECK")
        print("="*70)
    
    # Find best baseline
    best_baseline_mean = max(
        baseline_results["random"]["mean"],
        baseline_results["hardcoded"]["mean"],
        baseline_results["phase1a_wrapper"]["mean"]
    )
    
    hardcoded_mean = baseline_results["hardcoded"]["mean"]
    agent_mean = agent_results["mean"]
    agent_std = agent_results["std"]
    
    # Criterion 1: Beat best baseline by >30%
    vs_best = (agent_mean / best_baseline_mean) if best_baseline_mean > 0 else 0
    target_30pct = best_baseline_mean * 1.30
    criterion1_pass = agent_mean >= target_30pct
    
    if verbose:
        print(f"\n1️⃣  Beat Best Baseline by >30%:")
        print(f"   Best Baseline: {best_baseline_mean:.1f}")
        print(f"   Target (+30%): {target_30pct:.1f}")
        print(f"   Agent: {agent_mean:.1f}")
        print(f"   Ratio: {vs_best:.2f}x")
        print(f"   Status: {' PASS' if criterion1_pass else ' FAIL'}")
    
    # Criterion 2: Beat hardcoded by >30%
    vs_hardcoded = (agent_mean / hardcoded_mean) if hardcoded_mean > 0 else 0
    criterion2_pass = vs_hardcoded > 1.3
    
    if verbose:
        print(f"\n2️⃣  Beat Hardcoded by >30%:")
        print(f"   Hardcoded: {hardcoded_mean:.1f}")
        print(f"   Agent: {agent_mean:.1f}")
        print(f"   Ratio: {vs_hardcoded:.2f}x")
        print(f"   Status: {' PASS' if criterion2_pass else ' FAIL'}")
    
    # Criterion 3: Variance check
    criterion3_pass = agent_std < 200
    
    if verbose:
        print(f"\n3️⃣  Stable Performance (variance <200):")
        print(f"   Agent Std: {agent_std:.1f}")
        print(f"   Status: {' PASS' if criterion3_pass else ' FAIL'}")
    
    # Criterion 4: Intelligent nmap usage
    nmap_usage = agent_results.get("nmap_usage_rate", 0)
    # Expect 50-80% usage (skip on web-only, use on infrastructure)
    criterion4_pass = 0.5 <= nmap_usage <= 0.9
    
    if verbose:
        print(f"\n4️⃣  Intelligent Nmap Usage (50-90%):")
        print(f"   Nmap Usage Rate: {nmap_usage*100:.1f}%")
        print(f"   Status: {' PASS' if criterion4_pass else ' FAIL'}")
    
    # Overall
    all_pass = criterion1_pass and criterion2_pass and criterion3_pass and criterion4_pass
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"OVERALL: {' PHASE 1B SUCCESS!' if all_pass else ' NEEDS ITERATION'}")
        
        if all_pass:
            print("\n READY FOR PHASE 2!")
            print("    Beats all baselines")
            print("    Stable performance")
            print("    Intelligent nmap usage")
        else:
            print("\n ITERATION NEEDED:")
            if not criterion1_pass:
                print(f"   - Increase reward to >{target_30pct:.0f}")
            if not criterion2_pass:
                print("   - Improve vs hardcoded baseline")
            if not criterion3_pass:
                print("   - Reduce variance (more training?)")
            if not criterion4_pass:
                print("   - Tune strategic bonus weights")
        
        print(f"{'='*70}")
    
    return all_pass


def main():
    """Main training loop for Phase 1B"""
    
    print("="*70)
    print("PHASE 1B LOCAL TRAINING - 3-TOOL WORKFLOW")
    print("="*70)
    print("Learning Goal: WHEN to use nmap (conditional tool intelligence)")
    print("="*70)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    training_path = str(data_dir / "phase1b_train.json")
    test_path = str(data_dir / "phase1b_test.json")
    
    # Verify files exist
    if not Path(training_path).exists():
        raise FileNotFoundError(f"Training scenarios not found: {training_path}")
    if not Path(test_path).exists():
        raise FileNotFoundError(f"Test scenarios not found: {test_path}")
    
    # Create output directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "outputs" / f"phase1b_run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tensorboard_dir = output_dir / "tensorboard"
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    
    print(f"\n Output Directory: {output_dir}")
    print(f" TensorBoard: tensorboard --logdir={tensorboard_dir}")
    print(f" Open: http://localhost:6006")
    
    # Create environments
    print("\n️  Creating environments...")
    train_env = DummyVecEnv([lambda: make_env(training_path)])
    
    # VecNormalize wrapper (critical for stable training!)
    print("   Adding VecNormalize wrapper...")
    train_env = VecNormalize(
        train_env,
        norm_obs=True,         # Normalize observations
        norm_reward=True,      # Normalize rewards
        clip_obs=10.0,
        clip_reward=10.0,
        gamma=0.99
    )
    
    # Save normalization stats path
    norm_stats_path = output_dir / "vec_normalize_stats.pkl"
    
    # Eval env with SAME wrapper (but training=False)
    eval_env = DummyVecEnv([lambda: make_env(training_path)])
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=False,     # Don't normalize rewards during eval
        clip_obs=10.0,
        training=False,
        gamma=0.99
    )
    
    print(f"   Training scenarios: 20")
    print(f"   Test scenarios: 5")
    print(f"   Observation space: 40-dim")
    print(f"   Action space: 9 discrete (3 tools × 3 modes)")
    print(f"   Normalization: ENABLED")
    
    # Evaluate baselines first
    baseline_results = evaluate_baselines(eval_env, n_episodes=20, verbose=True)
    
    # Create PPO model (use Phase 1A proven hyperparameters!)
    print("\n Creating PPO agent...")
    model = PPO(
        "MlpPolicy",
        train_env,
        
        # PROVEN HYPERPARAMETERS from Phase 1A success
        learning_rate=1e-3,      # Fast learning
        ent_coef=0.05,           # High exploration (critical!)
        
        # Update frequency
        n_steps=512,             # Update more often
        batch_size=128,          # Larger batches
        n_epochs=20,             # Learn more per update
        
        # Standard settings
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        
        verbose=1,
        tensorboard_log=str(tensorboard_dir)
    )
    
    print("   Policy: MLP (Multi-Layer Perceptron)")
    print("   Learning rate: 1e-3")
    print("   Entropy coef: 0.05 (high exploration)")
    print("   Batch size: 128")
    print("   Training timesteps: 150,000")
    print("   Expected time: 6-10 hours (local)")
    
    # Setup callbacks
    print("\n️  Setting up callbacks...")
    
    # Checkpoint every 25k steps
    checkpoint_callback = CheckpointCallback(
        save_freq=25000,
        save_path=str(checkpoints_dir),
        name_prefix="ppo_phase1b"
    )
    
    # Evaluation every 10k steps
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(output_dir / "best_model"),
        log_path=str(output_dir / "eval_logs"),
        eval_freq=10000,
        n_eval_episodes=10,
        deterministic=True,
        render=False
    )
    
    # Custom Phase 1B metrics
    metrics_callback = Phase1BMetricsCallback()
    
    # Combine callbacks
    callbacks = CallbackList([checkpoint_callback, eval_callback, metrics_callback])
    
    print("    Checkpoints every 25k steps")
    print("    Evaluation every 10k steps")
    print("    Custom Phase 1B metrics enabled")
    
    # Train!
    print("\n" + "="*70)
    print("️  STARTING TRAINING")
    print("="*70)
    print("\n TIP: Monitor progress in TensorBoard:")
    print(f"   tensorboard --logdir={tensorboard_dir}")
    print(f"   http://localhost:6006")
    print("\n Key metrics to watch:")
    print("   - phase1b/episode_reward (should trend up)")
    print("   - phase1b/nmap_usage_rate (should stabilize 50-80%)")
    print("   - phase1b/nmap_on_infra_accuracy (should trend up)")
    print("\n⏱️  Expected duration: 6-10 hours")
    print("="*70 + "\n")
    
    try:
        model.learn(
            total_timesteps=150000,
            callback=callbacks,
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\n️  Training interrupted by user")
    
    # Save final model
    final_model_path = output_dir / "final_model"
    model.save(str(final_model_path))
    print(f"\n Final model saved: {final_model_path}")
    
    # Save VecNormalize stats (CRITICAL!)
    train_env.save(str(norm_stats_path))
    print(f" Normalization stats saved: {norm_stats_path}")
    
    # Final evaluation
    print("\n" + "="*70)
    print(" FINAL EVALUATION (Training Scenarios)")
    print("="*70)
    
    agent_results = evaluate_agent(model, eval_env, n_episodes=20, verbose=True)
    
    # Check success criteria
    success = check_success_criteria(baseline_results, agent_results, verbose=True)
    
    # Convert numpy types for JSON
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    # Save results
    results_summary = {
        "timestamp": timestamp,
        "phase": "1B",
        "baselines": convert_to_native(baseline_results),
        "agent": convert_to_native(agent_results),
        "success": success,
        "training_timesteps": 150000,
        "hyperparameters": {
            "learning_rate": 1e-3,
            "ent_coef": 0.05,
            "n_steps": 512,
            "batch_size": 128,
            "n_epochs": 20
        }
    }
    
    results_file = output_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\n Results saved: {results_file}")
    
    # Next steps
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    
    if success:
        print(" Training successful!")
        print("\n Day 8 Tasks:")
        print("   1. Evaluate on TEST scenarios (phase1b_test.json)")
        print("   2. Analyze nmap usage patterns")
        print("   3. Compare with all baselines")
        print("   4. Make gate decision: PASS → Phase 2 OR ITERATE")
        print("\n If test evaluation passes → READY FOR PHASE 2!")
    else:
        print("️  Training did not meet success criteria")
        print("\n Iteration options:")
        print("   1. Continue training (more timesteps)")
        print("   2. Adjust strategic bonus weights")
        print("   3. Generate more diverse scenarios")
        print("   4. Tune hyperparameters")
    
    print("="*70)
    print(" TRAINING COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

