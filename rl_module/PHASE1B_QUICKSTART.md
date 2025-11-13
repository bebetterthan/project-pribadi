# 🚀 PHASE 1B QUICK START

## Summary: 3-Tool Sequential Learning (Subfinder + HTTPX + Nmap)

**Goal**: Train agent to decide WHEN to use nmap (conditional tool usage)

**Key Lesson from Phase 1A**: ✅ Positive rewards > Penalties!

---

## 📊 Phase 1A Results (Context)

- **Trained Agent**: 365 ± 98
- **vs Random** (251): +45% improvement (1.45x)
- **vs Hardcoded** (242): +51% improvement (1.51x)
- **Status**: ✅ **PARTIAL SUCCESS** - Learned positive rewards work!

**What Worked**:

- Reward V2 (simplified, positive-dominant)
- High exploration (ent_coef 0.05)
- VecNormalize (observation + reward normalization)
- Fast updates (n_steps 512)

**Phase 1B Target**: Build on this foundation + add nmap intelligence!

---

## 🎯 Phase 1B Success Criteria

1. ✅ Beat Phase 1A by >30% → Target: >475 reward
2. ✅ Beat Hardcoded 3-Tool by >50% → Target: >450 reward
3. ✅ Variance <150 (stable learning)
4. ✅ Observable intelligent nmap usage (conditional, not always/never)

---

## 📅 Timeline: 7-8 Days (LOCAL CPU)

