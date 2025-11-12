"""
Train PPO agent on ReconEnv environment.

COPILOT PROMPT:
Create complete training script using Stable-Baselines3 PPO algorithm.

Configuration:
- Algorithm: PPO (Proximal Policy Optimization)
- Policy: MlpPolicy (Multi-Layer Perceptron)
- Learning rate: 3e-4 with linear decay
- Batch size: 64
- N steps: 2048
- N epochs: 10
- Gamma: 0.99 (discount factor)
- GAE lambda: 0.95
- Clip range: 0.2
- Total timesteps: 500,000

Features:
- Checkpoint saving every 50,000 steps
- Evaluation callback every 10,000 steps on held-out scenarios
- TensorBoard logging with custom metrics
- Progress bar with ETA
- Automatic best model saving
- Training metrics tracking

Usage:
    # Basic training
    python train.py
    
    # Custom configuration
    python train.py --timesteps 1000000 --learning-rate 1e-4 --batch-size 128
    
    # Resume from checkpoint
    python train.py --resume checkpoints/recon_ppo_250k.zip
"""

import argparse
import os
from pathlib import Path
from typing import Dict, Any

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
    CallbackList,
    BaseCallback
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import torch

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from envs.recon_env import ReconEnv


class TensorBoardCallback(BaseCallback):
    """
    Custom callback for additional TensorBoard logging.
    
    TODO for Copilot:
    - Log custom metrics every N steps
    - Track episode statistics
    - Log action distribution
    - Log reward components
    """
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
    
    def _on_step(self) -> bool:
        """
        Called at each training step.
        
        TODO for Copilot:
        - Check if episode is done
        - If done, log episode reward and length
        - Log to TensorBoard using self.logger.record()
        - Return True to continue training
        """
        return True


def make_env(scenarios_path: str, max_steps: int = 50, time_limit: int = 600):
    """
    Create and wrap environment.
    
    Args:
        scenarios_path: Path to scenarios JSON
        max_steps: Maximum episode steps
        time_limit: Maximum episode time (seconds)
    
    Returns:
        Wrapped environment
    
    TODO for Copilot:
    - Create ReconEnv
    - Wrap with Monitor for logging
    - Return wrapped env
    """
    pass


def train(
    total_timesteps: int = 500000,
    learning_rate: float = 3e-4,
    batch_size: int = 64,
    n_steps: int = 2048,
    n_epochs: int = 10,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_range: float = 0.2,
    save_dir: str = "./checkpoints",
    log_dir: str = "./logs",
    scenarios_path: str = "data/scenarios/training.json",
    test_scenarios_path: str = "data/scenarios/test.json",
    resume_from: str = None,
    device: str = "auto"
):
    """
    Train PPO agent on ReconEnv.
    
    Args:
        total_timesteps: Total training timesteps
        learning_rate: Learning rate for optimizer
        batch_size: Minibatch size for PPO updates
        n_steps: Steps per rollout
        n_epochs: Epochs per PPO update
        gamma: Discount factor
        gae_lambda: GAE lambda parameter
        clip_range: PPO clipping parameter
        save_dir: Directory for checkpoints
        log_dir: Directory for TensorBoard logs
        scenarios_path: Training scenarios path
        test_scenarios_path: Test scenarios path (for evaluation)
        resume_from: Path to checkpoint to resume from
        device: Device for training (cpu, cuda, auto)
    
    TODO for Copilot:
    1. Create directories (save_dir, log_dir)
    2. Create training environment (with Monitor wrapper)
    3. Create evaluation environment (separate from training)
    4. Setup callbacks:
       - CheckpointCallback (save every 50k steps)
       - EvalCallback (eval every 10k steps)
       - TensorBoardCallback (custom metrics)
    5. Initialize PPO model (or load from resume_from)
    6. Train with model.learn()
    7. Save final model
    8. Print training summary
    """
    
    # Create directories
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    print("🚀 Starting RL Training")
    print(f"   Total timesteps: {total_timesteps:,}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Batch size: {batch_size}")
    print(f"   Device: {device}")
    print()
    
    # TODO: Implement training logic
    # Create env, setup callbacks, train
    
    print("✅ Training complete!")
    print(f"   Checkpoints saved to: {save_dir}")
    print(f"   Logs saved to: {log_dir}")
    print(f"   View with: tensorboard --logdir {log_dir}")


def main():
    parser = argparse.ArgumentParser(description='Train RL agent on ReconEnv')
    
    # Training parameters
    parser.add_argument('--timesteps', type=int, default=500000,
                        help='Total training timesteps')
    parser.add_argument('--learning-rate', type=float, default=3e-4,
                        help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=64,
                        help='Batch size')
    parser.add_argument('--n-steps', type=int, default=2048,
                        help='Steps per rollout')
    parser.add_argument('--n-epochs', type=int, default=10,
                        help='Epochs per update')
    parser.add_argument('--gamma', type=float, default=0.99,
                        help='Discount factor')
    parser.add_argument('--gae-lambda', type=float, default=0.95,
                        help='GAE lambda')
    parser.add_argument('--clip-range', type=float, default=0.2,
                        help='PPO clip range')
    
    # Directories
    parser.add_argument('--save-dir', type=str, default='./checkpoints',
                        help='Checkpoint directory')
    parser.add_argument('--log-dir', type=str, default='./logs',
                        help='TensorBoard log directory')
    
    # Data
    parser.add_argument('--scenarios', type=str, default='data/scenarios/training.json',
                        help='Training scenarios path')
    parser.add_argument('--test-scenarios', type=str, default='data/scenarios/test.json',
                        help='Test scenarios path')
    
    # Resume
    parser.add_argument('--resume', type=str, default=None,
                        help='Checkpoint to resume from')
    
    # Device
    parser.add_argument('--device', type=str, default='auto',
                        choices=['auto', 'cpu', 'cuda'],
                        help='Training device')
    
    args = parser.parse_args()
    
    # Start training
    train(
        total_timesteps=args.timesteps,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        n_steps=args.n_steps,
        n_epochs=args.n_epochs,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_range=args.clip_range,
        save_dir=args.save_dir,
        log_dir=args.log_dir,
        scenarios_path=args.scenarios,
        test_scenarios_path=args.test_scenarios,
        resume_from=args.resume,
        device=args.device
    )


if __name__ == '__main__':
    main()
