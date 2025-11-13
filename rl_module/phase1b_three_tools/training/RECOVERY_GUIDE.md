# Kalau Laptop Mati - Recovery Guide

## TL;DR - Yang Penting!

1. **COLOKKAN CHARGER SEKARANG!** (Battery: 37%, cuma 57 menit)
2. Training sudah save checkpoint tiap 25k steps
3. Kalau mati, bisa resume otomatis dari checkpoint terakhir
4. Run `keep_awake.ps1` di terminal baru untuk prevent sleep

---

## Current Status

- ✅ Training RUNNING (PID 10412)
- ⚠️ Battery: 37% (BAHAYA!)
- ⏱️ Progress: 20k / 150k steps (~14%)
- 🎯 Target: 1,671 reward
- 📊 Current: 1,230 reward

---

## 🔴 Emergency Actions

### 1. Prevent Laptop Sleep (PENTING!)

```powershell
# Terminal baru, jangan tutup!
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
.\keep_awake.ps1
```

**Ini akan**:

- Disable sleep/hibernate saat plugged in
- Keep laptop awake selama training
- Monitor battery dan training process
- Auto-stop kalau training selesai

### 2. Colokkan Charger!

Battery cuma 37%, training butuh 6-10 jam!

---

## 📦 Checkpoint System (Auto-Save)

Training otomatis save checkpoint tiap **25k steps**:

- ✅ 25k steps → `rl_model_25000_steps.zip`
- ✅ 50k steps → `rl_model_50000_steps.zip`
- ✅ 75k steps → `rl_model_75000_steps.zip`
- ✅ 100k steps → `rl_model_100000_steps.zip`
- ✅ 125k steps → `rl_model_125000_steps.zip`
- ✅ 150k steps → `final_model.zip` (DONE!)

**Location**: `outputs/phase1b_run_YYYYMMDD_HHMMSS/checkpoints/`

---

## 🔄 Resume Training (Kalau Mati)

### Option 1: Auto-Resume Script (RECOMMENDED)

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
.\auto_resume.ps1
```

Script akan:

1. Check kalau training masih running
2. Kalau tidak, cari checkpoint terakhir
3. Resume otomatis dari checkpoint
4. Continue sampai 150k steps

### Option 2: Manual Resume

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
python resume_training.py
```

### Option 3: Monitor Mode (Auto-detect & Resume)

```powershell
# Akan check tiap 5 menit, auto-resume kalau training stop
.\auto_resume.ps1 -Monitor -CheckIntervalSeconds 300
```

---

## 📊 Monitor Training

### Check Progress

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
.\monitor_live_training.ps1
```

Output:

- Process status (PID, memory, CPU)
- Latest metrics (reward, steps)
- Checkpoint count
- Errors (if any)

### Watch Real-Time Logs

```powershell
Get-Content training_stdout.log -Wait -Tail 20
```

### TensorBoard (Visual)

```powershell
# Terminal baru
tensorboard --logdir="D:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\outputs\phase1b_run_20251113_094132\tensorboard"

# Open browser: http://localhost:6006
```

---

## 🛡️ Protection Strategy

### Before Sleep/Shutdown Checklist:

1. ✅ Check training progress: `.\monitor_live_training.ps1`
2. ✅ Verify checkpoints exist: Check `outputs/.../checkpoints/`
3. ✅ Note latest checkpoint number (e.g., 75000 steps)
4. ✅ Battery > 50% OR plugged in
5. ✅ Keep-awake script running: `.\keep_awake.ps1`

### After Restart:

1. Open terminal di training directory
2. Run: `.\auto_resume.ps1`
3. Confirm resume (it will show progress)
4. Start keep-awake: `.\keep_awake.ps1` (terminal baru)
5. Monitor: `.\monitor_live_training.ps1`

---

## 🔍 Verify Training Status

### Is Training Running?

```powershell
Get-Process python | Where-Object { $_.CommandLine -like "*train_phase1b*" }
```

If result: **Training RUNNING** ✅  
If empty: **Training STOPPED** → Use resume script

### Latest Checkpoint?

```powershell
$latest = Get-ChildItem "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\outputs\phase1b_run_*\checkpoints\rl_model_*_steps.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Latest: $($latest.Name)"
```

### How Much Progress Lost?

If laptop mati at 87k steps, last checkpoint is 75k:

- **Lost**: 12k steps (~1 hour)
- **Remaining**: 75k steps (~5 hours)
- **Recovery**: Resume from 75k checkpoint

---

## 💡 Pro Tips

### 1. Multiple Terminals

- **Terminal 1**: Training (`python train_phase1b_local.py`)
- **Terminal 2**: Keep-awake (`.\keep_awake.ps1`)
- **Terminal 3**: Monitor (`.\monitor_live_training.ps1`)
- **Terminal 4**: TensorBoard (`tensorboard --logdir=...`)

### 2. Battery Critical (<20%)

```powershell
# Quick save current progress
Stop-Process -Name python  # Training stops, last checkpoint preserved
# Plug charger
.\auto_resume.ps1  # Resume
```

### 3. Scheduled Task (Advanced)

Create Windows scheduled task to auto-resume on startup:

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training\auto_resume.ps1`" -Monitor"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "Phase1B_AutoResume" -Action $action -Trigger $trigger -RunLevel Highest
```

---

## 🎯 Success Criteria

Training selesai kalau:

- ✅ 150,000 steps completed
- ✅ `final_model.zip` exists
- ✅ Reward > 1,671 (30% above baseline)
- ✅ Process exits with code 0

Check final result:

```powershell
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
python evaluate_phase1b.py --model "../outputs/phase1b_run_LATEST/final_model.zip"
```

---

## 🆘 Emergency Contacts (Commands)

### Kill Training (If Needed)

```powershell
Stop-Process -Id 10412  # Use actual PID from monitor
```

### Clean Restart

```powershell
# Kill all python processes
Get-Process python | Stop-Process -Force

# Start fresh
cd "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
python train_phase1b_local.py
```

### Check Disk Space

```powershell
Get-PSDrive D | Select-Object Used,Free
```

Training uses ~500MB total (checkpoints + logs).

---

## Summary

**Right Now**:

1. ⚠️ **COLOKKAN CHARGER!** (Battery 37%)
2. Run `.\keep_awake.ps1` di terminal baru
3. Training akan jalan 6-10 jam
4. Checkpoint save tiap 25k steps
5. Kalau mati, jalankan `.\auto_resume.ps1`

**Worst Case**: Laptop mati di 140k steps

- Lost: 15k steps (~1 hour work)
- Resume: From 125k checkpoint
- Time: 1.5 hours to completion

**Best Case**: Training complete overnight

- Wake up → 150k steps done
- Reward > 1,671 ✅
- Phase 1B: PASS → Phase 2!

---

_Last Updated: 2025-11-13 09:43_
