# Expert Consultation: RL Training Optimization for Conditional Tool Selection

## 📋 Context

I'm training a Reinforcement Learning agent for intelligent security reconnaissance tool selection. The agent must learn **WHEN to use nmap** (on infrastructure targets) vs **WHEN to skip** (on web-only targets) - a conditional learning problem.

**Repository**: https://github.com/bebetterthan/project-pribadi
**Details**: See `rl_module/phase1b_three_tools/TRAINING_ISSUES_SUMMARY.md`

---

## 🎯 Project Goal

Train PPO agent to:
1. **Conditional decision-making**: Use nmap 50-90% of time (not always, not never)
2. **High reward**: Beat baseline by >30% (target >4726 reward)
3. **Stable performance**: Variance <200
4. **Intelligent selection**: Use nmap on infrastructure, skip on web-only

---

## 📊 Current Achievement

After 16 training iterations:
- ✅ **Conditional learning WORKING**: 60-65% nmap usage achieved
- ✅ **V13 best eval**: 4321 reward, 65% nmap (19% above baseline)
- ✅ **V16 best rollout**: 3910 ep_rew_mean, 60% nmap
- ❌ **Cannot reach 30% target**: Stuck at 19% improvement
- ❌ **High variance**: 1500-2000 (target <200)
- ❌ **Non-monotonic optimization**: More reward → worse performance!

---

## ❓ CRITICAL QUESTIONS FOR EXPERT

### 1. 🔴 Non-Monotonic Optimization Problem

**Issue**: Increasing reward values makes performance WORSE, not better!

```
V13: 4321 reward, 65% nmap (baseline: discovery × 2.16x)
V14: 3976 reward, 70% nmap (+10% boost) → DOWN 8%! ❌
V15: 3590 reward, 63% nmap (+5% boost) → DOWN 17%! ❌
V16: 4025 reward, 60% nmap (strategic boost) → DOWN 7%! ❌
```

**Questions**:
- **Why does increasing reward coefficients hurt performance?**
- Is this reward scale sensitivity common in PPO?
- Should I use reward normalization/clipping?
- Is V13 a local optimum I can't escape from?
- How do I systematically find optimal reward scaling?

**What I've Tried**:
- Uniform scaling (+10%, +20%) → Failed
- Strategic amplification (only high-value components) → Failed
- Rebalancing ratios → Helped initially, then plateaued
- Going back to V13 base + tweaks → Still worse

**Suspected Causes**:
- Policy overfitting to specific reward landscape
- Exploration/exploitation balance disrupted
- Value function approximation error amplified
- Non-convex optimization landscape

---

### 2. 🟡 Evaluation vs Rollout Performance Mismatch

**Issue**: Training metrics don't predict evaluation performance!

```
V13: rollout 3630, eval 4321 (ratio: 1.19x) ← eval BETTER
V16: rollout 3910, eval 4025 (ratio: 1.03x) ← rollout BETTER

V16 has BEST training metrics but WORSE final eval!
```

**Questions**:
- **Which metric should I trust: rollout or eval?**
- Is this overfitting to training distribution?
- How do I select best model when metrics disagree?
- Should I use larger/different evaluation set?
- Is this ratio discrepancy a red flag?