| Day | Task                  | Time      | Critical Focus                     |
| --- | --------------------- | --------- | ---------------------------------- |
| 1-2 | Scenario Design       | 6h        | **DIVERSITY** (Gemini's lesson!)   |
| 3   | Generate & Validate   | 6h        | 20 train + 5 test scenarios        |
| 4   | Implement Environment | 7h        | 40-dim state, 9 actions, Reward V2 |
| 5   | Baseline Agents       | 5h        | Random, Hardcoded, Phase1A wrapper |
| 6   | Training Prep         | 4h        | Scripts, TensorBoard, checkpoints  |
| 7   | **TRAINING**          | **6-10h** | **OVERNIGHT** run                  |
| 8   | Evaluation            | 2h        | Gate decision: PASS or ITERATE     |

**Total**: 7-8 days with LOCAL training (no cloud needed!) ✅

---

## 🔧 Technical Specs

### Environment: `FullReconEnv`

**State Space**: 40 dimensions (vs 22 in Phase 1A)

- **Group 1** (8): Target characteristics (complexity, coverage, time, phase)
- **Group 2** (12): Tool usage history (9 tool flags + metrics)
- **Group 3** (10): Discovery metrics (subdomains/ports/services)
- **Group 4** (10): **Nmap-specific** (scannable ports, service versions, priority)

**Action Space**: 9 actions (vs 6 in Phase 1A)

- **0-2**: Subfinder (passive, active, comprehensive)
- **3-5**: HTTPX (basic, detailed, full)
- **6-8**: **Nmap** (quick, full, service) ← NEW!

**Action Masking** (Sequential Workflow):

```
Initial → Only subfinder available
After subfinder → HTTPX available
After HTTPX → Nmap available
```

### Reward Function V2 (Learned from Phase 1A!)

**Philosophy**: POSITIVE-DOMINANT (encourage trying!)

**Component 1**: Discovery Rewards (ALL POSITIVE)

- +20 per new subdomain
- +40 per high-value subdomain (admin, api, db)
- +15 per new endpoint
- +30 per new port discovered
- +50 per critical service (SSH, database, admin)
- +25 per service version detected (nmap!)
- +10 per technology detected

**Component 2**: Completion Bonus (GOAL INCENTIVE)

- +300 if >80% coverage
- +200 if >70% coverage
- +150 if >60% coverage
- +100 if >50% coverage
- 0 otherwise (NO PENALTY!)

**Component 3**: Strategic Bonus (INTELLIGENT DECISIONS)

- +80 if used nmap on infrastructure (HIGH value decision)
- +40 if SKIPPED nmap on web-only (smart efficiency)
- +60 if correct sequential usage
- +50 if high efficiency
- 0 if suboptimal (NO PENALTY!)

**Component 4**: Efficiency Bonus (OPTIONAL REWARD)

- +100 if <90s
- +60 if <120s
- +30 if <180s
- 0 if >180s (NO TIME PENALTY!)

**CRITICAL**: Timeout = 0 reward (not negative!) → Encourages trying!

---

## 📂 File Structure

```
rl_module/
├── phase1_single_tool/           # Phase 1A (DONE)
│   ├── outputs/run_20251113_040938/  # Trained model
│   └── best_model/                    # Use for Phase1A wrapper
│
└── phase1b_three_tools/          # Phase 1B (TO CREATE)
    ├── data/scenarios/
    │   ├── phase1b_train.json    # 20 training scenarios
    │   └── phase1b_test.json     # 5 test scenarios
    │
    ├── envs/
    │   └── full_recon_env.py     # 40-dim, 9-action environment
    │
    ├── baselines/
    │   ├── random_agent_phase1b.py
    │   ├── hardcoded_agent_phase1b.py
    │   └── phase1a_wrapper.py    # Use Phase 1A model
    │
    ├── tests/
    │   └── test_full_recon_env.py  # 7 critical tests
    │
    ├── train_phase1b_local.py    # Training script
    ├── evaluate_phase1b.py       # Evaluation script
    │
    └── outputs/                  # Training results
        └── run_YYYYMMDD_HHMMSS/
```

---

## 🎓 Key Lessons Applied

### 1. Scenario Quality = Agent Intelligence (Gemini's Wisdom)

**Phase 1B Scenario Distribution**:

- **5 scenarios**: Web-only (nmap LOW value) → Agent learns to SKIP
- **8 scenarios**: Infrastructure (nmap HIGH value) → Agent learns to USE
- **7 scenarios**: Hybrid (CONDITIONAL) → Agent learns WHEN
- **5 scenarios**: Edge cases (unusual patterns)

**Port Diversity** (CRITICAL):

- 15+ unique port patterns across scenarios
- Common web: 80, 443, 8080, 8443, 3000
- Infrastructure: 22 (SSH), 3306 (MySQL), 5432 (PostgreSQL), 3389 (RDP)
- Mail: 25, 587 (SMTP), 993 (IMAP)
- Unusual: Custom ports 4000-10000 range

**Why Diversity Matters**: Agent must learn PATTERNS, not memorize!

### 2. Positive Rewards > Negative Penalties (Phase 1A Lesson)

**Phase 1A Failure**:

- Harsh time penalties (-0.05/sec)
- Redundancy penalties (-20)
- Agent learned: "Give up fast = less punishment"
- Result: Stuck in local minimum ❌

**Phase 1B Fix**:

- NO time penalties!
- NO harsh punishments!
- Timeout = 0 (not negative)
- Encourages exploration ✅

### 3. Local Training is Viable

**Phase 1A**: 100k steps in 3-4 minutes (CPU)
**Phase 1B**: 150k steps in 6-10 hours (CPU)

**Why Doable**:

- Fast environment (>500 steps/sec)
- Pre-computed tool results (no actual scanning)
- Overnight training window
- Zero cost! ✅

**When to Use Colab**: Phase 2+ (advanced tools, 300k+ timesteps)

---

## 🚦 Gate Decision Framework

### ✅ PASS → Proceed to Phase 2

**Criteria**:

- Beat Phase 1A by >30% (Target: >475 reward)
- Beat Hardcoded by >50% (Target: >450 reward)
- Variance <150
- Intelligent nmap usage observable

**Action**: Document results, celebrate, plan Phase 2! 🎉

### ⚠️ PARTIAL PASS → Quick Iteration

**Criteria**:

- Beat Phase 1A by 15-30% (close but not quite)
- Some intelligent behavior visible

**Options**:

1. Proceed anyway (diminishing returns)
2. Increase to 200k timesteps (+2-3 hours)
3. Minor reward tuning

**Timeline**: +1 day max

### ❌ FAIL → Needs Iteration

**Criteria**:

- Does NOT beat Phase 1A
- High variance (>200)
- No intelligent nmap usage
- Rewards flat/decreasing

**Root Causes to Check**:

1. Reward function problem → Adjust strategic bonuses (+2 days)
2. Exploration collapsed → Increase ent_coef to 0.08-0.1 (+1 day)
3. Overfitting → Generate more scenarios (+2 days)
4. State representation insufficient → Add features (+2 days)

---

## 💡 Quick Start Commands

### Day 1-2: Scenario Design

```bash
# Create scenario design document
# Document optimal strategies per scenario type
# No code yet - pure planning!
```

### Day 3: Generate Scenarios

```python
# Create data/generate_scenarios_phase1b.py
# Run: python data/generate_scenarios_phase1b.py
# Validate: python data/validate_scenarios.py
```

### Day 4: Environment Implementation

```python
# Create envs/full_recon_env.py
# Run tests: pytest tests/test_full_recon_env.py -v
# Expected: All 7 tests pass
```

### Day 5: Baseline Agents

```python
# Create all 3 baseline agents
# Test: python baselines/random_agent_phase1b.py
# Test: python baselines/hardcoded_agent_phase1b.py
```

### Day 6: Training Prep

```python
# Create train_phase1b_local.py
# Create evaluate_phase1b.py
# Verify imports work
```

### Day 7: TRAINING! 🚀

```bash
# Start training (overnight)
python train_phase1b_local.py

# Monitor in separate terminal (optional)
tensorboard --logdir=logs/phase1b --port=6006
# Open: http://localhost:6006
```

### Day 8: Evaluation

```bash
# After training completes
python evaluate_phase1b.py

# Check results
cat outputs/run_YYYYMMDD_HHMMSS/results.json
```

---

## 📈 Expected Results

### Baselines (Targets)

- **Random**: 200 ± 60 (discovery by luck)
- **Hardcoded 3-Tool**: 300 ± 80 (systematic but inflexible)
- **Phase 1A Wrapper**: 365 ± 98 (good at 2 tools, basic at nmap)

### Trained Phase 1B Agent (Target)

- **Mean Reward**: 475 ± 120
- **vs Phase 1A**: +30% improvement ✅
- **vs Hardcoded**: +58% improvement ✅
- **vs Random**: +138% improvement ✅

### Intelligent Behavior Indicators

- Uses nmap on infrastructure targets (high value)
- Skips nmap on web-only targets (efficiency)
- Sequential workflow: subfinder → httpx → conditional nmap
- Best episodes: 600-800 reward (comprehensive discovery)

---

## 🎯 Success Checklist

Before declaring Phase 1B complete:

- [ ] 20-25 diverse scenarios created
- [ ] Type distribution correct (5/8/7/5)
- [ ] Port patterns diverse (15+ unique)
- [ ] FullReconEnv implemented (40-dim, 9-action)
- [ ] All 7 tests passing
- [ ] Performance >500 steps/sec
- [ ] 3 baseline agents working
- [ ] Training completed (150k timesteps)
- [ ] No crashes during training
- [ ] Beat Phase 1A by >30%
- [ ] Beat Hardcoded by >50%
- [ ] Variance <150
- [ ] Intelligent nmap usage observable
- [ ] Results documented

**If ALL checked**: ✅ **PHASE 1B COMPLETE! Ready for Phase 2!**

---

## 🔥 Bottom Line

**Phase 1B** builds on Phase 1A success by adding **conditional tool intelligence**.

**Key Differentiator**: Agent learns WHEN to use nmap, not just HOW.

**Timeline**: 7-8 days with LOCAL CPU training (totally doable!)

**Success Metric**: Beat Phase 1A by >30% while showing intelligent nmap usage.

**Next Step**: Start Day 1 - Scenario Design! 🚀

---

**Ready to begin Phase 1B?** 💪
