# Phase 6 - Cities Only (Simplified)

## Overview

Phase 6 is a simplified version of Phase 5 that focuses on core game mechanics:
- **Territory control** with cluster awareness
- **City building** for economic growth
- **Gold accumulation**

Removed complexity:
- All building types except Cities (Ports, Silos, SAMs, Defense Posts, Factories)
- Nuclear weapons (Atom Bombs, Hydrogen Bombs)
- Complex observation features related to removed buildings

## Key Improvements

### Action Space Reduction
- **Phase 5**: 38,500 actions = `5 × 11 × 5 × 7 × 2 × 10 × 10`
- **Phase 6**: 2,500 actions = `5 × 10 × 5 × 10`
- **Reduction**: 93.5% fewer actions

Action components:
- `cluster_id`: 0-4 (which cluster to control)
- `action_type`: 0-7=attack directions, 8=WAIT, 9=BUILD_CITY
- `intensity`: 0-4 (15%, 30%, 45%, 60%, 75%) - for attacks only
- `tile`: 0-9 (tile position within cluster for building)

### Observation Space Simplification

**Spatial Features** (128×128 map):
- Phase 5: 16 channels
- Phase 6: 8 channels
  - 0: Our territory
  - 1: Enemy territory
  - 2: Neutral territory
  - 3: Border tiles
  - 4: Troop density
  - 5: Our cities
  - 6: Enemy cities
  - 7: Valid building locations

**Global Features**:
- Phase 5: 32 features
- Phase 6: 16 features (territory, population, economy, game state)

**Cluster Features**:
- Phase 5: 6 features per cluster
- Phase 6: 4 features per cluster (tiles, troops, has_city, can_afford)

### Reward Structure (Simplified)

Reward components:
- Territory growth: +10 per tile gained
- Population growth: +5 per increase
- Survival: +1 per step
- Elimination bonus: +50 per player eliminated
- Gold accumulation: +0.1 per gold gained
- City construction: +20 per city built
- Win bonus: +200
- Death penalty: -100

## Files

### Core Files (from Phase 5)
- `src/environment_cities.py` - Main RL environment (simplified)
- `src/game_wrapper.py` - Python-TypeScript bridge (unchanged)
- `game_bridge/game_bridge.ts` - Game engine interface (unchanged)
- `train_cities.py` - Training script (updated for Phase 6)

### Testing
- `test_phase6.py` - Comprehensive test suite
- `SIMPLIFICATION_PLAN.md` - Detailed plan of what was removed

## Training

### Quick Start (Local)

```bash
# Test the environment
python3 test_phase6.py

# Start training with 1 environment (recommended for local/testing)
python3 train_cities.py --map australia_256x256 --bots 10 --timesteps 20000000 --n-envs 1 --device mps
```

### Mac Training (Apple Silicon)

**Recommended: Use 3 environments for faster training**

```bash
# Quick start
./train_cities_mac.sh

# Or with restart + cleanup
./restart_training_mac.sh

# Monitor every 10-15 minutes (IMPORTANT!)
./monitor_training_mac.sh
```

**⚠️ Important**: With multiple environments, game bridge processes can accumulate. Monitor regularly and restart when >6 processes detected. See `MAC_TRAINING_GUIDE.md` for detailed instructions.

### GPU Server Training

```bash
# Activate virtual environment
source venv/bin/activate

# Select GPU (0 or 3 are free)
export CUDA_VISIBLE_DEVICES=0

# Start training in screen/tmux
screen -S phase6_training
python3 train_cities.py --map australia_256x256 --bots 10 --timesteps 20000000 --n-envs 1 --device cuda

# Detach: Ctrl+A then D
# Reattach: screen -r phase6_training
```

### Training Parameters

Default hyperparameters (optimized for cities-only):
- Learning rate: 3e-4
- Batch size: 128
- N steps: 2,048
- N epochs: 10
- Gamma: 0.995
- Entropy coefficient: 0.02

### Expected Training Time

- **GPU**: 15-25 hours (vs 30-50 for Phase 5)
- **CPU**: 50-75 hours (vs 100-150 for Phase 5)

Faster training due to:
- 93.5% fewer actions (faster policy evaluation)
- 50% fewer features (smaller network)
- Simpler reward calculation

## Monitoring

### TensorBoard

```bash
tensorboard --logdir logs/
```

Navigate to `http://localhost:6006`

### Key Metrics to Watch

- `rollout/ep_rew_mean` - Average episode reward
- `train/policy_loss` - Policy network loss
- `train/value_loss` - Value network loss
- `train/entropy_loss` - Exploration metric

## Testing Trained Models

```bash
# Load and test a trained model
python3 test_cities.py --model models/ppo_cities_TIMESTAMP/best_model.zip

# Visual test (if implemented)
python3 visual_test_cities.py --model models/ppo_cities_TIMESTAMP/best_model.zip
```

## Differences from Phase 5

| Feature | Phase 5 | Phase 6 |
|---------|---------|---------|
| Action Space | 38,500 | 2,500 |
| Spatial Channels | 16 | 8 |
| Global Features | 32 | 16 |
| Cluster Features | 6 | 4 |
| Building Types | 6 | 1 (City) |
| Nuke Types | 2 | 0 |
| Complexity | High | Low |
| Training Time | 30-50h | 15-25h |

## Architecture

```
Phase 6
├── src/
│   ├── environment_cities.py     # RL environment (2,500 actions)
│   └── game_wrapper.py           # Game bridge (unchanged)
├── game_bridge/
│   └── game_bridge.ts            # TypeScript game interface
├── train_cities.py               # Training script
├── test_phase6.py                # Test suite
├── SIMPLIFICATION_PLAN.md        # Detailed changes
└── README.md                     # This file
```

## Known Issues / Limitations

1. **Action masking required**: Without MaskablePPO, the agent will try invalid actions
2. **Game simulation bottleneck**: 90% of time is game simulation (CPU), only 10% is GPU training
3. **Cluster handling**: Maximum 5 clusters supported, though rare to have more
4. **Enemy cities**: May not be tracked in game state (channel 6 might be empty)

## Next Steps

After training Phase 6:
1. Compare performance with Phase 5 (simpler = better learning?)
2. Evaluate if city building strategy is learned effectively
3. Consider Phase 7 with additional complexity if needed
4. Test on different maps (not just australia_256x256)

## Questions?

- Check `SIMPLIFICATION_PLAN.md` for detailed changes
- Run `python3 test_phase6.py` to verify setup
- See Phase 5 documentation for game mechanics details