**What I Observe**:
- V16: Highest ep_rew_mean during training (3910)
- V16: Lower final evaluation reward (4025 vs V13's 4321)
- Both trained on same scenarios, same PPO config
- V16 has better explained_variance (0.991 vs V13's lower)

**Possible Explanations**:
- Stochastic variance in evaluation
- Policy converged to different local optimum
- Scenario distribution mismatch
- Need actual test set to decide

---

### 3. 🟠 High Variance Problem

**Issue**: Cannot reduce variance below 1500 (target <200)

```
All versions: variance 1500-2000
V13: 1700 (range: 2247 - 7250)
V16: 1955 (range: 1944 - 7288)

Scenario types:
- Web-only: 1500-2500 reward
- Infrastructure: 4000-7000 reward
→ 2x difference causes high variance!
```

**Questions**:
- **Is variance <200 realistic for conditional learning?**
- Should I normalize rewards per scenario type?
- Would separate policies (web vs infra) help?
- Is high variance inherent to multi-objective RL?
- How do production RL systems handle this?

**What I've Tried**:
- Increasing training length (150k → 300k) → No effect
- Reward engineering (multiple iterations) → No effect
- Different entropy coefficients → Marginal effect

**Alternative Approaches**:
- Train two separate policies (web-only, infrastructure)?
- Use hierarchical RL (meta-policy selects sub-policy)?
- Normalize rewards within scenario categories?
- Accept high variance as inherent to problem?

---

### 4. 🔵 Moving Baseline Problem

**Issue**: Baseline performance changes between evaluations!

```
Same hardcoded agent evaluated:
V13: 3585 reward
V14: 3289 reward
V16: 4445 reward (+24%!)

How can deterministic agent get different scores?!
```

**Questions**:
- **Why does baseline performance vary so much?**
- Is my environment stochastic when it shouldn't be?
- Should I fix baseline with 100+ evaluations?
- How do I establish reliable comparison metrics?
- Is success criterion (>30% vs baseline) even valid?

**Suspected Issues**:
- Environment has hidden stochasticity
- Scenario sampling variance
- Small evaluation set (20 scenarios)
- Need fixed seed for baselines?

---

### 5. 🟣 Model Architecture Questions

**Current Setup**:
```python
Algorithm: PPO
Learning Rate: 1e-3
Entropy Coefficient: 0.05
Batch Size: 128
Timesteps: 300,000
Network: Default MLP (64, 64)
```

**Questions**:
- **Is 1e-3 learning rate too aggressive for RL?**
- Should I try lower lr (3e-4, 1e-4)?
- Would SAC/TD3 be more stable than PPO?
- Is 300k steps sufficient for convergence?
- Should I use learning rate schedule/decay?

**Alternative Algorithms**:
- SAC: Better for continuous? (but I have discrete actions)
- TD3: More stable than PPO?
- A2C/A3C: Simpler, more stable?
- DQN: Better for discrete actions?

**Architecture Experiments**:
- Larger network: (64,64) → (128,128)?
- Add LSTM for memory?
- Separate policy/value networks?
- Use attention mechanism?

---

### 6. 🟢 Reward Structure Design

**Current Reward Components**:
```python
Total = Discovery + Completion + Strategic + Efficiency

Discovery: Based on found items (subdomains, endpoints, ports)
Completion: Based on coverage percentage
Strategic: Scenario-specific bonuses (infra vs web)
Efficiency: Time-based bonus

Problem: Components can conflict!
- High discovery + skip nmap = good for web
- High strategic + use nmap = good for infra
- Agent receives mixed signals
```

**Questions**:
- **Should I remove conflicting incentives?**
- Use single reward objective per scenario type?
- How to structure reward for multi-objective RL?
- Is hierarchical reward (primary + secondary) better?
- Should rewards be normalized/scaled differently?

**Alternatives Considered**:
- Reward shaping with potential functions
- Intrinsic motivation bonuses
- Curiosity-driven exploration
- Multi-task learning approach

---

### 7. 🔴 Conditional Policy Learning

**Challenge**: Agent must learn DIFFERENT policies for different scenarios

```python
Web-only scenarios (9/20):
- Optimal: Skip nmap (get 1000 bonus)
- Using nmap: Lower reward

Infrastructure scenarios (11/20):
- Optimal: Use nmap (get 2600 bonus)
- Skipping: Large penalty (-400)

Agent must classify scenario type and act accordingly!
```

**Questions**:
- **Should I use explicit scenario classifier?**
- Would mixture-of-experts help (separate heads)?
- Is option-critic framework better for this?
- How to encourage policy specialization?
- Should I use curriculum learning?

**Architectural Ideas**:
- Two policy heads: web_policy, infra_policy
- Meta-policy selects which head to use
- Shared encoder, separate decision layers
- Explicit scenario type as input feature

---

### 8. 🟡 Environment Design Issues

**State Space** (40 dimensions):
```
- 8: scenario metadata (port counts, categories)
- 12: subfinder state
- 10: httpx state  
- 10: nmap state
```

**Identified Problems**:
1. **Ambiguous scenario classification**: What if 1 web + 1 infra port?
2. **Equal importance assumption**: 1 service = 10 subdomains?
3. **Sequential masking complexity**: 3 different policies per phase
4. **Hidden information**: Agent doesn't know scenario type explicitly

**Questions**:
- **Should I simplify state space?** (40D → 25D?)
- Add explicit scenario_type feature (0=web, 1=infra, 0.5=hybrid)?
- Remove sequential masking (allow any action anytime)?
- Would continuous action space work better?
- Should I redesign state representation?

---

### 9. 🟠 Training Strategy

**Current Approach**: Train on all 20 scenarios simultaneously

**Questions**:
- **Should I use curriculum learning?**
  - Start: Clear cases (pure web, pure infra)
  - Middle: Add hybrid scenarios
  - End: Add edge cases
- Would this improve convergence?
- How to design curriculum progression?
- Use automatic difficulty adjustment?

**Progressive Training Ideas**:
1. Phase 1: Train on 5 clear web-only scenarios
2. Phase 2: Add 5 clear infrastructure scenarios
3. Phase 3: Add 7 hybrid scenarios
4. Phase 4: Add 3 edge cases
5. Fine-tune on all 20 together

---

### 10. 🔵 Hyperparameter Tuning Strategy

**Current Method**: Manual tuning through 16 iterations

**Questions**:
- **Should I use systematic hyperparameter search?**
- Bayesian optimization (Optuna)?
- Population-based training (PBT)?
- Grid search feasible? (expensive!)
- Which hyperparameters matter most?

**Key Hyperparameters to Tune**:
```python
learning_rate: [1e-4, 3e-4, 1e-3]
entropy_coef: [0.01, 0.05, 0.1]
batch_size: [64, 128, 256]
n_steps: [1024, 2048, 4096]
reward_scale: [0.5, 1.0, 2.0, 5.0]
```

**Constraints**:
- Each run takes ~9 minutes
- Limited compute budget
- Need efficient search strategy

---

## 🎯 SPECIFIC GUIDANCE NEEDED

### Immediate Decisions:

1. **Model Selection**: Should I use V13 (4321 eval) or V16 (3910 rollout)?
2. **Success Criteria**: Is 19% improvement + conditional learning sufficient?
3. **Variance Target**: Should I accept >1500 variance as inherent?

### Strategic Direction:

4. **Algorithm Change**: Stay with PPO or try SAC/TD3/A2C?
5. **Architecture**: Keep simple MLP or add complexity (LSTM, attention)?
6. **Reward Design**: Keep multi-component or simplify?

### Implementation:

7. **Next Experiment**: What single change would most likely improve performance?
8. **Debugging Strategy**: How to diagnose why more reward hurts?
9. **Convergence Check**: How to know if I've truly converged?

---

## 💡 MY HYPOTHESES

### Why V13 is Best:

1. **Reward scale sweet spot**: 2.16x amplification is optimal
2. **Ratio balance**: 26:1 infrastructure:web-only perfect
3. **Exploration/exploitation**: 65% nmap hits sweet spot
4. **Lucky convergence**: Random seed played role?

### Why Further Optimization Fails:

1. **Non-convex landscape**: V13 is local optimum, hard to escape
2. **Sensitivity**: Small reward changes → big policy changes
3. **Overfitting**: Policy specialized to V13 reward structure
4. **Insufficient exploration**: Entropy too low to find better solution

### Why Variance is High:

1. **Problem structure**: Conditional learning inherently variable
2. **Scenario diversity**: 2x reward difference between types
3. **Small sample**: 20 scenarios not enough
4. **Policy uncertainty**: Agent not fully confident in decisions

---

## 🔬 EXPERIMENTS ALREADY TRIED

### Reward Engineering (12 iterations):
- ✅ Amplification (1.8x, 2.0x, 2.16x, 2.38x)
- ✅ Ratio rebalancing (infrastructure:web = 26:1)
- ✅ Strategic bonuses (3-tool workflow: 2000-2600)
- ✅ Completion bonuses (coverage-based)
- ✅ Efficiency bonuses (time-based)
- ❌ All hit ceiling at ~4300 reward

### Training Configuration:
- ✅ Extended training (150k → 300k steps)
- ✅ Entropy tuning (0.01, 0.05, 0.1)
- ✅ Learning rate: 1e-3 (only value tested)
- ❌ Different algorithms (only PPO)

### Action Space:
- ✅ Added skip_nmap action (critical breakthrough!)
- ✅ Sequential masking (subfinder → httpx → nmap/skip)
- ❌ Continuous actions (not tried)

### Architecture:
- ✅ Default MLP (64, 64)
- ❌ Larger networks (not tried)
- ❌ LSTM/attention (not tried)
- ❌ Multi-head policies (not tried)

---

## 🚀 PROPOSED NEXT STEPS

Based on expert input, I'm considering:

### Option A: Accept Current Best (V13)
- 4321 reward, 65% nmap usage
- 19% above baseline (close to 30% target)
- Conditional learning working well
- Move to test set evaluation

### Option B: Try Alternative Algorithm
- Implement SAC or TD3
- More stable than PPO?
- Better for high-variance environments?
- Worth 10+ hours compute?

### Option C: Architectural Change
- Multi-head policy (web vs infra)
- Explicit scenario classifier
- Curriculum learning
- Higher risk, higher reward

### Option D: Hyperparameter Search
- Optuna for systematic search
- Focus on lr, entropy, reward_scale
- 50-100 training runs
- Most data-driven approach

---

## 🤔 META QUESTIONS

1. **Is this level of difficulty normal for RL?**
   - 16 iterations to get conditional learning working
   - Non-monotonic optimization common?
   - How long do production RL projects typically take?

2. **Am I doing RL correctly?**
   - Is my debugging process sound?
   - Are my reward engineering strategies standard?
   - Should I be using different tools/frameworks?

3. **When to stop optimizing?**
   - Is 19% improvement "good enough"?
   - Is perfect score unrealistic for complex RL?
   - How do I know if further optimization is worthwhile?

4. **Production considerations**:
   - How to ensure robustness for deployment?
   - How to monitor RL agent in production?
   - How to handle distribution shift?

---

## 📚 ADDITIONAL CONTEXT

**Full Details**: See `rl_module/phase1b_three_tools/TRAINING_ISSUES_SUMMARY.md` in repository

**Key Files**:
- Environment: `envs/full_recon_env.py` (1009 lines)
- Training: `training/train_phase1b_local.py`
- Evaluation: `training/evaluate_phase1b.py`
- Scenarios: `data/phase1b_train.json` (20 scenarios)

**Training Logs**: Available for all 16 versions

**Models**: V13 and V16 checkpoints saved

---

## 🎯 TL;DR - WHAT I NEED MOST

1. **Why is my RL optimization non-monotonic?** (More reward → worse results)
2. **V13 vs V16: Which model to deploy?** (Best eval vs best rollout)
3. **Is variance <200 achievable?** (Currently 1500-2000)
4. **Should I try different algorithm?** (SAC/TD3 vs PPO)
5. **What's ONE change most likely to help?** (Next experiment priority)

---

**Thank you for your expertise!** Any insights into these RL optimization challenges would be incredibly valuable. I've been stuck in this local optimum for multiple iterations and need expert guidance on the path forward.

**Repository**: https://github.com/bebetterthan/project-pribadi
**Issue Summary**: `rl_module/phase1b_three_tools/TRAINING_ISSUES_SUMMARY.md`

---

## 📊 APPENDIX: Quick Stats

| Metric | V13 (Best Eval) | V16 (Best Rollout) | Target |
|--------|-----------------|-------------------|---------|
| Mean Reward | 4321 | 4025 | >4726 |
| Nmap Usage | 65% | 60% | 50-90% ✅ |
| Variance | 1700 | 1955 | <200 ❌ |
| Rollout Mean | 3630 | 3910 | N/A |
| vs Baseline | +19% | +11% | >30% ❌ |
| Training Time | 9 min | 9 min | N/A |

**Conditional Learning**: ✅ **ACHIEVED**
**Performance Target**: ❌ **91% there (4321/4726)**
**Stability**: ⚠️ **High variance but consistent nmap usage**
