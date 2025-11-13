# 📊 Phase 1 Local Training & Monitoring

Panduan lengkap untuk training dan monitoring di local machine.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd rl_module
pip install -r requirements.txt
```

### 2. Start Training

```bash
cd phase1_single_tool
python train_local.py
```

### 3. Monitor dengan TensorBoard (Terminal Terpisah)

```bash
cd phase1_single_tool
python start_tensorboard.py
```

Atau manual:

```bash
tensorboard --logdir=outputs --port=6006
```

### 4. Open Browser

```
http://localhost:6006
```

---

## 📈 Monitoring Dashboard

### **TensorBoard Metrics**

#### 1. **Rollout Metrics**

- `rollout/ep_rew_mean` - Average episode reward (UTAMA!)
- `rollout/ep_len_mean` - Average episode length
- Target: Reward naik, length turun (lebih efisien)

#### 2. **Custom Metrics**

- `custom/episode_reward` - Individual episode rewards
- `custom/episode_length` - Individual episode lengths
- `custom/subdomains_found` - Subdomains discovered per episode
- `custom/efficiency` - Reward per step (higher = better)

#### 3. **Training Metrics**

- `train/learning_rate` - Learning rate schedule
- `train/policy_loss` - Policy network loss
- `train/value_loss` - Value network loss
- `train/entropy_loss` - Exploration bonus

#### 4. **Time Metrics**

- `time/fps` - Training speed (steps per second)
- `time/total_timesteps` - Total training steps

---

## 📊 What to Look For

### ✅ **Good Signs**

1. **Episode reward trending UP** 📈

   - Means agent is learning
   - Should see steady improvement over time

2. **Episode length trending DOWN** 📉

   - Agent solving faster
   - More efficient strategy

3. **Efficiency (reward/step) INCREASING** ⚡

   - Better decisions per action
   - Strategic improvement

4. **Low variance after 50k steps** 🎯
   - Stable policy
   - Convergence

### ⚠️ **Warning Signs**

1. **Flat reward curve**

   - Not learning
   - May need hyperparameter tuning

2. **High variance throughout**

   - Unstable training
   - Reduce learning rate

3. **Reward drops suddenly**
   - Catastrophic forgetting
   - Check if too aggressive

---

## 🎯 Success Criteria

Training selesai setelah **100,000 timesteps** (~5-10 menit).

### **Gate Requirements:**

- ✅ Beat Random by >100% (2x improvement)
- ✅ Beat Hardcoded by >30% (1.3x improvement)
- ✅ Observable learning curve in TensorBoard
- ✅ Stable policy (low variance)

**Baselines (reference):**

- Random: ~859 ± 156
- Hardcoded: ~681 ± 164

**Target RL Agent:**

- Mean reward: **>1718** (2x random)
- Mean reward: **>885** (1.3x hardcoded)
- Actual target: **>1718** (stricter criterion)

---

## 📁 Output Structure

```
phase1_single_tool/outputs/run_YYYYMMDD_HHMMSS/
├── tensorboard/          # TensorBoard logs
│   └── PPO_1/
├── checkpoints/          # Model checkpoints every 25k steps
│   ├── ppo_subfinder_25000_steps.zip
│   ├── ppo_subfinder_50000_steps.zip
│   ├── ppo_subfinder_75000_steps.zip
│   └── ppo_subfinder_100000_steps.zip
├── best_model/           # Best model during training
│   └── best_model.zip
├── final_model.zip       # Final model at 100k steps
├── eval_logs/            # Evaluation logs
└── results.json          # Final results summary
```

---

## 🔧 Training Configuration

**Algorithm:** PPO (Proximal Policy Optimization)

**Hyperparameters:**

```python
learning_rate = 3e-4      # Adam optimizer
n_steps = 2048            # Steps per rollout
batch_size = 64           # Minibatch size
n_epochs = 10             # Gradient update epochs
gamma = 0.99              # Discount factor
gae_lambda = 0.95         # GAE parameter
clip_range = 0.2          # PPO clip range
ent_coef = 0.01           # Entropy bonus
```

**Environment:**

- State: 15 dimensions (normalized [0,1])
- Actions: 3 (passive, active, comprehensive)
- Scenarios: 10 training, 5 evaluation

---

## 🎮 Manual Evaluation

Setelah training, test manual:

```python
from stable_baselines3 import PPO
from envs.subfinder_env import SubfinderEnv

# Load trained model
model = PPO.load("outputs/run_XXXXXX_XXXXXX/final_model.zip")

# Create environment
env = SubfinderEnv("../data/scenarios/phase1_eval.json")

# Run episode
obs, info = env.reset()
done = False
total_reward = 0

while not done:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    done = terminated or truncated

    print(f"Action: {action}, Reward: {reward:.2f}")

print(f"Total: {total_reward:.2f}, Found: {info['total_subdomains_found']}")
```

---

## 🐛 Troubleshooting

### Problem: TensorBoard tidak bisa dibuka

```bash
# Kill existing TensorBoard
taskkill /F /IM tensorboard.exe

# Restart dengan port berbeda
tensorboard --logdir=outputs --port=6007
```

### Problem: Training lambat

- Check: Apakah environment cukup cepat? (target >1000 steps/sec)
- Reduce: n_steps atau batch_size
- Check: CPU usage (seharusnya high)

### Problem: Reward tidak naik

- Check: Apakah random/hardcoded baseline reasonable?
- Try: Increase ent_coef (more exploration)
- Try: Reduce learning_rate (more stable)
- Check: Reward function balance (4 components)

### Problem: High variance

- Try: Reduce learning_rate (3e-5 instead of 3e-4)
- Try: Increase batch_size (128 instead of 64)
- Check: Scenario diversity (should be balanced)

---

## 📝 Tips

1. **Training Time**

   - 100k steps ≈ 5-10 menit di laptop modern
   - Monitor TensorBoard dari awal
   - Checkpoint setiap 25k steps (safety)

2. **TensorBoard Best Practices**

   - Refresh page untuk update terbaru
   - Smooth curves dengan slider (kiri atas)
   - Compare multiple runs (run training multiple times)

3. **Hyperparameter Tuning**

   - Jangan tune sebelum melihat baseline belajar
   - Start dengan defaults
   - Tune hanya jika stuck

4. **Debugging**
   - Check performance test passed (>1000 steps/sec)
   - Verify reward breakdown makes sense
   - Test baselines first (should be reasonable)

---

## 🎯 Next Steps

**If SUCCESS (beats criteria):**

```bash
# Proceed to Phase 2
cd ../phase2_multi_tool
```

**If FAIL (below criteria):**

1. Analyze TensorBoard curves
2. Check reward component balance
3. Verify scenario diversity
4. Consider reward function iteration
5. Re-run training with adjusted hyperparameters

---

## 📞 Need Help?

Check these in order:

1. ✅ All tests passing? (`pytest tests/ -v`)
2. ✅ Baselines reasonable? (`python baselines/random_agent.py`)
3. ✅ Environment fast? (>1000 steps/sec in tests)
4. ✅ Scenarios diverse? (check `data/scenarios/phase1_training.json`)
5. ✅ TensorBoard accessible? (http://localhost:6006)

---

**Happy Training! 🚀**
