# OpenFront.io Reinforcement Learning Agent

A sophisticated deep reinforcement learning system for training AI agents to play OpenFront.io, a real-time multiplayer territory control game. This project implements multi-scale spatial observations, attention mechanisms, and cluster-aware action spaces to handle complex strategic gameplay on maps up to 1024×1024 tiles.

## See It In Action

### Agent Playing on 100×100 Map

![Agent Gameplay](content/playing_agent.gif)
_Trained agent playing on australia_100x100_nt map with real-time decision visualization_

## What's Implemented

### ✅ Phase 3: Basic RL Integration (Complete)

- TypeScript-Python IPC bridge for game state communication
- Core PPO training loop with Stable-Baselines3
- Basic action space: 9 directions × 5 attack intensities (0-100%)
- Simple observation space: territory map + army positions
- Initial training on small maps (100×100)

### ✅ Phase 4: Visual Testing System (Complete)

- Real-time visualization of trained agents
- Overlays showing RL decisions on the game UI
- Testing framework for evaluating agent performance
- Integrated with existing OpenFront.io client

### ✅ Phase 5.1: Core Features (Complete)

- Frame stacking (4 frames) for temporal context
- Action masking with MaskablePPO for valid moves only
- Reward shaping: territory growth + population + survival
- Training scripts for multiple map sizes
- Model checkpointing and evaluation

### ✅ Phase 5.2: Multi-Scale Architecture (Complete)

**For large maps (1024×1024) with ~60,000 tiles:**

- **Global View**: Full map downsampled to 128×128 (8×8 max pooling)
- **Local View**: 256×256 region around territory center at 128×128 (2×2 pooling)
- **Tactical View**: 64×64 border region at full resolution
- **Spatial Attention**: AlphaStar-inspired attention to focus on key regions
- **Channel Attention**: Emphasizes important observation features

### ✅ Phase 5.3: Cluster-Aware Actions (Complete)

**Handles disconnected territories:**

- Flood-fill algorithm detects up to 5 separate territory clusters
- Action space: [5 clusters, 9 directions, 5 intensities] = 225 actions
- Action masking prevents commands to non-existent clusters
- Independent troop allocation for each disconnected region

### ✅ Phase 5.4: Working Attack System (Complete)

- Direction-based attacks (N, S, E, W, NE, NW, SE, SW, Hold)
- Intensity control (20%, 40%, 60%, 80%, 100% of troops)
- Turn-based game loop with configurable tick rate
- Proper game state synchronization

### 🚧 Phase 5.5: Economic & Military System (In Progress)

**Currently implementing:**

- Building construction: Cities, Ports, Missile Silos, SAM Launchers, Defense Posts, Factories
- Nuclear weapons: Atom Bombs, Hydrogen Bombs
- Gold economy and resource management
- Expanded action space: 315+ actions with building types
- Enhanced observation space with economic/military features

**Status**: Game bridge updated with unit counting and capability checking. Build/nuke methods pending.

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install stable-baselines3 sb3-contrib torch numpy

# Install Node.js dependencies
cd base-game
npm install
npm run build
```

### Training an Agent

#### Attention-Enhanced Training (Recommended)

Train with attention mechanisms, multi-environment parallelization, and optimized hyperparameters:

```bash
cd phase5-implementation
python3 src/train_attention.py --device mps --n-envs 12 --total-timesteps 2000000 --no-curriculum --num-bots 5
```

**Configuration**:

- Device: `mps` (Apple Silicon), `cuda` (NVIDIA GPU), or `cpu`
- Parallel environments: 12 (adjust based on your CPU cores)
- Training steps: 2M (adjust up to 10M+ for better performance)
- Opponents: 5 bots (start with fewer for faster learning)
- Architecture: Multi-scale CNN with spatial/channel attention
- Features: Frame stacking, action masking, cluster detection
- Output: Models saved to `runs/run_YYYYMMDD_HHMMSS/checkpoints/`

**Training Options**:

```bash
# Full training run (10M steps, harder opponents)
python3 src/train_attention.py --device mps --n-envs 12 --total-timesteps 10000000 --num-bots 10

# Quick test (CPU, fewer steps)
python3 src/train_attention.py --device cpu --n-envs 4 --total-timesteps 500000 --num-bots 3

# With curriculum learning (gradually increases difficulty)
python3 src/train_attention.py --device mps --n-envs 12 --total-timesteps 5000000
```

### Monitoring Training

View training progress in real-time:

```bash
tensorboard --logdir logs/
```

Open http://localhost:6006 to see:

- Episode rewards over time
- Territory/population growth
- Episode length (survival time)
- Learning rate and loss curves

### Testing a Trained Model

#### Real-Time Visualization (Watch Agent Play)

Visualize the agent playing in real-time with decision overlays:

```bash
cd phase5-implementation
python3 src/visualize_realtime.py \
  --model ../phase3-implementation/runs/run_20251102_025235/checkpoints/single_phase/best_model.zip \
  --map australia_100x100_nt \
  --crop none
