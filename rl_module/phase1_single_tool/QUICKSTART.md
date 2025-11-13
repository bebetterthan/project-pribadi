# 🚀 QUICK START: Phase 1 Training

## Prerequisites

✅ Scenarios generated (10 training, 5 eval) - DONE
✅ Environment implemented (SubfinderHttpxEnv, 22-dim state) - DONE  
✅ Baselines tested (Random: 465.84, Hardcoded: 659.21) - DONE
✅ Performance verified (25,043 steps/sec) - DONE

## Training Steps

### 1. Open Terminal #1 - Start Training

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1_single_tool"
python train_local.py
```

**What happens:**

- Creates `outputs/run_YYYYMMDD_HHMMSS/` directory
- Evaluates baselines first (random, hardcoded)
- Trains PPO agent for 100,000 timesteps (~5-10 minutes)
- Saves checkpoints every 25k steps
- Evaluates every 10k steps
- Shows progress bar

**Expected output:**

```
🚀 PHASE 1 LOCAL TRAINING - SUBFINDER + HTTPX STRATEGY
============================================================

📁 Output Directory: outputs/run_20251113_XXXXXX
📊 TensorBoard: tensorboard --logdir=outputs/run_20251113_XXXXXX/tensorboard
🌐 Open: http://localhost:6006

🏗️ Creating environments...
   Training scenarios: 10
   Evaluation scenarios: 5

📊 EVALUATING BASELINES
============================================================

🎲 Random Agent...
   Mean: 465.84 ± 214.11

🔧 Hardcoded Agent...
   Mean: 659.21 ± 414.82

🤖 Creating PPO agent...
   Policy: MLP
   Learning rate: 3e-4
   Timesteps: 100,000

🏋️ STARTING TRAINING
============================================================

💡 TIP: Open TensorBoard to monitor progress:
   tensorboard --logdir=outputs/run_20251113_XXXXXX/tensorboard
   http://localhost:6006
```

### 2. Open Terminal #2 - Start TensorBoard (WHILE TRAINING)

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1_single_tool"
python start_tensorboard.py
```

**OR manually:**

```powershell
tensorboard --logdir=outputs --port=6006
```

### 3. Open Browser - Monitor Real-Time

Navigate to:

```
http://localhost:6006
```

## 📊 What to Monitor in TensorBoard

### **SCALARS Tab** (Main Metrics)

#### 1. Rollout Metrics (MOST IMPORTANT)

- `rollout/ep_rew_mean` - **Average episode reward**
  - Should increase from ~465 (random) to >931 (2x target)
  - Look for steady upward trend
- `rollout/ep_len_mean` - **Average episode length**
  - Should stabilize around 2-3 steps (subfinder + httpx)
  - Lower is more efficient

#### 2. Custom Metrics (Phase Details)

- `custom/episode_reward` - Individual episode rewards
- `custom/subdomains_found` - Subdomains discovered per episode
- `custom/live_hosts_found` - **NEW: Live hosts found (HTTPX)**
- `custom/efficiency` - Reward per step (higher = better)

#### 3. Training Metrics (Learning Progress)

- `train/learning_rate` - Should stay at 3e-4
- `train/policy_loss` - Should decrease over time
- `train/value_loss` - Should decrease over time
- `train/entropy_loss` - Exploration bonus

#### 4. Time Metrics

- `time/fps` - Training speed (steps/second)
- `time/total_timesteps` - Progress to 100k

### **Charts You Want to See**

```
Episode Reward (rollout/ep_rew_mean):
465 ────┐
        │     ╱╲ ╱╲
        │   ╱    ╲ ╲  ╱╲
        │ ╱        ╲╱  ╲╱╲
        └────────────────────► timesteps
        0   25k  50k  75k  100k

Target: Finish above 931 (2x random)
```

### **Good Signs ✅**

- Reward curve trending UP
- Episode length STABLE (2-3 steps)
- Low variance after 50k steps
- Training speed >1000 fps

### **Warning Signs ⚠️**

- Flat reward curve (not learning)
- High variance throughout (unstable)
- Reward drops suddenly (catastrophic forgetting)

## 📁 Output Files

After training completes (~5-10 min):

```
outputs/run_20251113_XXXXXX/
├── tensorboard/           # Open in TensorBoard
├── checkpoints/
│   ├── ppo_subfinder_25000_steps.zip
│   ├── ppo_subfinder_50000_steps.zip
│   ├── ppo_subfinder_75000_steps.zip
│   └── ppo_subfinder_100000_steps.zip
├── best_model/
│   └── best_model.zip     # Best performing model
├── final_model.zip        # Model at 100k steps
├── eval_logs/             # Evaluation results
└── results.json           # Final summary

results.json contains:
{
  "baselines": {
    "random": {"mean": 465.84, "std": 214.11},
    "hardcoded": {"mean": 659.21, "std": 414.82}
  },
  "agent": {
    "mean": ???,  # Should be >931
    "std": ???
  },
  "success": true/false,
  "training_timesteps": 100000
}
```

## 🎯 Success Criteria Check

Training script automatically checks:

1. **Beat Random by >100%**: Agent reward / 465.84 > 2.0 ✅
2. **Beat Hardcoded by >30%**: Agent reward / 659.21 > 1.3 ✅

If BOTH pass → **✅ PHASE 1 SUCCESS - Ready for Phase 2!**

## 🔧 Troubleshooting

### TensorBoard not opening?

```powershell
# Kill existing processes
taskkill /F /IM tensorboard.exe

# Restart on different port
tensorboard --logdir=outputs --port=6007
```

### Training too slow?

Check `time/fps` in TensorBoard:

- Should be >1000 fps
- We achieved 25,043 steps/sec (25x target!)

### Reward not increasing?

- Wait until 25k steps (early training is noisy)
- Check if all 4 reward components are working
- Verify scenario diversity (10 training scenarios)

### Want to stop early?

Press `Ctrl+C` in training terminal

- Model saved at last checkpoint
- Can resume from checkpoint if needed

## 💡 Tips

1. **Start TensorBoard BEFORE training** for full history
2. **Smooth curves** with slider (top-left in TensorBoard)
3. **Compare runs** by running training multiple times
4. **Episode length** should be 2 (1 subfinder + 1 httpx)
5. **Training time** ~5-10 minutes for 100k steps

## 🎉 Expected Results

Based on our sandbox design:

- **Random baseline**: 465.84 ± 214.11
- **Hardcoded baseline**: 659.21 ± 414.82
- **RL Agent (expected)**: 931-1200 (2x-2.5x random)

Agent should learn:

- Use **passive subfinder** for small targets
- Use **active/comprehensive** for larger targets
- Use **quick HTTPX** when few hosts discovered
- Use **thorough/comprehensive HTTPX** when many hosts

---

**Ready? Let's train! 🚀**

Open 2 terminals and run the commands above.
