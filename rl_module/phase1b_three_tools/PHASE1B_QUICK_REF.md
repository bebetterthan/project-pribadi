# Phase 1B Quick Reference

## 🎯 Goal

Train RL agent to learn **WHEN** to use nmap (conditional tool intelligence)

## 📊 Performance Summary

### Baselines (Training Scenarios)

| Agent             | Mean ± Std     | Range    |
| ----------------- | -------------- | -------- |
| Random            | 1138 ± 305     | 730-2055 |
| Hardcoded         | **1215 ± 187** | 890-1470 |
| Phase1A Heuristic | 1101 ± 223     | 715-1510 |

**Training Target**: 1580+ (best baseline +30%)

## 🚀 Quick Commands

### Train (Overnight)

```bash
cd phase1b_three_tools/training
python train_phase1b_local.py
```

### Monitor

```bash
tensorboard --logdir=../outputs/phase1b_run_TIMESTAMP/tensorboard
# http://localhost:6006
```

### Evaluate

```bash
python evaluate_phase1b.py \
    --model ../outputs/phase1b_run_TIMESTAMP/best_model/best_model.zip \
    --test-scenarios ../data/phase1b_test.json
```

## 📈 Key Metrics to Watch

| Metric                           | Target       | Meaning           |
| -------------------------------- | ------------ | ----------------- |
| `phase1b/episode_reward`         | >1580        | Should trend up   |
| `phase1b/nmap_usage_rate`        | 50-80%       | Conditional usage |
| `phase1b/nmap_on_infra_accuracy` | >80%         | Use on infra      |
| `phase1b/nmap_skip_intelligence` | >70%         | Skip on web       |
| `train/entropy_loss`             | -0.3 to -0.5 | Exploration level |

## ✅ Success Criteria (Gate)

1. Beat best baseline (+30%): ≥1580
2. Beat hardcoded (+30%): >1.3x
3. Stable performance: std <200
4. Nmap usage: 50-90%
5. Nmap correctness: >70%

**All pass** → Phase 2 | **Any fail** → Iterate

## 🏗️ Environment Specs

- **State**: 40-dim (8+12+10+10)
- **Actions**: 9 discrete (3 tools × 3 modes)
- **Workflow**: Sequential (subfinder → httpx → nmap)
- **Reward**: V2 positive-dominant (4 components)
- **Scenarios**: 20 train, 5 test

## 🔧 Hyperparameters

```python
learning_rate = 1e-3      # Fast learning
ent_coef = 0.05           # High exploration
n_steps = 512             # Update frequency
batch_size = 128          # Larger batches
n_epochs = 20             # Learn more per update
timesteps = 150000        # ~6-10 hours
```

## 📁 Output Structure

```
outputs/phase1b_run_TIMESTAMP/
├── tensorboard/              # Logs
├── checkpoints/              # Every 25k
│   └── ppo_phase1b_*.zip
├── best_model/               # Best eval
│   └── best_model.zip
├── vec_normalize_stats.pkl   # CRITICAL!
├── final_model.zip           # After 150k
└── results.json              # Summary
```

## 🐛 Common Issues

### Reward not increasing

- Check entropy (-0.3 to -0.5)
- Try `ent_coef=0.08`
- Continue training

### Nmap usage too low (<30%)

- Increase strategic bonus
- More infrastructure scenarios

### Nmap usage too high (>90%)

- Increase web skip bonus
- More web-only scenarios

### High variance (>200)

- Continue training (150k→200k)
- Check VecNormalize loaded

## 🎬 Training Timeline

| Phase | Steps    | Behavior          | Reward    |
| ----- | -------- | ----------------- | --------- |
| Early | 0-25k    | High exploration  | 800-1200  |
| Mid   | 25-100k  | Learning patterns | 1400-1600 |
| Late  | 100-150k | Fine-tuning       | 1580+     |

## 📚 Day-by-Day Progress

- ✅ Day 1-2: Scenario Design (25 scenarios)
- ✅ Day 3: Generate JSON (20 train, 5 test)
- ✅ Day 4: Environment (40-dim, 9 actions, 4997 steps/sec)
- ✅ Day 5: Baselines (1215 best)
- ✅ Day 6: Training Scripts (train + eval)
- ⏳ Day 7: Execute Training (overnight)
- ⏳ Day 8: Gate Decision (test eval)

## 🎯 Next Steps

**After Day 6** → Start training:

```bash
python train_phase1b_local.py
```

**After Day 7** → Evaluate:

```bash
python evaluate_phase1b.py --model ...
```

**After Day 8** → Gate decision:

- **PASS** → Phase 2 planning
- **FAIL** → Iteration strategy

---

**Current Status**: Day 6 Complete ✅  
**Ready for**: Day 7 Training 🏃

**Estimated Time**: 6-10 hours overnight
