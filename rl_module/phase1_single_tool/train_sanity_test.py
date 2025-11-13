"""
QUICK SANITY TEST - Train for 10k steps only
Verifies: Reward V2 + new hyperparameters work without errors
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from envs.subfinder_httpx_env import SubfinderHttpxEnv

def make_env(scenarios_path: str):
    env = SubfinderHttpxEnv(scenarios_path=scenarios_path)
    env = Monitor(env)
    return env

print("🧪 QUICK SANITY TEST - 10k steps")
print("="*60)

# Paths
data_dir = Path(__file__).parent.parent / "data" / "scenarios"
training_path = str(data_dir / "phase1_training.json")

# Create environment
print("\n🏗️ Creating environment...")
train_env = DummyVecEnv([lambda: make_env(training_path)])

# Add VecNormalize
print("   Adding VecNormalize...")
train_env = VecNormalize(
    train_env,
    norm_obs=True,
    norm_reward=True,
    clip_obs=10.0,
    clip_reward=10.0,
    gamma=0.99
)

# Create PPO model with V2 hyperparameters
print("\n🤖 Creating PPO agent (V2 hyperparameters)...")
model = PPO(
    "MlpPolicy",
    train_env,
    learning_rate=1e-3,    # Increased
    ent_coef=0.05,         # Increased
    n_steps=512,           # Decreased
    batch_size=128,        # Increased
    n_epochs=20,           # Increased
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1
)

print(f"   Learning rate: 1e-3")
print(f"   Entropy coef: 0.05 (5x baseline)")
print(f"   Batch size: 128")

# Train for 10k steps ONLY
print("\n🏋️ Training for 10,000 steps...")
print("   (Sanity check - should take ~2-3 minutes)\n")

try:
    model.learn(
        total_timesteps=10000,
        progress_bar=True
    )
    print("\n✅ Training completed successfully!")
    print("   No errors - ready for full training! 🎉")
    
except Exception as e:
    print(f"\n❌ Error during training: {e}")
    print("   Fix error before full training!")
    raise

print("\n📊 Quick Stats Check:")
print("   If you saw rewards trending positive -> ✅ GOOD")
print("   If entropy stayed >0.5 -> ✅ GOOD")
print("   If no crashes/errors -> ✅ GOOD")
print("\n🚀 Ready for full 100k training!")
