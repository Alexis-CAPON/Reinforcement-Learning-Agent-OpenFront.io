# OpenFront.io Phase 3 - Battle Royale RL Agent

Train an RL agent to play OpenFront.io in battle royale mode (50+ opponents) using PPO with curriculum learning.

## 🚨 CRITICAL FIXES APPLIED (Nov 1, 2025)

Two critical bugs have been fixed that were preventing the agent from learning:

1. **✅ Attack Execution Fixed** ([ATTACK_EXECUTION_FIX.md](ATTACK_EXECUTION_FIX.md))
   - **Problem:** Attacks weren't being executed - territory never changed
   - **Fix:** Corrected AttackExecution constructor (must pass Player object, not ID)
   - **Impact:** Agent can now capture territory (tested: 0.5% → 25.5%)

2. **✅ Reward Structure Improved** ([FIXES_APPLIED.md](FIXES_APPLIED.md))
   - **Problem:** Agent learned to only do WAIT actions (95%+ idle)
   - **Fix:** Applied phase1-2 proven rewards + action bonus + higher entropy
   - **Impact:** Encourages active play instead of passive survival

**These fixes are critical for training.** Previous runs were affected by broken attack execution.

## Overview

**Mode**: FFA Battle Royale (50 bots)
**Goal**: Outlast opponents, reach 80% territory
**Algorithm**: PPO with curriculum learning
**Training Time**: 2-4 days (M4 Max or RTX 3060)
**Expected Win Rate**: 25-40%

## Architecture

```
State:     128×128×5 map + 16 global features
Actions:   Direction (9) + Intensity (5) + Build (2) = 90
Model:     CNN + MLP (~500K params)
Algorithm: PPO
Training:  900K steps = 2-4 days
```

### Network Architecture

- **CNN Branch**: 128×128×5 → 512 features (spatial patterns)
- **MLP Branch**: 16 → 128 features (global state)
- **Fusion**: 640 → 256 features
- **Actor Head**: 256 → 90 actions
- **Critic Head**: 256 → 1 value

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Test Environment

```bash
python test_environment.py
```

This verifies:
- Environment can be created
- Observations have correct shapes (128×128×5 map + 16 global)
- Actions work (90 discrete actions)
- Model architecture (~500K parameters)

### 2. Train Agent

```bash
# With curriculum learning (recommended)
python src/train.py --device cpu --n-envs 8

# Without curriculum (50 bots from start)
python src/train.py --device cpu --n-envs 8 --no-curriculum
```

**Device options:**
- `cpu`: CPU training (slower)
- `cuda`: NVIDIA GPU
- `mps`: Apple Silicon GPU (M1/M2/M3/M4)

**Training phases (curriculum):**
1. **Phase 1** (100K steps): 10 bots - Learn basics
2. **Phase 2** (300K steps): 25 bots - Handle competition
3. **Phase 3** (500K steps): 50 bots - Full challenge

**Progress tracking:**
```bash
# In another terminal
tensorboard --logdir runs/
```

### 3. Evaluate Agent

```bash
# Evaluate trained model
python src/evaluate.py runs/run_TIMESTAMP/openfront_final --n-episodes 50 --num-bots 50

# Compare multiple models
python src/evaluate.py --compare \
    runs/run1/openfront_final \
    runs/run2/openfront_final \
    --n-episodes 50
```

### 4. Watch Agent Play (Visualization)

```bash
# Watch your agent play live
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip

# Play multiple games and save replays
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip \
    --num-games 5 --num-bots 25 --save-replays

# Visualize saved replays with graphs
python src/visualize_replay.py replays/replay_TIMESTAMP.json --mode all
```

**Output Example:**
```
[Step   100] Territory:   3.2% | Population:  12450 | Rank:  3/11 | Action: NE  @ 50%     | Reward:  +2.45
[Step   200] Territory:   8.7% | Population:  28900 | Rank:  2/11 | Action: S   @ 75% 🏗️  | Reward:  +5.31

Result: 🏆 VICTORY
Max Territory: 82.3%
Best Rank: 1/11
```

See [VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md) for detailed visualization options.

## Project Structure

```
phase3-implementation/
├── src/
│   ├── environment.py       # Gymnasium environment
│   ├── model.py            # Neural network architecture
│   ├── train.py            # Training script
│   ├── evaluate.py         # Evaluation script
│   ├── play_game.py        # Live game visualization
│   ├── visualize_replay.py # Replay visualization
│   └── game_wrapper.py     # Python game bridge client
├── game_bridge/            # TypeScript game interface
│   ├── game_bridge.ts
│   ├── RLConfig.ts
│   └── package.json
├── configs/
│   ├── config.yaml         # Default hyperparameters
│   └── config_quick_test.yaml  # Test configuration
├── checkpoints/            # Saved models
├── logs/                   # TensorBoard logs
├── runs/                   # Training runs
├── replays/                # Saved game replays
├── test_environment.py     # Test script
├── test_integration.py     # Integration tests
├── requirements.txt        # Dependencies
├── README.md              # This file
├── VISUALIZATION_GUIDE.md # Visualization documentation
├── PERFORMANCE_GUIDE.md   # Training speed guide
└── M4_MAX_GUIDE.md        # M4 Max optimization
```