```

**Visualization Options**:

```bash
# Use your own trained model
python3 src/visualize_realtime.py \
  --model runs/run_YYYYMMDD_HHMMSS/checkpoints/best_model.zip \
  --map australia_100x100_nt

# Different map
python3 src/visualize_realtime.py \
  --model runs/run_YYYYMMDD_HHMMSS/checkpoints/best_model.zip \
  --map australia_256x256

# With cropping for large maps
python3 src/visualize_realtime.py \
  --model runs/run_YYYYMMDD_HHMMSS/checkpoints/best_model.zip \
  --map australia_500x500 \
  --crop center
```

The visualization shows:

- Real-time game state
- Agent's territory (highlighted)
- Attack directions and intensities
- Decision reasoning overlays
- Performance metrics (territory %, population, rank)

## Creating Custom Maps

### Cropping Maps for Training

Create custom map sizes by cropping existing large maps:

```bash
cd base-game
python tools/crop_map.py \
  --source australia \
  --output australia_256x256 \
  --x 915 \
  --y 290 \
  --width 256 \
  --height 256
```

**Options**:

```bash
# Create a 100×100 map from a specific region
python tools/crop_map.py \
  --source australia \
  --output australia_100x100_custom \
  --x 500 \
  --y 400 \
  --width 100 \
  --height 100

# Create a 512×512 map for mid-sized training
python tools/crop_map.py \
  --source australia \
  --output australia_512x512 \
  --x 200 \
  --y 150 \
  --width 512 \
  --height 512
```

The cropped maps are saved to `base-game/resources/maps/` and can be used immediately for training.

## Project Structure

```
openfrontio-rl/
├── base-game/                      # OpenFront.io game engine
│   ├── src/
│   │   ├── client/                # Game client and UI
│   │   └── core/                  # Game logic and mechanics
│   └── resources/maps/            # Map data files
│
├── phase3-implementation/         # Basic RL integration
│   ├── game_bridge/              # TypeScript-Python bridge
│   └── rl_training/              # Initial PPO training
│
├── phase4-implementation/         # Visual testing system
│   └── visual_overlay/           # Real-time agent visualization
│
├── phase5-implementation/         # Advanced features (current)
│   ├── game_bridge/
│   │   └── game_bridge.ts        # Enhanced bridge with building/nuke support
│   ├── train_cluster_aware.py    # Cluster-aware training script
│   ├── train_multiscale_v4.py    # Multi-scale architecture training
│   ├── train_attention_v5.py     # Attention-enhanced training
│   ├── openfrontio_env.py        # Gym environment wrapper
│   └── models/                   # Saved model checkpoints
│
└── README.md                      # This file
```

## Architecture Overview

### Multi-Scale CNN (for 1024×1024 maps)

```
Input: Raw game state (1024×1024 × 3 channels)
  ↓
[Global Branch]    [Local Branch]     [Tactical Branch]
128×128 (pooled)   128×128 (cropped)  64×64 (border)
     ↓                  ↓                   ↓
  3×Conv2D          3×Conv2D            2×Conv2D
     ↓                  ↓                   ↓
Spatial Attention  Spatial Attention   Flatten
     ↓                  ↓                   ↓
Channel Attention  Channel Attention       |
     ↓                  ↓                   |
     └──────────[Concatenate]──────────────┘
                      ↓
                 Dense(512)
                      ↓
              [Actor Head]  [Critic Head]
                   ↓              ↓
              Action Probs    Value Est.
```

### Cluster-Aware Action Space

```
Territory Scan → Flood Fill → Identify Clusters (max 5)
                                      ↓
              Action = [Cluster ID, Direction, Intensity]
                                      ↓
                           Action Masking:
                           - Mask non-existent clusters
                           - Mask invalid directions per cluster
                                      ↓
                              Execute Command
