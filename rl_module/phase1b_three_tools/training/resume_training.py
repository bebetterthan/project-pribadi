#!/usr/bin/env python3
"""
Resume Phase 1B training from latest checkpoint
"""

import os
import sys
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import CallbackList
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from envs.full_recon_env import FullReconEnv
from training.train_phase1b_local import (
    Phase1BMetricsCallback,
    setup_checkpoint_callback,
    setup_eval_callback
)

def find_latest_checkpoint():
    """Find the latest checkpoint in outputs directory"""
    outputs_dir = Path(__file__).parent.parent / "outputs"
    
    # Find latest run directory
    run_dirs = sorted(outputs_dir.glob("phase1b_run_*"), reverse=True)
    if not run_dirs:
        print("[ERROR] No training runs found")
        return None, None
    
    latest_run = run_dirs[0]
    print(f"[Latest Run]: {latest_run.name}")
    
    # Find checkpoints
    checkpoint_dir = latest_run / "checkpoints"
    if not checkpoint_dir.exists():
        print("[ERROR] No checkpoints directory found")
        return None, None
    
    checkpoints = sorted(checkpoint_dir.glob("rl_model_*_steps.zip"), 
                        key=lambda x: int(x.stem.split('_')[2]))
    
    if not checkpoints:
        print("[ERROR] No checkpoints found")
        return None, None
    
    latest_checkpoint = checkpoints[-1]
    steps = int(latest_checkpoint.stem.split('_')[2])
    
    print(f"[Latest Checkpoint]: {latest_checkpoint.name} ({steps:,} steps)")
    
    return latest_run, latest_checkpoint

def resume_training():
    """Resume training from latest checkpoint"""
    
    print("\n" + "="*70)
    print("RESUME PHASE 1B TRAINING")
    print("="*70 + "\n")
    
    # Find latest checkpoint
    latest_run, checkpoint_path = find_latest_checkpoint()
    if not latest_run or not checkpoint_path:
        return
    
    # Extract current steps
    current_steps = int(checkpoint_path.stem.split('_')[2])
    remaining_steps = 150_000 - current_steps
    
    print(f"[Current Progress]: {current_steps:,} / 150,000 steps")
    print(f"[Remaining]: {remaining_steps:,} steps (~{remaining_steps//512} iterations)")
    print(f"[Estimated Time]: {remaining_steps//200//60} - {remaining_steps//150//60} minutes\n")
    
    # Setup environment (same as original training)
    training_path = Path(__file__).parent.parent / "data" / "phase1b_train.json"
    
    def make_env():
        return FullReconEnv(str(training_path))
    
    print("[Creating environment]...")
    env = DummyVecEnv([make_env])
    
    # Load VecNormalize stats if available
    vecnormalize_path = latest_run / "vecnormalize.pkl"
    if vecnormalize_path.exists():
        print("[Loading VecNormalize stats]...")
        env = VecNormalize.load(str(vecnormalize_path), env)
    else:
        print("[WARNING] VecNormalize stats not found, creating new...")
        env = VecNormalize(env, norm_obs=True, norm_reward=True)
    
    # Load model
    print(f"[Loading model from checkpoint]...")
    model = PPO.load(
        str(checkpoint_path),
        env=env,
        device='cpu'
    )
    
    print(f"[Model loaded successfully]")
    print(f"   Total timesteps trained: {model.num_timesteps:,}")
    
    # Setup callbacks (reuse from original training)
    tensorboard_dir = latest_run / "tensorboard"
    checkpoint_dir = latest_run / "checkpoints"
    
    checkpoint_callback = setup_checkpoint_callback(
        str(checkpoint_dir),
        save_freq=25_000,
        name_prefix="rl_model"
    )
    
    test_path = Path(__file__).parent.parent / "data" / "phase1b_test.json"
    eval_callback = setup_eval_callback(
        str(test_path),
        str(checkpoint_dir),
        eval_freq=10_000
    )
    
    metrics_callback = Phase1BMetricsCallback()
    
    callbacks = CallbackList([checkpoint_callback, eval_callback, metrics_callback])
    
    # Continue training
    print("\n" + "="*70)
    print("RESUMING TRAINING")
    print("="*70 + "\n")
    
    model.learn(
        total_timesteps=remaining_steps,
        callback=callbacks,
        reset_num_timesteps=False,  # IMPORTANT: Don't reset counter!
        tb_log_name="phase1b",
        progress_bar=True
    )
    
    # Save final model
    final_model_path = latest_run / "final_model.zip"
    model.save(str(final_model_path))
    env.save(str(latest_run / "vecnormalize_final.pkl"))
    
    print(f"\n[SAVED] Final model to {final_model_path}")
    print("[TRAINING RESUMED AND COMPLETED]")

if __name__ == "__main__":
    resume_training()
