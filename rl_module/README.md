# 🤖 Agent-P Reinforcement Learning Module

## 📋 Overview

**Standalone RL module** untuk mengoptimalkan AI decision-making dalam penetration testing menggunakan adaptive learning. Module ini **independen** dari backend utama untuk memudahkan experimentation dan training.

## 🎯 Learning Objectives

Menggunakan Reinforcement Learning untuk optimize:

1. **🛠️ Tool Selection & Sequencing** - Belajar urutan tool optimal berdasarkan scan state
2. **⚡ Model Selection (Flash vs Pro)** - Optimasi cost-performance tradeoff dinamis
3. **⚙️ Parameter Tuning** - Adaptive scan parameters (timing, concurrency, rate limits)
4. **🎨 Strategy Personalization** - Per-target strategy optimization

## 🏗️ Architecture

```
rl_module/
├── 📁 envs/              # Gym-like environments (ReconEnv, etc.)
├── 📁 agents/            # RL agent implementations (DQN, PPO)
├── 📁 baselines/         # Baseline agents (Random, Hardcoded, Greedy)
├── 📁 models/            # Neural network architectures
├── 📁 policies/          # Policy implementations
├── 📁 rewards/           # Reward function definitions
├── 📁 data/              # Training data & scenarios
│   └── scenarios/        # Pre-generated scan scenarios
├── 📁 training/          # Training scripts & utilities
├── 📁 integration/       # Backend integration layer
├── 📁 checkpoints/       # Saved model checkpoints
├── 📁 logs/              # TensorBoard logs
├── 📁 experiments/       # Experiment tracking
├── 📁 tests/             # Unit tests
├── 📁 notebooks/         # Jupyter notebooks untuk analysis
└── 📁 docs/              # Documentation
```

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Navigate to RL module
cd rl_module

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import gymnasium; import stable_baselines3; print('✅ Ready!')"
```

### 2️⃣ Generate Training Scenarios

```bash
# Generate 100 diverse pentesting scenarios
python data/generate_scenarios.py --count 100 --output data/scenarios/training.json

# Generate 20 test scenarios (held-out)
python data/generate_scenarios.py --count 20 --output data/scenarios/test.json --seed 999
```

### 3️⃣ Run Baseline Evaluation

```bash
# Evaluate all baseline agents
python evaluate_baselines.py

# Expected output:
# RandomAgent:     Coverage: 35%, Time: 180s
# HardcodedAgent:  Coverage: 72%, Time: 120s
# GreedyAgent:     Coverage: 64%, Time: 95s
```

### 4️⃣ Train RL Agent

```bash
# Train PPO agent (500k timesteps)
python train.py --env recon --algo ppo --timesteps 500000

# Monitor training
tensorboard --logdir logs/
```

### 5️⃣ Evaluate Trained Agent

```bash
# Compare RL agent vs baselines
python evaluate.py --model checkpoints/recon_ppo_500k.zip

# Visualize episode
python visualize.py --model checkpoints/recon_ppo_500k.zip --scenario 42
```

## 📊 Core Components

### 🌍 Environments

#### **ReconEnv** - Reconnaissance Workflow

- **State**: `[subdomains_found, endpoints_found, open_ports, tools_used, time_elapsed, scan_phase]`
- **Actions**: 9 discrete actions (subfinder, httpx, nmap variants, focus, finish)
- **Reward**: Finding quality + time efficiency - redundancy penalty

```python
from envs.recon_env import ReconEnv

env = ReconEnv(scenarios_path="data/scenarios/training.json")
obs, info = env.reset()
action = env.action_space.sample()
obs, reward, done, truncated, info = env.step(action)
```

#### **ModelSelectionEnv** - Flash vs Pro Optimizer

- **State**: `[query_complexity, budget_remaining, scan_progress, historical_accuracy]`
- **Actions**: 3 discrete (use_flash, use_pro, use_ollama)
- **Reward**: Accuracy - cost_penalty - latency_penalty

### 🤖 RL Agents

#### **Tool Selector Agent (DQN)**

```python
from agents.tool_selector_agent import ToolSelectorAgent

agent = ToolSelectorAgent(env)
agent.train(total_timesteps=500000)
agent.save("checkpoints/tool_selector_best.pt")
```

#### **Model Selector Agent (Q-Learning)**

```python
from agents.model_selector_agent import ModelSelectorAgent

