"""
PHASE 1 LOCAL TRAINING
======================

Train PPO agent for subfinder strategy learning with TensorBoard monitoring.

USAGE:
    python train_local.py

MONITORING:
    Open browser: http://localhost:6006
    
    TensorBoard shows:
    - Episode rewards (rollout/ep_rew_mean)
    - Episode lengths (rollout/ep_len_mean)
    - Learning rate
    - Loss functions
    - Custom metrics (discovery rate, efficiency, etc.)
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime
import json

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback, 
    EvalCallback, 
    CheckpointCallback,
    CallbackList
)
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

from envs.subfinder_httpx_env import SubfinderHttpxEnv
from baselines.random_agent import RandomAgent
from baselines.hardcoded_agent import HardcodedAgent


class MetricsCallback(BaseCallback):
    """
    Custom callback for logging detailed metrics to TensorBoard.
    Logs discovery rate, probing accuracy, efficiency, strategic decisions, etc.
    Updated for 2-tool workflow (subfinder + httpx).
    """
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_discoveries = []
        self.episode_efficiencies = []
        
    def _on_step(self) -> bool:
        # Get info from all environments
        for info in self.locals.get("infos", []):
            if "episode" in info:
                ep_reward = info["episode"]["r"]
                ep_length = info["episode"]["l"]
                
                self.episode_rewards.append(ep_reward)
                self.episode_lengths.append(ep_length)
                
                # Log to TensorBoard
                self.logger.record("custom/episode_reward", ep_reward)
                self.logger.record("custom/episode_length", ep_length)
                
                # Log subdomain discovery if available
                if "total_subdomains_found" in info:
                    self.logger.record("custom/subdomains_found", info["total_subdomains_found"])
                    self.episode_discoveries.append(info["total_subdomains_found"])
                
                # Log HTTPX live hosts (NEW for 2-tool)
                if "total_live_found" in info:
                    self.logger.record("custom/live_hosts_found", info["total_live_found"])
                
                # Log efficiency (reward per step)
                if ep_length > 0:
                    efficiency = ep_reward / ep_length
                    self.logger.record("custom/efficiency", efficiency)
                    self.episode_efficiencies.append(efficiency)
        
        return True


def make_env(scenarios_path: str):
    """
    Create and wrap environment with Monitor for logging.
    
    Args:
        scenarios_path: Path to scenarios JSON
    
    Returns:
        Wrapped environment
    """
    env = SubfinderHttpxEnv(scenarios_path=scenarios_path)
    env = Monitor(env)  # Wrap with Monitor for episode stats
    return env


def evaluate_baselines(eval_env, n_episodes=10):
    """
    Evaluate random and hardcoded baselines.
    
    Args:
        eval_env: Evaluation environment
        n_episodes: Number of episodes to test
    
    Returns:
        Dictionary with baseline results
    """
    print("\n" + "="*60)
    print("📊 EVALUATING BASELINES")
    print("="*60)
    
    results = {}
    
    # Random baseline
    print("\n🎲 Random Agent...")
    # Get unwrapped env for action_masks (VecNormalize wraps DummyVecEnv)
    unwrapped_env = eval_env.envs[0].unwrapped if hasattr(eval_env, 'envs') else eval_env.unwrapped
    random_agent = RandomAgent(unwrapped_env)
    random_rewards = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()  # VecEnv returns obs directly
        episode_reward = 0
        done = False
        
        while not done:
            action = random_agent.select_action(obs[0])  # VecEnv returns array of obs
            obs, reward, done_vec, info = eval_env.step([action])  # VecEnv expects array of actions
            episode_reward += reward[0]  # VecEnv returns array of rewards
            done = done_vec[0]
        
        random_rewards.append(episode_reward)
    
    results["random"] = {
        "mean": np.mean(random_rewards),
        "std": np.std(random_rewards),
        "min": np.min(random_rewards),
        "max": np.max(random_rewards)
    }
    
    print(f"   Mean: {results['random']['mean']:.2f} ± {results['random']['std']:.2f}")
    print(f"   Range: [{results['random']['min']:.2f}, {results['random']['max']:.2f}]")
    
    # Hardcoded baseline
    print("\n🔧 Hardcoded Agent (always comprehensive)...")
    hardcoded_agent = HardcodedAgent(unwrapped_env)
    hardcoded_rewards = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()  # VecEnv returns obs directly
        episode_reward = 0
        done = False
        
        while not done:
            action = hardcoded_agent.select_action(obs[0])  # VecEnv returns array of obs
            obs, reward, done_vec, info = eval_env.step([action])  # VecEnv expects array of actions
            episode_reward += reward[0]  # VecEnv returns array of rewards
            done = done_vec[0]
        
        hardcoded_rewards.append(episode_reward)
    
    results["hardcoded"] = {
        "mean": np.mean(hardcoded_rewards),
        "std": np.std(hardcoded_rewards),
        "min": np.min(hardcoded_rewards),
        "max": np.max(hardcoded_rewards)
    }
    
    print(f"   Mean: {results['hardcoded']['mean']:.2f} ± {results['hardcoded']['std']:.2f}")
    print(f"   Range: [{results['hardcoded']['min']:.2f}, {results['hardcoded']['max']:.2f}]")
    
    return results


def evaluate_agent(model, eval_env, n_episodes=10):
    """
    Evaluate trained RL agent.
    
    Args:
        model: Trained PPO model
        eval_env: Evaluation environment (VecEnv)
        n_episodes: Number of episodes to test
    
    Returns:
        Dictionary with evaluation results
    """
    print("\n🤖 Trained RL Agent...")
    rewards = []
    lengths = []
    discoveries = []
    
    for ep in range(n_episodes):
        obs = eval_env.reset()  # VecEnv returns obs directly
        episode_reward = 0
        episode_length = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done_vec, info = eval_env.step(action)
            episode_reward += reward[0]  # VecEnv returns array
            episode_length += 1
            done = done_vec[0]
            
            if done and len(info) > 0 and "total_subdomains_found" in info[0]:
                discoveries.append(info[0]["total_subdomains_found"])
        
        rewards.append(episode_reward)
        lengths.append(episode_length)
    
    results = {
        "mean": np.mean(rewards),
        "std": np.std(rewards),
        "min": np.min(rewards),
        "max": np.max(rewards),
        "mean_length": np.mean(lengths),
        "mean_discoveries": np.mean(discoveries) if discoveries else 0
    }
    
    print(f"   Mean Reward: {results['mean']:.2f} ± {results['std']:.2f}")
    print(f"   Range: [{results['min']:.2f}, {results['max']:.2f}]")
    print(f"   Mean Length: {results['mean_length']:.1f}")
    print(f"   Mean Discoveries: {results['mean_discoveries']:.1f}")
    
    return results


def check_success_criteria(baseline_results, agent_results):
    """
    Check if agent meets Phase 1 success criteria.
    
    Criteria:
    1. Beat random by >100% (2x)
    2. Beat hardcoded by >30% (1.3x)
    3. Observable improvement
    
    Args:
        baseline_results: Dictionary with random/hardcoded results
        agent_results: Dictionary with RL agent results
    
    Returns:
        Boolean indicating success
    """
    print("\n" + "="*60)
    print("🎯 SUCCESS CRITERIA CHECK")
    print("="*60)
    
    random_mean = baseline_results["random"]["mean"]
    hardcoded_mean = baseline_results["hardcoded"]["mean"]
    agent_mean = agent_results["mean"]
    
    # Criterion 1: Beat random by >100%
    vs_random = (agent_mean / random_mean) if random_mean > 0 else 0
    random_pass = vs_random > 2.0
    
    print(f"\n1️⃣ Beat Random by >100%:")
    print(f"   Random: {random_mean:.2f}")
    print(f"   Agent: {agent_mean:.2f}")
    print(f"   Ratio: {vs_random:.2f}x")
    print(f"   Status: {'✅ PASS' if random_pass else '❌ FAIL'}")
    
    # Criterion 2: Beat hardcoded by >30%
    vs_hardcoded = (agent_mean / hardcoded_mean) if hardcoded_mean > 0 else 0
    hardcoded_pass = vs_hardcoded > 1.3
    
    print(f"\n2️⃣ Beat Hardcoded by >30%:")
    print(f"   Hardcoded: {hardcoded_mean:.2f}")
    print(f"   Agent: {agent_mean:.2f}")
    print(f"   Ratio: {vs_hardcoded:.2f}x")
    print(f"   Status: {'✅ PASS' if hardcoded_pass else '❌ FAIL'}")
    
    # Overall
    all_pass = random_pass and hardcoded_pass
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {'✅ PHASE 1 SUCCESS!' if all_pass else '❌ NEEDS ITERATION'}")
    print(f"{'='*60}")
    
    return all_pass


def main():
    """Main training loop"""
    
    print("="*60)
    print("🚀 PHASE 1 LOCAL TRAINING - SUBFINDER STRATEGY")
    print("="*60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "scenarios"
    training_path = str(data_dir / "phase1_training.json")
    eval_path = str(data_dir / "phase1_eval.json")
    
    # Create output directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "outputs" / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tensorboard_dir = output_dir / "tensorboard"
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Output Directory: {output_dir}")
    print(f"📊 TensorBoard: tensorboard --logdir={tensorboard_dir}")
    print(f"🌐 Open: http://localhost:6006")
    
    # Create environments
    print("\n🏗️ Creating environments...")
    train_env = DummyVecEnv([lambda: make_env(training_path)])
    
    # ADD VECNORMALIZE WRAPPER (Reward V2 improvement)
    print("   Adding VecNormalize wrapper...")
    train_env = VecNormalize(
        train_env,
        norm_obs=True,         # Normalize observations ✅
        norm_reward=True,      # Normalize rewards ✅
        clip_obs=10.0,         # Clip outliers
        clip_reward=10.0,
        gamma=0.99
    )
    
    # Save normalization stats path
    norm_stats_path = output_dir / "vec_normalize_stats.pkl"
    
    # Create eval env with SAME wrapper structure (CRITICAL!)
    eval_env = DummyVecEnv([lambda: make_env(eval_path)])
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=False,     # Don't normalize rewards during eval
        clip_obs=10.0,
        training=False,        # Important: set to False for eval
        gamma=0.99
    )
    
    print(f"   Training scenarios: 10")
    print(f"   Observation normalization: ENABLED")
    print(f"   Evaluation scenarios: 5")
    
    # Evaluate baselines first
    baseline_results = evaluate_baselines(eval_env, n_episodes=10)
    
    # Create PPO model with UPDATED HYPERPARAMETERS (Reward V2)
    print("\n🤖 Creating PPO agent (V2 - Increased Exploration)...")
    model = PPO(
        "MlpPolicy",
        train_env,
        
        # INCREASED EXPLORATION (from failure analysis)
        learning_rate=1e-3,    # was 3e-4 (faster learning)
        ent_coef=0.05,         # was 0.01 (5x more exploration!)
        
        # MORE FREQUENT UPDATES
        n_steps=512,           # was 2048 (update more often)
        batch_size=128,        # was 64 (larger batches)
        n_epochs=20,           # was 10 (learn more per update)
        
        # UNCHANGED (these were OK)
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        
        verbose=1,
        tensorboard_log=str(tensorboard_dir)
    )
    
    print("   Policy: MLP (Multi-Layer Perceptron)")
    print("   Learning rate: 1e-3 (was 3e-4)")
    print("   Entropy coef: 0.05 (was 0.01 - 5x exploration!)")
    print("   Batch size: 128 (was 64)")
    print("   Timesteps: 100,000")
    
    # Setup callbacks
    print("\n⚙️ Setting up callbacks...")
    
    # Checkpoint every 25k steps
    checkpoint_callback = CheckpointCallback(
        save_freq=25000,
        save_path=str(checkpoints_dir),
        name_prefix="ppo_subfinder_v2"
    )
    
    # Evaluation every 10k steps
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(output_dir / "best_model"),
        log_path=str(output_dir / "eval_logs"),
        eval_freq=10000,
        n_eval_episodes=5,
        deterministic=True,
        render=False
    )
    
    # Custom metrics
    metrics_callback = MetricsCallback()
    
    # Combine callbacks
    callbacks = CallbackList([checkpoint_callback, eval_callback, metrics_callback])
    
    # Train!
    print("\n" + "="*60)
    print("🏋️ STARTING TRAINING")
    print("="*60)
    print("\n💡 TIP: Open TensorBoard to monitor progress:")
    print(f"   tensorboard --logdir={tensorboard_dir}")
    print(f"   http://localhost:6006\n")
    
    try:
        model.learn(
            total_timesteps=100000,
            callback=callbacks,
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user")
    
    # Save final model
    final_model_path = output_dir / "final_model"
    model.save(str(final_model_path))
    print(f"\n💾 Final model saved: {final_model_path}")
    
    # Save VecNormalize stats (CRITICAL for evaluation!)
    train_env.save(str(norm_stats_path))
    print(f"💾 Normalization stats saved: {norm_stats_path}")
    
    # Final evaluation
    print("\n" + "="*60)
    print("📊 FINAL EVALUATION")
    print("="*60)
    
    agent_results = evaluate_agent(model, eval_env, n_episodes=10)
    
    # Check success criteria
    success = check_success_criteria(baseline_results, agent_results)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_to_native(obj):
        """Recursively convert numpy types to Python native types"""
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
        "baselines": convert_to_native(baseline_results),
        "agent": convert_to_native(agent_results),
        "success": success,
        "training_timesteps": 100000
    }
    
    results_file = output_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\n📄 Results saved: {results_file}")
    
    if success:
        print("\n🎉 READY FOR PHASE 2!")
    else:
        print("\n🔄 Iterate on reward function or scenarios before Phase 2")
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