## Observation Space

### Map Features [128, 128, 5]

- **Channel 0**: Your territory (binary mask)
- **Channel 1**: Enemy density (aggregated, normalized)
- **Channel 2**: Neutral territory (binary mask)
- **Channel 3**: Your troop density (normalized)
- **Channel 4**: Enemy troop density (aggregated, normalized)

### Global Features [16]

```python
[
    population / max_population,      # 0: Utilization
    max_population / 100000,          # 1: Capacity
    population_growth_rate,           # 2: Growing/shrinking
    territory_percentage,             # 3: % of map
    territory_change,                 # 4: Recent change
    rank / 50,                        # 5: Placement
    border_pressure / 10,             # 6: Border exposure
    num_cities,                       # 7: Infrastructure
    gold / 50000,                     # 8: Resources
    time_alive / max_time,            # 9: Survival
    game_progress,                    # 10: Phase (0-1)
    nearest_threat / 128,             # 11: Closest danger
    0, 0, 0, 0                        # 12-15: Reserved
]
```

## Action Space

**Total: 90 discrete actions** = 9 directions × 5 intensities × 2 build

- **Directions (9)**: N, NE, E, SE, S, SW, W, NW, WAIT
- **Intensities (5)**: 20%, 35%, 50%, 75%, 100% of troops
- **Build (2)**: No, Yes (build city if possible)

## Reward Function

```python
reward = 0.0

# 1. Territory change (primary)
reward += (territory_pct - prev_territory_pct) * 1000

# 2. Population management (40-50% optimal)
if 0.40 <= pop_ratio <= 0.50:
    reward += 5
elif pop_ratio < 0.20:
    reward -= 10

# 3. Win/loss
if territory_pct >= 0.80:
    reward += 10000  # Victory
if territory_pct == 0.0:
    reward -= 10000  # Eliminated

# 4. Survival
reward += 0.5  # Per step
```

## Configuration

Edit `configs/config.yaml` to customize:

```yaml
training:
  total_timesteps: 900000
  n_envs: 8
  device: cpu

ppo:
  learning_rate: 3.0e-4
  n_steps: 1024
  batch_size: 128
  gamma: 0.995
  ent_coef: 0.02

curriculum:
  phase1:
    num_bots: 10
    steps: 100000
  phase2:
    num_bots: 25
    steps: 300000
  phase3:
    num_bots: 50
    steps: 500000
```

## Training Tips

### Faster Training

```python
# More parallel environments
python src/train.py --n-envs 16

# Use GPU/MPS
python src/train.py --device mps  # or cuda
```

### Out of Memory

```python
# Reduce parallel environments
python src/train.py --n-envs 4

# Or in config.yaml:
# batch_size: 64 (down from 128)
```

### Agent Not Learning

Check:
1. Observations are normalized [0, 1]
2. Rewards are reasonable (-100 to +100 typically)
3. Game interface is working correctly
4. Try simpler curriculum (fewer bots)

## Expected Results

### Phase 1 (10 bots, 100K steps)
- Win rate: 5-10%
- Avg rank: 5-7 / 10
- Learning: Basic expansion, avoiding elimination

### Phase 2 (25 bots, 300K steps)
- Win rate: 10-20%
- Avg rank: 10-15 / 25
- Learning: Opportunistic attacks, better survival

### Phase 3 (50 bots, 500K steps)
- Win rate: 20-30%
- Avg rank: 15-25 / 50
- Learning: Consistent top-half placement, occasional wins

## Troubleshooting

### "MPS not available"
```python
# Use CPU or CUDA instead
python src/train.py --device cpu
```

### Training too slow
- Increase `--n-envs` (more parallel environments)
- Use GPU: `--device cuda` or `--device mps`
- Reduce map size in game bridge

### Agent dies early
- Start with curriculum learning (phase 1: 10 bots)
- Increase survival bonus in reward function
- Check if game interface is providing correct observations

## Next Steps

1. **Integrate Game Bridge**: Connect to actual OpenFront.io game
2. **Tune Hyperparameters**: Adjust learning rate, entropy, etc.
3. **Extend Features**: Add more observation channels or global features
4. **Advanced Techniques**: Try PPG, IMPALA, or other algorithms

## Documentation

See documentation files for details:
- `00_OVERVIEW.md` - High-level architecture
- `01_ARCHITECTURE.md` - Neural network design
- `02_STATE_ACTIONS.md` - Observation and action spaces
- `03_REWARD_TRAINING.md` - Reward function and training strategy
- `04_IMPLEMENTATION.md` - Code implementation guide

## Performance

**Hardware requirements:**
- CPU: 4+ cores
- RAM: 8 GB+
- GPU: Optional but recommended (RTX 3060 or M4 Max)

**Expected training time:**
- CPU only: 5-7 days
- M4 Max (MPS): 2-3 days
- RTX 3060 (CUDA): 2-3 days

**Inference speed:**
- Target: <10ms per decision
- Actual: ~5-10ms on M4 Max / RTX 3060

## License

See parent project for license information.

## Citation

If you use this code, please cite:

```
OpenFront.io RL Agent - Phase 3 Battle Royale
https://github.com/[your-repo]/openfrontio-rl
```
