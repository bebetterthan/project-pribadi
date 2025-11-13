# Phase 1B Training Guide

## Overview

Phase 1B trains an RL agent for **intelligent 3-tool workflow** (Subfinder → HTTPX → Nmap).

**Key Learning Goal**: WHEN to use nmap (conditional tool intelligence)

## Quick Start

### 1. Train Agent (Overnight, ~6-10 hours)

```bash
cd phase1b_three_tools/training
python train_phase1b_local.py
```

**Monitor progress**:

```bash
tensorboard --logdir=../outputs/phase1b_run_TIMESTAMP/tensorboard
# Open: http://localhost:6006
```

### 2. Evaluate on Test Scenarios

```bash
python evaluate_phase1b.py \
    --model ../outputs/phase1b_run_TIMESTAMP/best_model/best_model.zip \
    --test-scenarios ../data/phase1b_test.json \
    --output ../outputs/phase1b_run_TIMESTAMP/test_results.json
```

## Training Configuration

### Hyperparameters (Proven from Phase 1A)

```python
{
    "learning_rate": 1e-3,      # Fast learning
    "ent_coef": 0.05,           # High exploration (CRITICAL!)
    "n_steps": 512,             # Update frequency
    "batch_size": 128,          # Larger batches
    "n_epochs": 20,             # Learn more per update
    "gamma": 0.99,              # Discount factor
    "gae_lambda": 0.95,         # GAE parameter
    "clip_range": 0.2           # PPO clip
}
```

### Environment

- **State Space**: 40 dimensions (8+12+10+10)

  - Group 1: Target characteristics (8)
  - Group 2: Tool usage history (12)
  - Group 3: Discovery metrics (10)
  - Group 4: Nmap-specific context (10)

- **Action Space**: 9 discrete (3 tools × 3 modes)

  - 0-2: Subfinder (passive, active, comprehensive)
  - 3-5: HTTPX (basic, thorough, comprehensive)
  - 6-8: Nmap (quick, full, service)

- **Episode Flow**: Sequential (subfinder → httpx → nmap)
- **Action Masking**: Enforces sequential workflow

### Training Data

- **Training scenarios**: 20 (phase1b_train.json)
  - 5 web-only targets (nmap low value)
  - 8 infrastructure targets (nmap high value)
  - 7 hybrid targets (conditional nmap)
- **Test scenarios**: 5 (phase1b_test.json)
  - Edge cases for final evaluation

## Baseline Performance

From Day 5 evaluation (20 training scenarios):

| Agent                 | Mean ± Std | Range    | Notes                       |
| --------------------- | ---------- | -------- | --------------------------- |
| **Random**            | 1138 ± 305 | 730-2055 | Random valid actions        |
| **Hardcoded**         | 1215 ± 187 | 890-1470 | Always comprehensive (BEST) |
| **Phase1A Heuristic** | 1101 ± 223 | 715-1510 | Smart heuristic             |

**Training Target**:

- Beat best baseline (+30%): **1580+**
- Ultimate goal (+50%): **1823+** with intelligent nmap usage

## Success Criteria (Gate Decision)

### Phase 1B Pass Requirements:

1. ✅ **Beat best baseline by >30%** (≥1580 reward)
2. ✅ **Beat hardcoded by >30%** (>1.3x ratio)
3. ✅ **Stable performance** (std <200)
4. ✅ **Intelligent nmap usage** (50-90% usage rate)
5. ✅ **Correct nmap decisions** (>70% accuracy)
   - Uses nmap on infrastructure targets
   - Skips nmap on web-only targets

If **ALL pass** → **PROCEED TO PHASE 2**

If **ANY fail** → **ITERATE** (more training, tune hyperparameters, or adjust scenarios)

## Monitoring Training

### TensorBoard Metrics

**Key metrics to watch**:

1. **phase1b/episode_reward**

   - Should trend upward
   - Target: >1580 by end of training

2. **phase1b/nmap_usage_rate**

   - Should stabilize at 50-80%
   - Too low: Agent not learning nmap value
   - Too high: Agent overusing nmap

3. **phase1b/nmap_on_infra_accuracy**

   - Should trend upward
   - Target: >80% (uses nmap on infrastructure)

4. **phase1b/nmap_skip_intelligence**

   - Should trend upward
   - Target: >70% (skips nmap on web-only)

5. **train/entropy_loss**
   - Should stabilize around -0.3 to -0.5
   - Too high: Too random (no learning)
   - Too low: Too deterministic (no exploration)

### Expected Training Behavior

**Early training (0-25k steps)**:

- High exploration (random-like behavior)
- Reward: ~800-1200
- Nmap usage: erratic (0-100%)