agent = ModelSelectorAgent(env)
agent.train(episodes=1000)
agent.save("checkpoints/model_selector.pkl")
```

### 📈 Baseline Agents

**RandomAgent** - Absolute lower bound
**HardcodedAgent** - Current best practice (sequential workflow)
**GreedyAgent** - Immediate reward maximization (no planning)

## 🧪 Algorithms

| Algorithm           | Use Case         | State Space | Action Space        |
| ------------------- | ---------------- | ----------- | ------------------- |
| **DQN**             | Tool selection   | Discrete    | Discrete (9 tools)  |
| **PPO**             | Parameter tuning | Continuous  | Continuous (params) |
| **Q-Learning**      | Model selection  | Discrete    | Discrete (3 models) |
| **Multi-Objective** | Cost-Performance | Mixed       | Mixed               |

## 📈 Training Progress

### Expected Learning Curve

```
Iteration 1 (100k steps):  RL beats Random (3x improvement)
Iteration 2 (250k steps):  RL beats Greedy (1.8x improvement)
Iteration 3 (500k steps):  RL beats Hardcoded (1.3x improvement) ✅ SUCCESS
```

### Metrics to Monitor

- **Coverage**: % of subdomains/endpoints/ports discovered
- **Efficiency**: Time to reach 90% coverage
- **Cost**: API cost per scan (for model selection)
- **Redundancy**: # of duplicate scans
- **Action Distribution**: Which actions are used most

## 🔗 Integration dengan Backend

```python
# In backend code
from rl_module.integration import RLOrchestrator

# Initialize with trained models
rl_orch = RLOrchestrator(
    tool_selector_checkpoint="rl_module/checkpoints/tool_selector_best.pt",
    model_selector_checkpoint="rl_module/checkpoints/model_selector.pkl"
)

# Use in HybridOrchestrator
next_tool = rl_orch.select_next_tool(
    scan_phase="reconnaissance",
    completed_tools=["subfinder"],
    findings_summary={"subdomains": 15}
)

model_choice = rl_orch.select_model(
    query_complexity="high",
    cost_budget_remaining=0.50
)
```

## 📊 TensorBoard Monitoring

```bash
# Start TensorBoard
tensorboard --logdir logs/

# View at http://localhost:6006
# Metrics:
# - Episode rewards (line chart)
# - Average reward (rolling window)
# - Episode length trend
# - Action distribution (histogram)
# - Loss values
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific component
pytest tests/test_environment.py -v

# Test with coverage
pytest tests/ --cov=envs --cov-report=html
```

## 📝 Configuration

Edit `configs/rl_config.yaml`:

```yaml
training:
  algorithm: ppo # or dqn, ddpg
  total_timesteps: 500000
  batch_size: 64
  learning_rate: 0.0003
  gamma: 0.99

exploration:
  strategy: epsilon_greedy
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.995

rewards:
  finding_weight: 15.0
  efficiency_weight: -0.05
  redundancy_penalty: -20.0
  completion_bonus: 100.0

environment:
  max_episode_steps: 50
  time_limit_seconds: 600
  scenarios_path: data/scenarios/training.json
```

## 🎓 Learning Resources

- 📘 [RL Book: Sutton & Barto](http://incompleteideas.net/book/the-book-2nd.html)
- 🌐 [OpenAI Spinning Up](https://spinningup.openai.com/)
- 📚 [Stable Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- 🎥 [DeepMind RL Course](https://www.youtube.com/playlist?list=PLqYmG7hTraZDM-OYHWgPebj2MfCFzFObQ)

## 📋 Development Checklist

### Phase 1: Setup ✅

- [x] Create project structure
- [x] Install dependencies
- [x] Setup git & gitignore
- [ ] Verify GPU availability (if using)

### Phase 2: Data Generation

- [ ] Generate 100 training scenarios
- [ ] Generate 20 test scenarios
- [ ] Validate scenario quality
- [ ] Test loading performance (<0.1s)

### Phase 3: Environment Implementation

- [ ] Implement ReconEnv
- [ ] Implement tool simulators
- [ ] Implement action masking
- [ ] Test environment (>1000 steps/sec)

### Phase 4: Baseline Evaluation

- [ ] Implement RandomAgent
- [ ] Implement HardcodedAgent
- [ ] Implement GreedyAgent
- [ ] Document baseline performance

### Phase 5: RL Training

- [ ] Configure PPO/DQN
- [ ] Setup callbacks & logging
- [ ] Train for 100k steps (sanity check)
- [ ] Train for 500k steps (full run)
- [ ] Compare to baselines

### Phase 6: Integration

- [ ] Create integration layer
- [ ] Test with backend
- [ ] Deploy trained models
- [ ] Monitor production performance

## 🐛 Troubleshooting

### Training not improving?

1. Check reward distribution (`python analyze_rewards.py`)
2. Verify action masking is working
3. Reduce learning rate or increase batch size
4. Check if environment is too easy/hard

### Out of memory?

1. Reduce batch size
2. Reduce buffer size
3. Use gradient accumulation
4. Enable mixed precision training

### Training too slow?

1. Verify environment runs >1000 steps/sec
2. Use vectorized environments (n_envs=8)
3. Enable GPU if available
4. Profile code for bottlenecks

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

Apache 2.0 - See main project LICENSE

## 👥 Authors

- **bebetterthan** - Initial work

---

**Status**: 🚧 Under Development  
**Version**: 0.1.0  
**Last Updated**: November 2025  
**Next Milestone**: Complete Phase 2 (Data Generation)