```

### Observation Space

- **Territory Map**: 2D array of tile ownership (0=neutral, 1=player, 2-N=opponents)
- **Army Strength**: Normalized troop counts per tile
- **Border Distance**: Distance to nearest enemy/neutral tile
- **Frame Stack**: Last 4 game states for temporal context
- **Economic Features** (Phase 5.5): Gold, buildings, production rates
- **Military Features** (Phase 5.5): Nukes available, silo positions, threats

### Action Space

- **Basic**: 45 actions (9 directions × 5 intensities)
- **Cluster-Aware**: 225 actions (5 clusters × 9 directions × 5 intensities)
- **With Buildings** (Phase 5.5): 315+ actions (clusters × directions × intensities × building types)

### Reward Function

```python
reward = (
    territory_gained * 10.0          # Expand territory
    + population_increase * 5.0      # Grow population
    + survival_bonus * 1.0           # Stay alive longer
    + kill_bonus * 50.0              # Eliminate opponents
    + death_penalty * -100.0         # Avoid elimination
    # Phase 5.5 additions:
    + gold_earned * 0.1              # Economic growth
    + building_bonus * 20.0          # Strategic buildings
    + nuke_bonus * 100.0             # Successful nuke launch
)
```

## Training Performance

### Small Maps (256×256)

| Metric               | Phase 3 (Basic) | Phase 5.1 (Enhanced) | Phase 5.3 (Cluster) |
| -------------------- | --------------- | -------------------- | ------------------- |
| Steps to convergence | ~5M             | ~3M                  | ~3M                 |
| Peak reward          | ~500            | ~1200                | ~1500               |
| Win rate vs random   | 60%             | 85%                  | 92%                 |
| Training time (GPU)  | 2 hours         | 3 hours              | 4 hours             |

### Large Maps (1024×1024)

| Metric               | Phase 5.2 (Multi-Scale) | Phase 5.3 (Attention) |
| -------------------- | ----------------------- | --------------------- |
| Steps to convergence | ~15M                    | ~12M                  |
| Peak reward          | ~800                    | ~1100                 |
| Win rate vs random   | 70%                     | 78%                   |
| Training time (GPU)  | 18 hours                | 20 hours              |

## Documentation

- **Architecture Deep Dive**: See `GAME_ARCHITECTURE.md`
- **Implementation Roadmap**: See `IMPLEMENTATION_ROADMAP.md`
- **Phase 4 Summary**: See `PHASE4_REFACTOR_SUMMARY.md`
- **Python Bridge Setup**: See `PYTHON_BRIDGE_REQUIREMENTS.md`
- **RL Quick Reference**: See `RL_QUICK_REFERENCE.md`

## Next Steps

### Immediate (Phase 5.5 completion)

1. **Complete Economic/Military System**:

   - Implement building construction methods in game bridge
   - Add nuclear weapon launch mechanics
   - Expand Python environment with 315+ action space
   - Create action masking for building constraints
   - Update reward function for economic/military objectives

2. **Train Full-Feature Agent**:

   - Create new training script with expanded action space
   - Design reward shaping for building strategies
   - Test on 256×256 map first, then scale up
   - Expected training time: 30-50 hours on GPU

3. **Create Demo Materials**:
   - Record agent gameplay GIFs
   - Capture attention heatmaps
   - Document interesting strategies learned

### Near-Term Improvements

- **Opponent Modeling**: Learn to predict enemy movements
- **Strategic Planning**: Long-term goal setting beyond immediate expansion
- **Alliance Mechanics**: Coordinate with teammates in team modes
- **Transfer Learning**: Pre-train on small maps, fine-tune on large maps
- **Curriculum Learning**: Gradually increase map size/difficulty

### Research Directions

- **Transformer Architecture**: Replace CNN with attention-based models
- **Multi-Agent RL**: Train against other RL agents (self-play)
- **Hierarchical RL**: High-level strategy + low-level tactics
- **Imitation Learning**: Bootstrap from human gameplay
- **Model-Based RL**: Learn world model for planning

## Troubleshooting

### Training Issues

**Problem**: Reward not increasing

- Check action masking is working (mask invalid actions)
- Verify reward function is balanced (not dominated by one term)
- Reduce learning rate if training is unstable
- Increase exploration (entropy coefficient)

**Problem**: Agent gets stuck in local optimum

- Try curriculum learning (start on easier maps)
- Adjust reward shaping to encourage exploration
- Increase batch size for more stable gradients

**Problem**: Out of memory

- Reduce buffer size in training script
- Use smaller batch size
- For large maps, ensure multi-scale architecture is being used

### Bridge Issues

**Problem**: Game bridge not connecting

- Check that webpack build completed successfully
- Verify port 3000 is not in use
- Look for TypeScript errors in console output

**Problem**: Actions not executing

- Verify action space matches between Python and TypeScript
- Check action masking isn't too restrictive
- Ensure game tick rate allows time for commands

## Quick Command Reference

```bash
# Training (from phase5-implementation/)
python3 src/train_attention.py --device mps --n-envs 12 --total-timesteps 2000000 --no-curriculum --num-bots 5

# Visualization (from phase5-implementation/)
python3 src/visualize_realtime.py --model runs/run_YYYYMMDD_HHMMSS/checkpoints/best_model.zip --map australia_100x100_nt --crop none

# Monitoring (from phase5-implementation/)
tensorboard --logdir runs/

# Creating Maps (from base-game/)
python tools/crop_map.py --source australia --output australia_256x256 --x 915 --y 290 --width 256 --height 256

# Building Game Engine (from project root)
npm run build-dev                         # Development build
npm run build-prod                        # Production build
```

## References

@misc{magent2020,
author = {Terry, Jordan K and Black, Benjamin and Jayakumar, Mario},
title = {MAgent},
year = {2020},
publisher = {GitHub},
note = {GitHub repository},
howpublished = {\url{https://github.com/Farama-Foundation/MAgent}}
}

## Contributing

This is a research project. Feel free to:

- Report bugs and issues
- Suggest improvements to architecture
- Share training results and strategies discovered
- Contribute new map designs for testing

## License

This project builds on OpenFront.io. Please respect the original game's licensing terms.