**Mid training (25k-100k steps)**:

- Learning nmap patterns
- Reward: increasing to ~1400-1600
- Nmap usage: stabilizing (50-80%)

**Late training (100k-150k steps)**:

- Fine-tuning decisions
- Reward: approaching target (1580+)
- Nmap usage: stable with intelligent patterns

## Output Files

After training, you'll find:

```
outputs/phase1b_run_TIMESTAMP/
├── tensorboard/              # TensorBoard logs
├── checkpoints/              # Model checkpoints (every 25k)
│   ├── ppo_phase1b_25000_steps.zip
│   ├── ppo_phase1b_50000_steps.zip
│   └── ...
├── best_model/               # Best model (from eval callback)
│   └── best_model.zip
├── eval_logs/                # Evaluation logs
├── final_model.zip           # Final model after 150k steps
├── vec_normalize_stats.pkl   # Normalization stats (CRITICAL!)
└── results.json              # Training summary
```

## Troubleshooting

### Issue: Reward not increasing

**Possible causes**:

- Insufficient exploration (entropy too low)
- Reward function issues
- Learning rate too low

**Solutions**:

1. Check `train/entropy_loss` in TensorBoard (should be -0.3 to -0.5)
2. If entropy too low, increase `ent_coef` (try 0.08 or 0.10)
3. Continue training (may need more timesteps)

### Issue: Nmap usage too low (<30%)

**Possible causes**:

- Strategic bonus not strong enough
- Agent learned to skip nmap (safer strategy)

**Solutions**:

1. Increase nmap strategic bonus weights in reward function
2. Check if agent discovered "skip nmap always" exploit
3. Adjust scenario distribution (more infrastructure targets)

### Issue: Nmap usage too high (>90%)

**Possible causes**:

- Agent learned "always use nmap" heuristic
- Not learning conditional intelligence

**Solutions**:

1. Increase skip bonus for web-only targets
2. Check scenario variety (need more web-only targets?)
3. Reduce nmap discovery rewards (make it less always-optimal)

### Issue: High variance (std >200)

**Possible causes**:

- Need more training
- Scenarios too diverse
- VecNormalize not working

**Solutions**:

1. Continue training (150k → 200k steps)
2. Check VecNormalize loaded correctly
3. Reduce scenario complexity range

## Next Steps After Training

### If Gate Check PASSES ✅:

1. **Document findings**:
   - Final reward: X ± Y
   - Nmap usage patterns: Z%
   - Baseline comparisons
2. **Analyze learned strategy**:

   - Which scenarios use nmap?
   - Which scenarios skip nmap?
   - Are decisions explainable?

3. **Prepare for Phase 2**:
   - 4-tool workflow (add Nuclei)
   - Multi-step episodes (5+ steps)
   - More complex decision trees

### If Gate Check FAILS ❌:

1. **Diagnose failure**:

   - Which criterion failed?
   - By how much?
   - Observable patterns in failures?

2. **Iteration options**:

   - **More training**: Continue from checkpoint (150k → 200k)
   - **Hyperparameter tuning**: Adjust `ent_coef`, `learning_rate`
   - **Reward tuning**: Adjust strategic bonus weights
   - **Scenario adjustment**: Add more diverse targets

3. **Re-evaluate**:
   - Run evaluation again after changes
   - Check if improvements observed

## Performance Optimization

### Training Speed

- **Current**: ~4997 steps/sec (measured)
- **150k timesteps**: ~30 seconds compute time
- **Actual time**: 6-10 hours (includes episode rollouts, evaluations, checkpoints)

### Memory Usage

- **VecNormalize**: ~10MB (running stats)
- **Model**: ~5MB (MLP policy)
- **Replay buffer**: ~50MB (PPO on-policy)

**Total**: ~65MB (very light!)

## Tips

1. **Always use VecNormalize**: Critical for stable training
2. **Monitor entropy**: Should stay in -0.3 to -0.5 range
3. **Save checkpoints**: Can resume if training interrupted
4. **Test early**: Evaluate at 50k steps to catch issues early
5. **Check nmap patterns**: Use TensorBoard custom metrics

## References

- Phase 1A success: 365±98 reward (beat baselines)
- Reward V2 philosophy: Positive-dominant (no negative penalties)
- Action masking: Sequential workflow enforcement
- Strategic bonus: Key to conditional learning

---

**Ready to train?**

```bash
python train_phase1b_local.py
```

**Monitor in real-time**:

```bash
tensorboard --logdir=../outputs/phase1b_run_TIMESTAMP/tensorboard
```

Good luck! 🚀
