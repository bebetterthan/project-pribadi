# 🚀 Google Colab Setup Guide

## TL;DR

**Upload ke Colab tidak sesederhana drag-and-drop!** Ada beberapa setup khusus yang perlu dilakukan:

1. **Enable GPU** ⚡ (kalau nggak, training 1 jam jadi 3 jam)
2. **Mount Google Drive** 💾 (biar checkpoint tidak hilang)
3. **Install dependencies** 📦 (Colab tidak punya Gymnasium/SB3 by default)
4. **Upload/embed environment code** 📝 (toy_env.py)
5. **Run training** 🤖 (~30 menit)

---

## 📋 Quick Start (30 menit)

### Option 1: Upload Notebook (Recommended) ✅

1. **Upload notebook ke Colab**:

   - Buka https://colab.research.google.com
   - Click `File` > `Upload notebook`
   - Upload `rl_module/notebooks/Phase0_Colab_Training.ipynb`

2. **Enable GPU**:

   - Click `Runtime` > `Change runtime type`
   - Hardware accelerator: **GPU** (T4)
   - Click `Save`

3. **Run all cells**:

   - Click `Runtime` > `Run all` (atau Ctrl+F9)
   - Notebook akan otomatis:
     - Check GPU
     - Mount Google Drive (kamu akan diminta authorize)
     - Install dependencies
     - Embed environment code
     - Train agent
     - Evaluate results
     - Compare with baseline

4. **Wait ~30 minutes** ⏱️

   - Training akan berjalan otomatis
   - TensorBoard akan show live progress
   - Final result akan show success criteria

5. **Download checkpoint** 💾
   - Run last cell untuk download `.zip` file
   - Atau ambil dari Google Drive: `MyDrive/agent_p_rl/checkpoints/`

### Option 2: GitHub (If you have repo)

```python
# Di Colab notebook, run:
!git clone https://github.com/your-username/agent-p-rl.git
%cd agent-p-rl/rl_module/phase0_toy
!pip install -r ../requirements.txt
!python train_toy.py
```

---

## 🔧 Manual Setup (Detail)

Kalau kamu mau setup manual step-by-step:

### Step 1: Check GPU

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

**Expected Output**:

```
CUDA available: True
GPU: Tesla T4
```

**If False**:

- Click `Runtime` > `Change runtime type` > GPU

### Step 2: Mount Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')

# Create workspace
import os
WORKSPACE = '/content/drive/MyDrive/agent_p_rl'
os.makedirs(f"{WORKSPACE}/checkpoints", exist_ok=True)
os.makedirs(f"{WORKSPACE}/logs", exist_ok=True)
```

**Expected Output**:

```
Mounted at /content/drive
✅ Workspace ready: /content/drive/MyDrive/agent_p_rl
```

**If Authorization Error**:

- Click link yang muncul
- Login dengan Google account
- Copy authorization code
- Paste ke Colab

### Step 3: Install Dependencies

```python
!pip install -q gymnasium stable-baselines3[extra] tensorboard

# Verify
import gymnasium as gym
from stable_baselines3 import PPO
print("✅ Dependencies installed!")
```

**Time**: ~2 menit

### Step 4: Upload Environment Code

**Option A: Upload File** (kalau filenya ada di local):

```python
from google.colab import files
uploaded = files.upload()  # Choose toy_env.py
```

**Option B: Embed Code** (recommended):

Notebook sudah include full `ToyReconEnv` class di cell 4. **Tidak perlu upload file!**

### Step 5: Train

```python
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

env = ToyReconEnv()
env = Monitor(env)

model = PPO("MlpPolicy", env, verbose=1,
            tensorboard_log=f"{WORKSPACE}/logs")

