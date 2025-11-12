"""
PHASE 0: Training Script - Proof of Concept

Train PPO agent on ToyReconEnv to validate RL setup works.

Target: 10,000 steps (30 minutes training)
Success: Agent beats random baseline by >60%

COPILOT PROMPT:
Create minimal training script using Stable-Baselines3:
1. Import ToyReconEnv
2. Wrap with Monitor for logging
3. Create PPO agent with simple config
4. Train for 10,000 steps
5. Save model and log results
6. Compare to random baseline

Usage:
    python train_toy.py
    python train_toy.py --timesteps 20000  # Longer training
"""

import argparse
import os
from pathlib import Path
import time

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent))

from toy_env import ToyReconEnv

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
    import torch
    HAS_SB3 = True
except ImportError:
    print("⚠️  Stable-Baselines3 not installed!")
    print("   Install with: pip install stable-baselines3")
    HAS_SB3 = False


class ProgressCallback(BaseCallback):
    """
    Custom callback to log training progress.
    
    COPILOT: Implement logging of episode rewards and info
    """
    
    def __init__(self, check_freq: int = 100, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.episode_rewards = []
        self.episode_lengths = []
    
    def _on_step(self) -> bool:
        """
        Called at each training step.
        
        COPILOT: Log episode statistics when episode ends
        """
        # Check if episode finished
        if self.locals.get('dones'):
            if self.locals['dones'][0]:
                # Episode ended
                if 'infos' in self.locals and len(self.locals['infos']) > 0:
                    info = self.locals['infos'][0]
                    if 'episode' in info:
                        reward = info['episode']['r']
                        length = info['episode']['l']
                        self.episode_rewards.append(reward)
                        self.episode_lengths.append(length)
                        
                        if self.verbose > 0:
                            print(f"Episode {len(self.episode_rewards)}: "
                                  f"Reward = {reward:.2f}, Length = {length}")
        
        return True


def evaluate_random_baseline(env, num_episodes: int = 10) -> float:
    """
    Evaluate random policy as baseline.
    
    COPILOT: Run episodes with random actions and return average reward
    """
    print(f"\n📊 Evaluating random baseline ({num_episodes} episodes)...")
    
    total_rewards = []
    
    for episode in range(num_episodes):
        obs, info = env.reset()
        episode_reward = 0.0
        done = False
        truncated = False
        
        while not done and not truncated:
            action = env.action_space.sample()  # Random action
            obs, reward, done, truncated, info = env.step(action)
            episode_reward += reward
        
        total_rewards.append(episode_reward)
        if (episode + 1) % 5 == 0:
            print(f"  Episode {episode+1}/{num_episodes}: {episode_reward:.2f}")
    
    avg_reward = sum(total_rewards) / len(total_rewards)
    std_reward = (sum((r - avg_reward) ** 2 for r in total_rewards) / len(total_rewards)) ** 0.5
    
    print(f"\n✅ Random Baseline Results:")
    print(f"   Average Reward: {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min Reward: {min(total_rewards):.2f}")
    print(f"   Max Reward: {max(total_rewards):.2f}")
    
    return avg_reward


def evaluate_trained_agent(model, env, num_episodes: int = 10) -> float:
    """
    Evaluate trained agent.
    
    COPILOT: Run episodes with trained policy and return average reward
    """
    print(f"\n📊 Evaluating trained agent ({num_episodes} episodes)...")
    
    total_rewards = []
    
    for episode in range(num_episodes):
        obs, info = env.reset()
        episode_reward = 0.0
        done = False
        truncated = False
        
        while not done and not truncated:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            episode_reward += reward
        
        total_rewards.append(episode_reward)
        if (episode + 1) % 5 == 0:
            print(f"  Episode {episode+1}/{num_episodes}: {episode_reward:.2f}")
    
    avg_reward = sum(total_rewards) / len(total_rewards)
    std_reward = (sum((r - avg_reward) ** 2 for r in total_rewards) / len(total_rewards)) ** 0.5
    
    print(f"\n✅ Trained Agent Results:")
    print(f"   Average Reward: {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"   Min Reward: {min(total_rewards):.2f}")
    print(f"   Max Reward: {max(total_rewards):.2f}")
    
    return avg_reward


def train(
    total_timesteps: int = 10000,
    learning_rate: float = 3e-4,
    n_steps: int = 256,
    batch_size: int = 64,
    save_dir: str = "../checkpoints/phase0",
    log_dir: str = "../logs/phase0"
):
    """
    Train PPO agent on ToyReconEnv.
    
    COPILOT: Implement complete training pipeline
    """
    if not HAS_SB3:
        print("❌ Cannot train without Stable-Baselines3!")
        return
    
    # Create directories
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    print("🚀 PHASE 0: Proof of Concept Training")
    print("=" * 60)
    print(f"Environment: ToyReconEnv")
    print(f"Algorithm: PPO")
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Learning rate: {learning_rate}")
    print(f"Batch size: {batch_size}")
    print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print("=" * 60)
    
    # Create environment
    print("\n1️⃣ Creating environment...")
    env = ToyReconEnv()
    env = Monitor(env, log_dir)
    print(f"   ✅ Environment created")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")
    
    # Evaluate random baseline
    print("\n2️⃣ Evaluating random baseline...")
    random_baseline = evaluate_random_baseline(env, num_episodes=10)
    
    # Create PPO model
    print("\n3️⃣ Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        verbose=1,
        tensorboard_log=log_dir
    )
    print(f"   ✅ PPO model created")
    
    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=2500,
        save_path=save_dir,
        name_prefix="toy_ppo"
    )
    
    progress_callback = ProgressCallback(check_freq=100, verbose=1)
    
    # Train
    print(f"\n4️⃣ Training for {total_timesteps:,} steps...")
    start_time = time.time()
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, progress_callback],
        progress_bar=True
    )
    
    training_time = time.time() - start_time
    print(f"\n   ✅ Training complete in {training_time:.1f} seconds")
    
    # Save final model
    final_model_path = os.path.join(save_dir, "toy_ppo_final.zip")
    model.save(final_model_path)
    print(f"   💾 Model saved to: {final_model_path}")
    
    # Evaluate trained agent
    print("\n5️⃣ Evaluating trained agent...")
    trained_performance = evaluate_trained_agent(model, env, num_episodes=10)
    
    # Compare results
    print("\n" + "=" * 60)
    print("📊 PHASE 0 RESULTS")
    print("=" * 60)
    print(f"Random Baseline:  {random_baseline:.2f} reward/episode")
    print(f"Trained Agent:    {trained_performance:.2f} reward/episode")
    improvement = ((trained_performance - random_baseline) / abs(random_baseline)) * 100
    print(f"Improvement:      {improvement:+.1f}%")
    print("=" * 60)
    
    # Success criteria check
    print("\n✅ SUCCESS CRITERIA:")
    success_criteria = {
        'Environment runs': True,
        f'Training < 1 hour': training_time < 3600,
        f'Beats random by >60%': improvement > 60,
        f'Reward improves': trained_performance > random_baseline
    }
    
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
    
    all_passed = all(success_criteria.values())
    
    if all_passed:
        print("\n🎉 PHASE 0 SUCCESS! Ready to proceed to Phase 1")
        print("   Next: Implement single-tool environment (subfinder)")
    else:
        print("\n⚠️  Some criteria not met. Debug before proceeding.")
        print("   Check: reward function, state representation, training config")
    
    print(f"\n📈 View training logs: tensorboard --logdir {log_dir}")
    
    env.close()
    
    return model, trained_performance, random_baseline


def main():
    parser = argparse.ArgumentParser(description='PHASE 0: Train toy RL agent')
    parser.add_argument('--timesteps', type=int, default=10000,
                        help='Total training timesteps (default: 10000)')
    parser.add_argument('--learning-rate', type=float, default=3e-4,
                        help='Learning rate')
    parser.add_argument('--save-dir', type=str, default='../checkpoints/phase0',
                        help='Checkpoint directory')
    parser.add_argument('--log-dir', type=str, default='../logs/phase0',
                        help='TensorBoard log directory')
    
    args = parser.parse_args()
    
    train(
        total_timesteps=args.timesteps,
        learning_rate=args.learning_rate,
        save_dir=args.save_dir,
        log_dir=args.log_dir
    )


if __name__ == '__main__':
    main()
