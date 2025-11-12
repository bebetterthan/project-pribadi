# 🎯 START HERE - RL Module Quick Start Guide

## ⚡ What is This?

**Reinforcement Learning module** untuk optimize AI decision-making di AI Pentesting platform.

**Goal**: Belajar adaptive tool selection, model routing, dan parameter tuning menggunakan RL.

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Install Dependencies

```bash
cd rl_module
pip install -r requirements.txt
```

### Step 2: Test Toy Environment

```bash
cd phase0_toy
python toy_env.py
```

**Expected output**: Environment runs test episode successfully ✅

### Step 3: Train First Agent (Phase 0)

```bash
python train_toy.py
```

**Expected**: Training completes in ~30 minutes, agent beats random baseline by >60%

### Step 4: View Results

```bash
# Open TensorBoard
tensorboard --logdir ../logs/phase0

# Visit: http://localhost:6006
```

---

## 📋 Progressive Training Strategy

**DO NOT skip phases!** Each phase validates assumptions before proceeding.

| Phase       | Time      | Complexity       | Goal               |
| ----------- | --------- | ---------------- | ------------------ |
| **Phase 0** | Day 1-5   | Toy (2 actions)  | Prove RL works     |
| **Phase 1** | Day 6-10  | Simple (1 tool)  | Prove design       |
| **Phase 2** | Day 11-16 | Medium (2 tools) | Prove coordination |
| **Phase 3** | Day 17-24 | Full (3 tools)   | Prove production   |
| **Phase 4** | Day 25-30 | Polish           | Production ready   |

**Read detailed strategy**: [`PROGRESSIVE_STRATEGY.md`](PROGRESSIVE_STRATEGY.md)

---

## 📂 Directory Structure

```
rl_module/
├── README.md                    # Main documentation
├── START_HERE.md               # This file!
├── PROGRESSIVE_STRATEGY.md     # Detailed phase breakdown
├── requirements.txt            # Dependencies
├── .gitignore                  # Git ignore rules
│
├── phase0_toy/                 # ✅ PHASE 0: Proof of Concept
│   ├── toy_env.py              # Ultra-minimal environment
│   ├── train_toy.py            # Training script
│   └── README_PHASE0.md        # Phase 0 documentation
│
├── phase1_single_tool/         # TODO: PHASE 1 (after Phase 0 success)
│   └── (created after Phase 0 gates pass)
│
├── phase2_two_tools/           # TODO: PHASE 2 (after Phase 1 success)
│   └── (created after Phase 1 gates pass)
│
├── phase3_full_system/         # TODO: PHASE 3 (after Phase 2 success)
│   └── (created after Phase 2 gates pass)
│
├── data/                       # Training scenarios
│   ├── generate_scenarios.py  # Scenario generator (with Copilot prompts)
│   └── scenarios/              # Generated JSON files
│
├── envs/                       # Gymnasium environments
│   └── recon_env.py           # Full recon environment (for reference)
│
├── checkpoints/                # Saved models
│   ├── phase0/
│   ├── phase1/
│   └── ...
│
└── logs/                       # TensorBoard logs
    ├── phase0/
    ├── phase1/
    └── ...
```

---

## ✅ Current Status

### Phase 0: Proof of Concept

- [x] Toy environment created
- [x] Training script ready
- [ ] **TODO**: Run training and validate success criteria
- [ ] **TODO**: Pass Phase 0 gates (>60% improvement over random)

### Next Steps

1. Run `phase0_toy/train_toy.py`
2. Verify agent learns (TensorBoard)
3. Check success criteria met
4. If pass → Implement Phase 1
5. If fail → Debug and iterate

---

## 🎓 Learning Path

### Complete Beginner?

1. Start with `phase0_toy/toy_env.py` - Read code, understand structure
2. Run `python toy_env.py` - See environment in action
3. Read `phase0_toy/train_toy.py` - Understand training loop
4. Run training - Watch agent learn
5. Analyze results - Why did it learn (or not)?

### Have RL Experience?

1. Review `PROGRESSIVE_STRATEGY.md` - Understand progressive approach
2. Jump to current phase (likely Phase 0)
3. Implement and validate
4. Proceed to next phase

### Want to Integrate with Backend?

1. Complete Phase 3 first (full system working)
2. See `integration/` folder (will be created in Phase 3)
3. Use trained models in `backend/app/core/hybrid_orchestrator.py`

---

## 📊 Success Indicators

### You're On Track If:

- ✅ Each phase takes expected time (not stuck for weeks)
- ✅ Success gates achieved before proceeding
- ✅ Understanding deepens incrementally
- ✅ Confidence increases with each phase
- ✅ Can explain agent behavior

### You're Off Track If:

- ❌ Skipping phases ("let's jump to Phase 3")
- ❌ Proceeding without meeting gates
- ❌ Debugging takes longer than building
- ❌ Losing confidence or clarity
- ❌ Can't explain what agent learned

---

## 🐛 Troubleshooting

### Import errors (gymnasium, stable_baselines3)?

```bash
pip install -r requirements.txt
```

### Training not improving?

1. Check reward function (is it informative?)
2. Verify environment logic (test manually)
3. Try simpler state representation
4. Reduce learning rate
5. **Don't proceed to next phase** - fix current phase first!

### Agent behaving randomly?

1. Train longer (may need more timesteps)
2. Check if reward signal is too sparse
3. Verify observation normalization
4. Check action masking (if applicable)

### Out of memory?

1. Reduce batch size
2. Use CPU instead of GPU (for small models)
3. Reduce buffer size

---

## 💡 Key Principles

### 1. Progressive Validation

**Prove small things before building big things**

### 2. Clear Success Gates

**Can't proceed without meeting objectives**

### 3. Fast Feedback

**Start with 30-min training, scale gradually**

### 4. Incremental Complexity

**Add ONE challenge per phase**

### 5. Reusable Components

**Build once, reuse across phases**

---

## 📚 Resources

### Documentation

- [`README.md`](README.md) - Full documentation
- [`PROGRESSIVE_STRATEGY.md`](PROGRESSIVE_STRATEGY.md) - Detailed strategy
- Phase-specific READMEs in each `phaseN_*/` folder

### External Resources

- [Gymnasium Docs](https://gymnasium.farama.org/)
- [Stable-Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- [RL Book (Sutton & Barto)](http://incompleteideas.net/book/the-book-2nd.html)
- [OpenAI Spinning Up](https://spinningup.openai.com/)

### Tools

- **TensorBoard**: Monitor training progress
- **Jupyter Notebooks**: Analyze results (see `notebooks/`)
- **pytest**: Run tests

---

## 🎯 What To Do RIGHT NOW

### Option 1: Complete Beginner (Never Used RL)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test environment
cd phase0_toy
python toy_env.py

# 3. Read code and understand
# Open toy_env.py and read through it

# 4. Run training
python train_toy.py

# 5. Watch TensorBoard
tensorboard --logdir ../logs/phase0
```

### Option 2: Have RL Experience

```bash
# 1. Review strategy
cat PROGRESSIVE_STRATEGY.md

# 2. Jump to Phase 0 training
cd phase0_toy
python train_toy.py --timesteps 20000

# 3. Validate and proceed
# If success → Implement Phase 1
# If fail → Debug Phase 0
```

### Option 3: Want Production Integration

```bash
# Don't do this yet! Complete Phase 0-3 first.
# Integration happens in Phase 4.
```

---

## ❓ FAQ

### Q: Can I skip Phase 0 and go straight to Phase 3?

**A**: NO! Phase 0 validates your RL setup works. Skipping = high failure risk.

### Q: How long does complete training take?

**A**: Phase 0: 30min, Phase 1: 3h, Phase 2: 8h, Phase 3: 20h. Total: ~30 hours training time over 30 days.

### Q: What if Phase 0 doesn't work?

**A**: Debug before proceeding! Check: environment logic, reward function, dependencies installed correctly.

### Q: Can I use this with real backend?

**A**: Yes, but only after Phase 3 completes. Integration layer in Phase 4.

### Q: What hardware do I need?

**A**: Phase 0-1: CPU fine. Phase 2-3: GPU recommended but not required.

---

## 📞 Support

### Issues?

1. Check `PROGRESSIVE_STRATEGY.md` for detailed phase info
2. Review phase-specific README in current phase folder
3. Test environment manually (run `python toy_env.py`)
4. Check TensorBoard logs for training issues

### Still Stuck?

1. Verify all dependencies installed: `pip list | grep gymnasium`
2. Check Python version: `python --version` (need 3.8+)
3. Review error messages carefully
4. Debug ONE phase at a time (don't skip!)

---

## 🎉 Success Path

```
Day 1-5:   Implement & train Phase 0 ✅
           ↓ (Beats random by >60%)

Day 6-10:  Implement & train Phase 1 ✅
           ↓ (Single tool mastery)

Day 11-16: Implement & train Phase 2 ✅
           ↓ (Two-tool coordination)

Day 17-24: Implement & train Phase 3 ✅
           ↓ (Full system working)

Day 25-30: Polish & integrate Phase 4 ✅
           ↓

🎯 PRODUCTION READY!
```

---

**Current Milestone**: Complete Phase 0  
**Next Action**: Run `phase0_toy/train_toy.py`  
**Success Criteria**: Agent beats random baseline by >60%

**LET'S GO!** 🚀

---

**Last Updated**: November 13, 2025  
**Version**: 0.1.0  
**Status**: Phase 0 Implementation Complete, Ready to Train
