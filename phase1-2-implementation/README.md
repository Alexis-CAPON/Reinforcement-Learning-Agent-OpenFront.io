# OpenFront.io RL - Multi-Phase Implementation

Reinforcement learning agents for OpenFront.io with progressive improvements across three phases:
- **Phase 1**: PPO baseline (no action masking enforcement)
- **Phase 2**: Enhanced PPO with improved observation space
- **Phase 3**: MaskablePPO with proper action masking ✨ **RECOMMENDED**

## Phase Comparison

| Feature | Phase 1 | Phase 2 | Phase 3 ✨ |
|---------|---------|---------|-----------|
| Algorithm | PPO | PPO | **MaskablePPO** |
| Action Space | Dict (9 targets + continuous %) | Dict (9 targets + continuous %) | **Discrete(45)** |
| Action Masking | Provided but ignored | Provided but ignored | **Enforced by algorithm** |
| Observation Features | 5 basic | **12 enhanced** | 12 enhanced |
| Neighbor Info | None | **8×2 matrix** | 8×2 matrix |
| Player Info | None | **8×3 matrix** | 8×3 matrix |
| Attack Percentages | Continuous 0-100% | Continuous 0-100% | **5 levels: [0%, 25%, 50%, 75%, 100%]** |
| Invalid Action Handling | Safety check (→ IDLE) | Safety check (→ IDLE) | **Masked during training** |
| Sample Efficiency | Baseline | Improved | **Best** (no capacity wasted) |

## Common Features (All Phases)

- **Multi-player Support**: 1 RL agent vs 7 AI bots (8 players total)
- **50×50 Map**: Training on "plains" test map
- **Fast Bridge**: Cached TypeScript bridge (~30s first reset, fast subsequent resets)
- **Headless Mode**: No UI/rendering, pure game engine
- **Full Logging**: TensorBoard integration and checkpoint management
- **Stalemate Detection**: Episodes end when agent has no valid moves
- **Proper Termination**: Win/Loss/Timeout detection

## Project Structure

```
phase1-implementation/
├── configs/
│   ├── phase1_config.json          # Phase 1 configuration (baseline PPO)
│   ├── phase2_config.json          # Phase 2 configuration (enhanced PPO)
│   └── phase3_config.json          # Phase 3 configuration (MaskablePPO) ✨
├── game_bridge/
│   ├── game_bridge_cached.ts       # Main TypeScript bridge (cached, fast resets)
│   ├── game_bridge_final.ts        # Non-cached version
│   └── RLConfig.ts                 # Custom config with tick rate support
├── rl_env/
│   ├── game_wrapper.py             # Python IPC wrapper for game
│   ├── openfrontio_env.py          # Phase 1/2 Gymnasium environment
│   ├── openfrontio_env_phase3.py   # Phase 3 environment (discrete actions) ✨
│   ├── flatten_action_wrapper.py   # Wrapper for Phase 1/2 (flatten Dict actions)
│   ├── maskable_wrapper.py         # Wrapper for Phase 3 (expose action_masks()) ✨
│   └── training_callback.py        # Custom training callbacks
├── train.py                         # Phase 1/2 training script
├── train_phase3.py                  # Phase 3 training script ✨
├── visualize_game.py                # Visualize trained agent gameplay
├── requirements.txt                 # Python dependencies
├── PHASE3_IMPLEMENTATION.md         # Phase 3 technical documentation ✨
└── README.md                        # This file
```

## Setup Instructions

### 1. Prerequisites

- **Node.js** 18+ (for game engine)
- **Python** 3.9+ (for RL training)
- **tsx** (TypeScript runner - installed via npx, no compilation needed!)

### 2. Install Python Dependencies

```bash
cd phase1-implementation
pip install -r requirements.txt
```

### 3. Test the Setup

No compilation needed! The bridge uses `tsx` to run TypeScript directly.

```bash
# Test the game bridge
python3 test_bridge_cached.py

# Test full environment integration
python3 test_environment_real.py
```

Both tests should pass showing:
- ✅ Fast map loading (~0.3s first time)
- ✅ Even faster resets (<1ms)
- ✅ Players spawn with 52 tiles each
- ✅ Game progresses normally

## Training

### Phase 3 (Recommended) ✨

Train with MaskablePPO and proper action masking:

```bash
# Full training (2M timesteps, ~3-4 hours)
python3 train_phase3.py --config configs/phase3_config.json

# Quick test (10k timesteps)
python3 train_phase3.py --config configs/phase3_config.json --timesteps 10000

# Custom output directory
python3 train_phase3.py --config configs/phase3_config.json --output runs/phase3_experiment
```

**Why Phase 3?**
- ✅ Action masking enforced by algorithm (no invalid actions predicted)
- ✅ More sample-efficient learning
- ✅ No model capacity wasted on learning invalid actions
- ✅ 5 attack percentage levels provide strategic flexibility

### Phase 1/2 (Legacy)

Train with standard PPO:

```bash
# Phase 1 (baseline)
python3 train.py --config configs/phase1_config.json --timesteps 500000

# Phase 2 (enhanced observations)
python3 train.py --config configs/phase2_config.json --timesteps 1000000
```

### Training Parameters

Edit `configs/phase1_config.json` to customize:

- **Game settings**: Map name, difficulty, max ticks
- **Environment**: Observation features, reward weights
- **Training**: Learning rate, batch size, epochs, etc.

### Monitor Training

View training progress with TensorBoard:

```bash
tensorboard --logdir runs/
```

Open http://localhost:6006 in your browser.

## Evaluation

Evaluate a trained model:

```bash
python train.py eval \
  --model runs/run_20241026_123456/best_model/best_model.zip \
  --episodes 20
```

## Configuration

### Key Configuration Parameters

**Game Configuration** (`configs/phase1_config.json`):

```json
{
  "game": {
    "map_name": "training_phase1",     // Map to use
    "opponent_difficulty": "Easy",      // Easy, Medium, Hard, Impossible
    "max_ticks": 1000,                  // Max game duration
    "tick_interval_ms": 25              // Tick speed (lower = faster, default 100ms)
  },
  "reward": {
    "per_tile_gained": 10,              // Reward per tile conquered
    "win_bonus": 1000,                  // Bonus for winning
    "loss_penalty": -1000               // Penalty for losing
  }
}
```

**PPO Hyperparameters**:

```json
{
  "training": {
    "learning_rate": 0.0003,            // Adam learning rate
    "n_steps": 2048,                    // Steps per rollout
    "batch_size": 64,                   // Minibatch size
    "n_epochs": 10,                     // Epochs per update
    "gamma": 0.99,                      // Discount factor
    "clip_range": 0.2                   // PPO clipping epsilon
  }
}
```

## Expected Results

### Phase 1 Goals

| Metric | Target (100ms ticks) | Target (25ms ticks) |
|--------|---------------------|---------------------|
| Training time | 3-5 hours (200k steps) | 1-1.5 hours (4× speedup) |
| Win rate vs Easy AI | 40-50% | 40-50% (same) |
| Avg tiles controlled | 30-40 tiles | 30-40 tiles (same) |
| Episode length | 400-800 steps | 400-800 steps (same) |

**Note**: Using faster tick rates (25ms instead of 100ms) speeds up training without changing game balance!

### Training Progress

Typical learning curve:

- **0-50k steps**: Random exploration, ~5% win rate
- **50k-100k steps**: Basic expansion learned, ~20% win rate
- **100k-150k steps**: Strategic attacks, ~35% win rate
- **150k-200k steps**: Consistent play, ~45% win rate

## Performance Optimization

### Tick Rate Speedup (4-10× faster training!)

You can speed up training significantly by reducing the tick interval without changing game balance:

```json
{
  "game": {
    "tick_interval_ms": 25  // 4× speedup (was 100ms)
  }
}
```

**How it works**: Everything in the game happens proportionally faster:
- 100ms ticks: 100 gold/tick = 1,000 gold/second
- 25ms ticks: 100 gold/tick = 4,000 gold/second
- But gameplay duration ratios stay the same!

**Recommended values**:
- `100ms` - Baseline (safest, slowest)
- `50ms` - 2× speedup (very safe)
- `25ms` - 4× speedup (recommended for Phase 1)
- `10ms` - 10× speedup (maximum, test first)

**See `docs/TICK_RATE_SPEEDUP.md` for detailed explanation.**

---

## Troubleshooting

### Common Issues

**1. "Game bridge not found" error**

Solution:
```bash
cd game_bridge
tsc game_bridge.ts
```

**2. "Cannot find module" in TypeScript**

Solution: Check that base-game path is correct. The game_bridge.ts imports assume:
```
openfrontio-rl/
├── base-game/
└── phase1-implementation/
    └── game_bridge/
```

**3. Game process crashes**

Check stderr logs:
```bash
# Add debug logging
python train.py train 2>&1 | tee training.log
```

**4. PPO not learning (flat reward curve)**

Possible causes:
- Reward scale too small/large
- Learning rate too high/low
- Environment bugs (check with manual testing)

Solutions:
- Adjust reward weights in config
- Try lr=1e-4 or lr=1e-3
- Run environment test: `python openfrontio_env.py`

**5. Episodes ending with tiles=0 but not detecting loss**

**FIXED!** The loss detection now properly checks for `tiles_owned == 0` in addition to `isAlive()`.

Verify the fix is working:
```bash
python3 verify_loss_fix.py
```

You should see ✅ markers showing episodes terminate immediately when agent loses.

See `LOSS_DETECTION_FIX.md` for details.

## Development

### Testing Individual Components

**Test game wrapper**:
```bash
cd rl_env
python game_wrapper.py
```

**Test environment**:
```bash
cd rl_env
python openfrontio_env.py
```

**Test training (quick)**:
```bash
python train.py train --timesteps 1000
```

### Debugging

Enable debug logging:

```python
# In train.py or test script
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps (Phase 2-3)

After achieving Phase 1 goals:

1. **Phase 2**: Extended training (500k steps) → 50% win rate
2. **Phase 3**: Enhanced observations (22 features) + curriculum learning → 55% win rate
3. **Phase 4**: Multi-agent self-play with Ray RLlib → 60%+ win rate

## References

- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)
- [Gymnasium Documentation](https://gymnasium.farama.org/)

## License

This project uses the OpenFront.io game engine. See base-game/LICENSE for details.
