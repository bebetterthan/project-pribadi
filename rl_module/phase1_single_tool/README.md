# 🎯 PHASE 1: Subfinder + HTTPX Sequential Strategy

## Objective

Master 2-TOOL SEQUENTIAL workflow:

1. **Subfinder** (subdomain discovery) → Choose optimal mode
2. **HTTPX** (live probing) → Choose optimal probe strategy

Learn which tool combinations work best for different target scenarios.

## Success Criteria

- ✅ Agent beats random baseline by >100% (Target: >931 reward)
- ✅ Agent beats hardcoded "always comprehensive" by >30% (Target: >857 reward)
- ✅ Observable strategic decision-making (contextual tool selection)
- ✅ Validates sandbox design + reward function

## Baselines (2-Tool Workflow)

- **Random**: 465.84 ± 214.11 (random subfinder + random httpx)
- **Hardcoded**: 659.21 ± 414.82 (always comprehensive for both)
- **Performance**: 25,043 steps/sec (25x target!)

## Timeline

**3 Days** | Local Training + TensorBoard Monitoring

## Structure

```
phase1_single_tool/
├── README.md                          # This file
├── TRAINING_GUIDE.md                  # 📊 Local training & monitoring guide
├── train_local.py                     # 🚀 Main training script
├── start_tensorboard.py               # 📊 TensorBoard launcher
├── outputs/                           # Training outputs
│   └── run_YYYYMMDD_HHMMSS/
│       ├── tensorboard/               # TensorBoard logs
│       ├── checkpoints/               # Model checkpoints
│       ├── best_model/                # Best model
│       ├── final_model.zip            # Final trained model
│       └── results.json               # Results summary
├── data/
│   └── scenarios/
│       ├── phase1_training.json       # 10 diverse training scenarios
│       └── phase1_eval.json           # 5 held-out test scenarios
├── baselines/
│   ├── random_agent.py                # Random action baseline
│   └── hardcoded_agent.py             # Always comprehensive baseline
├── envs/
│   └── subfinder_env.py               # Gymnasium environment
└── tests/
    └── test_subfinder_env.py          # Comprehensive test suite

```

## Current Status

### Day 1: Scenario Generation ✅ COMPLETE

- ✅ Generate 10 diverse training scenarios
- ✅ Generate 5 held-out eval scenarios
- ✅ Validate scenario diversity (PASS: 3/4/3 distribution)
- ✅ Document diversity strategy

### Day 2: Environment Implementation ✅ COMPLETE

- ✅ Implement SubfinderEnv (15-dim state, 3 actions)
- ✅ Implement reward function (4 components with anti-hacking)
- ✅ Implement action masking
- ✅ Test environment locally (**36,335 steps/sec** - 36x target!)
- ✅ Implement baselines (random: 859±156, hardcoded: 681±164)
- ✅ Comprehensive test suite (**17/17 tests passing**)

### Day 3: Local Training 🔄 READY TO START

- ⏳ Run training with PPO (100k timesteps, ~5-10 min)
- ⏳ Monitor with TensorBoard (localhost:6006)
- ⏳ Evaluate vs baselines
- ⏳ Check success criteria (>2x random, >1.3x hardcoded)
- ⏳ Document results

---

## 🚀 Quick Start

### 1. Run Training

```bash
cd phase1_single_tool
python train_local.py
```

### 2. Monitor (Separate Terminal)

```bash
cd phase1_single_tool
python start_tensorboard.py
# Or manually: tensorboard --logdir=outputs --port=6006
```

### 3. Open Browser

```
http://localhost:6006
```

### 4. Check Results

Training akan otomatis evaluate dan compare dengan baselines.
Results tersimpan di `outputs/run_YYYYMMDD_HHMMSS/results.json`

📖 **Full Guide**: See `TRAINING_GUIDE.md` for detailed monitoring instructions.

---

## Design Philosophy (Gemini Insights)

### 80/20 Rule

- **80% Design** (scenarios + reward + state) ✅ DONE
- **20% Execution** (just run and monitor) ⏳ NOW

### Critical Focus

1. **Scenario Diversity (40%)**: Pattern learning > Memorization ✅
2. **Reward Design (40%)**: Anti-reward-hacking measures ✅
3. **State Representation (15%)**: Rich, informative features ✅
4. **Training (5%)**: Run with good hyperparams ⏳

### Anti-Reward-Hacking Measures ✅

- Time penalty: Prevent spam
- Redundancy penalty: Prevent repeat scans
- Wrong tool penalty: Prevent always-comprehensive
- Strategic bonuses: Reward contextual decisions
- Completion multiplier: Encourage efficiency

---

## Next Steps

**RIGHT NOW**: Generate diverse scenarios with `generate_scenarios_phase1.py`

**Key**: Ensure REAL diversity (types, naming patterns, tech stacks, complexity)!