model.learn(total_timesteps=10000, progress_bar=True)
model.save(f"{WORKSPACE}/checkpoints/toy_ppo_final")
```

**Time**: ~30 menit on GPU, ~1 jam on CPU

**Expected Output**:

```
| rollout/           |          |
|    ep_len_mean     | 8.5      |
|    ep_rew_mean     | 45.2     |
| time/              |          |
|    fps             | 125      |
|    total_timesteps | 10000    |
```

### Step 6: Evaluate

```python
# Evaluate random baseline
def evaluate_random(env, num_episodes=10):
    rewards = []
    for _ in range(num_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        done = False
        truncated = False

        while not done and not truncated:
            action = env.action_space.sample()
            obs, reward, done, truncated, _ = env.step(action)
            episode_reward += reward

        rewards.append(episode_reward)

    return sum(rewards) / len(rewards)

random_avg = evaluate_random(env)
print(f"Random baseline: {random_avg:.2f}")

# Evaluate trained agent
def evaluate_trained(model, env, num_episodes=10):
    rewards = []
    for _ in range(num_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        done = False
        truncated = False

        while not done and not truncated:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, _ = env.step(action)
            episode_reward += reward

        rewards.append(episode_reward)

    return sum(rewards) / len(rewards)

trained_avg = evaluate_trained(model, env)
print(f"Trained agent: {trained_avg:.2f}")

improvement = ((trained_avg - random_avg) / abs(random_avg)) * 100
print(f"Improvement: {improvement:+.1f}%")

if improvement > 60:
    print("✅ PHASE 0 SUCCESS!")
else:
    print("❌ Failed. Train longer or debug.")
```

**Expected Output**:

```
Random baseline: 25.3
Trained agent: 52.8
Improvement: +108.7%
✅ PHASE 0 SUCCESS!
```

---

## 💾 Download Results

### Option 1: Download via Colab

```python
from google.colab import files
files.download(f"{WORKSPACE}/checkpoints/toy_ppo_final.zip")
```

### Option 2: Copy from Google Drive

1. Buka Google Drive
2. Navigate ke `MyDrive/agent_p_rl/checkpoints/`
3. Download `toy_ppo_final.zip`
4. Extract ke local `rl_module/checkpoints/phase0/`

---

## 📈 View TensorBoard

```python
%load_ext tensorboard
%tensorboard --logdir {WORKSPACE}/logs
```

Kamu akan lihat:

- **Reward curve** (should increase over time)
- **Episode length** (should stabilize)
- **Learning rate** (should decrease)
- **Policy loss** (should decrease)

**Good Training Signs**:

- ✅ Reward meningkat dari ~25 ke ~50+
- ✅ Episode length stabil di 6-10 steps
- ✅ Policy loss turun dari 0.1 ke 0.01

**Bad Training Signs**:

- ❌ Reward flat (tidak naik)
- ❌ Episode length random (tidak stabil)
- ❌ Policy loss naik atau oscillate

---

## 🐛 Troubleshooting

### Issue 1: "RuntimeError: CUDA out of memory"

**Solution**:

```python
# Reduce batch size
model = PPO("MlpPolicy", env, batch_size=32)  # default: 64
```

Or:

- Restart runtime: `Runtime` > `Restart runtime`
- Clear output: `Edit` > `Clear all outputs`

### Issue 2: "No module named 'gymnasium'"

**Solution**:

```python
!pip install --upgrade gymnasium stable-baselines3
```

### Issue 3: Training sangat lambat (< 10 steps/second)

**Check GPU**:

```python
import torch
print(torch.cuda.is_available())  # Should be True
```

If False:

- Enable GPU: `Runtime` > `Change runtime type` > GPU

### Issue 4: Google Drive mount failed

**Solution**:

- Clear browser cache
- Use Incognito mode
- Try different Google account
- Or skip Drive mount (checkpoints will be lost on disconnect)

### Issue 5: Colab disconnected (training lost!)

**Prevention**:

```python
# Use checkpoint callback (already in notebook)
from stable_baselines3.common.callbacks import CheckpointCallback

checkpoint_callback = CheckpointCallback(
    save_freq=2500,
    save_path=f"{WORKSPACE}/checkpoints",
    name_prefix="toy_ppo"
)

model.learn(total_timesteps=10000, callback=checkpoint_callback)
```

Now checkpoints saved every 2500 steps. If disconnect, load last checkpoint:

```python
model = PPO.load(f"{WORKSPACE}/checkpoints/toy_ppo_7500_steps")
model.learn(total_timesteps=2500)  # Continue training
```

### Issue 6: "NotImplementedError: Box(0.0, 1.0, (5,))"

**Solution**: Update Gymnasium

```python
!pip install --upgrade gymnasium
```

---

## 📊 Expected Results

### Phase 0 Success Criteria

| Metric          | Target     | Expected       |
| --------------- | ---------- | -------------- |
| Training time   | < 1 hour   | ~30 min on GPU |
| Random baseline | -          | 20-30 reward   |
| Trained agent   | -          | 50-70 reward   |
| Improvement     | > 60%      | 80-120%        |
| Reward trend    | Increasing | ✅             |

### Example Run

```
📊 PHASE 0 RESULTS
============================================================
Random Baseline:  25.3 ± 8.1
Trained Agent:    58.7 ± 5.2

Improvement:      +132.0%
============================================================

✅ SUCCESS CRITERIA:
   ✅ Environment runs
   ✅ Training < 1 hour
   ✅ Beats random by >60%
   ✅ Reward improves

🎉 PHASE 0 SUCCESS! Ready to proceed to Phase 1
```

---

## 🎯 Next Steps After Phase 0

### If Success ✅

1. **Download checkpoint**:

   ```
   MyDrive/agent_p_rl/checkpoints/toy_ppo_final.zip
   ```

2. **Copy ke local**:

   ```
   rl_module/checkpoints/phase0/toy_ppo_final.zip
   ```

3. **Proceed to Phase 1**:
   - Implement single-tool environment (subfinder)
   - Train on Colab lagi (~3 hours)
   - Repeat success validation

### If Failed ❌

**Don't proceed!** Debug first:

1. **Check TensorBoard**: Reward curve should increase
2. **Try longer training**: 20k steps instead of 10k
3. **Check environment**: Run test episode manually
4. **Verify GPU**: Should be enabled
5. **Ask for help**: Show TensorBoard screenshot + error message

---

## 💡 Tips & Best Practices

### 1. Save Work Frequently

```python
# Save checkpoint every 5 minutes
import time
start = time.time()

while model.num_timesteps < 10000:
    model.learn(total_timesteps=1000)

    if time.time() - start > 300:  # 5 minutes
        model.save(f"{WORKSPACE}/checkpoints/backup_{model.num_timesteps}")
        start = time.time()
```

### 2. Monitor Training Live

```python
# Print progress every 1000 steps
from stable_baselines3.common.callbacks import BaseCallback

class ProgressCallback(BaseCallback):
    def _on_step(self):
        if self.n_calls % 1000 == 0:
            print(f"Step {self.n_calls}: reward={self.locals['rewards'][-1]:.2f}")
        return True

model.learn(total_timesteps=10000, callback=ProgressCallback())
```

### 3. Compare Multiple Runs

```python
# Train 3 agents with different seeds
seeds = [42, 123, 999]
results = []

for seed in seeds:
    env = ToyReconEnv()
    model = PPO("MlpPolicy", env, seed=seed)
    model.learn(total_timesteps=10000)

    avg_reward = evaluate_trained(model, env)
    results.append(avg_reward)
    print(f"Seed {seed}: {avg_reward:.2f}")

print(f"Average: {sum(results)/len(results):.2f}")
```

### 4. Debug with Verbose Logs

```python
# Enable detailed logging
model = PPO("MlpPolicy", env, verbose=2)  # verbose=2 for debug info
```

### 5. Keep Colab Alive

Colab disconnects after 90 minutes idle. To prevent:

```javascript
// Run this in browser console (F12)
function ClickConnect() {
  console.log("Clicking connect button");
  document.querySelector("colab-connect-button").click();
}
setInterval(ClickConnect, 60000);
```

Or use Colab Pro ($10/month) untuk longer sessions.

---

## 🎁 Bonus: Run All Phases in Colab

Kalau kamu mau train semua phases di Colab:

1. **Phase 0**: 30 min (notebook provided)
2. **Phase 1**: 3 hours (coming soon)
3. **Phase 2**: 8 hours (coming soon)
4. **Phase 3**: 20 hours (coming soon - split into overnight runs)

**Total**: ~30 hours training → Bisa dilakukan dalam 1 minggu kalau run overnight.

**Colab Free Limits**:

- 12 hours max continuous runtime
- Total 100 GPU hours per week

**Strategy**:

- Phase 0: 1 session (30 min)
- Phase 1: 1 session (3 hours)
- Phase 2: 1 session (8 hours)
- Phase 3: 2 sessions (10 hours each)

**Save checkpoints di Google Drive** agar tidak hilang saat session timeout!

---

## 📚 Resources

- **Notebook**: `rl_module/notebooks/Phase0_Colab_Training.ipynb`
- **Original code**: `rl_module/phase0_toy/`
- **Strategy doc**: `rl_module/PROGRESSIVE_STRATEGY.md`
- **Quick start**: `rl_module/START_HERE.md`

- **Colab docs**: https://colab.research.google.com/
- **Stable-Baselines3**: https://stable-baselines3.readthedocs.io/
- **Gymnasium**: https://gymnasium.farama.org/

---

**Ready to train?** 🚀

Upload `Phase0_Colab_Training.ipynb` ke Colab dan click `Run all`!
