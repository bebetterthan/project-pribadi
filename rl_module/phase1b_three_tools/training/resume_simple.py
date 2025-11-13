#!/usr/bin/env python3
"""
Simple resume script - load checkpoint and continue training
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, CallbackList
from envs.full_recon_env import FullReconEnv

# Paths
output_dir = Path("../outputs/phase1b_run_20251113_094132")
checkpoint_path = output_dir / "checkpoints" / "ppo_phase1b_75000_steps.zip"
vecnormalize_path = output_dir / "vec_normalize_stats.pkl"
training_data = Path("../data/phase1b_train.json")
test_data = Path("../data/phase1b_test.json")

print("\n" + "="*70)
print("RESUME PHASE 1B TRAINING")
print("="*70)
print(f"\n[Checkpoint]: {checkpoint_path.name}")
print(f"[Current Steps]: 75,000")
print(f"[Remaining]: 75,000 steps (~3-5 hours)")

# Create environment
print("\n[Creating environment]...")
def make_env():
    return FullReconEnv(str(training_data))

env = DummyVecEnv([make_env])

# Load VecNormalize
print("[Loading normalization stats]...")
env = VecNormalize.load(str(vecnormalize_path), env)

# Load model
print("[Loading model]...")
model = PPO.load(str(checkpoint_path), env=env, device='cpu')
print(f"[Model loaded]: {model.num_timesteps:,} steps trained")

# Setup callbacks
print("\n[Setting up callbacks]...")
checkpoint_callback = CheckpointCallback(
    save_freq=25000,
    save_path=str(output_dir / "checkpoints"),
    name_prefix="ppo_phase1b"
)

def make_eval_env():
    return FullReconEnv(str(test_data))

eval_env = DummyVecEnv([make_eval_env])
eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=True, training=False)

eval_callback = EvalCallback(
    eval_env,
    best_model_save_path=str(output_dir / "best_model"),
    log_path=str(output_dir / "eval_logs"),
    eval_freq=10000,
    n_eval_episodes=5,
    deterministic=True
)

callbacks = CallbackList([checkpoint_callback, eval_callback])

# Continue training
print("\n" + "="*70)
print("RESUMING TRAINING")
print("="*70 + "\n")

try:
    model.learn(
        total_timesteps=75000,  # Remaining steps
        callback=callbacks,
        reset_num_timesteps=False,  # Keep counter!
        tb_log_name="phase1b",
        progress_bar=True
    )
    
    # Save final
    print("\n[Saving final model]...")
    model.save(str(output_dir / "final_model_resumed"))
    env.save(str(output_dir / "vec_normalize_final.pkl"))
    
    print("\n" + "="*70)
    print("TRAINING COMPLETED")
    print("="*70)
    print(f"\n[Total Steps]: 150,000")
    print(f"[Final Model]: {output_dir / 'final_model_resumed.zip'}")
    
except KeyboardInterrupt:
    print("\n[WARNING] Training interrupted")
    print(f"[Saving checkpoint at]: {model.num_timesteps:,} steps")
    model.save(str(output_dir / f"interrupted_{model.num_timesteps}"))
    env.save(str(output_dir / "vec_normalize_interrupted.pkl"))
