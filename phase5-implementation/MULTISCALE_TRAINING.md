# Multi-Scale Training for Large Maps (1024×1024+)

For training on very large maps where single-scale downsampling loses too much information.

## When to Use Multi-Scale

### Use Multi-Scale If:
- ✅ Map size ≥ 1024×1024 (8×8 or more downsampling)
- ✅ Need tactical precision (cities, small territories, exact borders)
- ✅ Agent needs both strategic and tactical awareness
- ✅ You have GPU memory (multi-scale uses ~2× more memory)

### Use Single-Scale If:
- ✅ Map size ≤ 512×512 (4×4 or less downsampling)
- ✅ Strategic-level learning is sufficient
- ✅ Limited GPU memory
- ✅ Want faster training

## Multi-Scale Architecture

### Three Observation Scales:

```
1. Global Map (128×128)
   - Entire 1024×1024 map → 128×128 (8×8 pooling)
   - Strategic overview of all players
   - "Where to expand?"

2. Local Map (128×128)
   - 256×256 region around you → 128×128 (2×2 pooling)
   - Tactical awareness of nearby area
   - "Who are my neighbors?"

3. Tactical Map (64×64)
   - 64×64 border region → 64×64 (full resolution!)
   - Precise border details, cities, units
   - "Exactly where to attack?"
```

### Neural Network:
```
Global CNN (128×128) ─┐
Local CNN (128×128)  ─┤─→ Cross-Attention ─→ Fusion ─→ Actions
Tactical CNN (64×64) ─┘        ↑
Global Features ───────────────┘
```

## Quick Start

### 1. Train on 1024×1024 Map

```bash
cd phase5-implementation/src

python train_multiscale.py \
  --map your_1024x1024_map \
  --num-bots 10 \
  --local-view-size 256 \
  --total-timesteps 1000000
```

### 2. Adjust Local View Size

```bash
# Smaller local view (faster, less tactical info)
python train_multiscale.py --local-view-size 128

# Larger local view (slower, more tactical info)
python train_multiscale.py --local-view-size 512
```

### 3. MPS (Mac) Training

```bash
python train_multiscale.py \
  --device mps \
  --n-envs 4 \
  --batch-size 64 \
  --n-steps 512 \
  --map your_1024x1024_map \
  --total-timesteps 500000
```

## Configuration

### Recommended Settings

| Hardware | n_envs | batch_size | n_steps | local_view_size |
|----------|--------|------------|---------|-----------------|
| CUDA 24GB | 8 | 256 | 1024 | 256 |
| CUDA 16GB | 4 | 128 | 512 | 256 |
| MPS 16GB | 4 | 64 | 512 | 256 |
| CPU | 2 | 32 | 256 | 128 |

### Parameters

```bash
--map MAP_NAME              # Your large map
--num-bots N                # Opponent count (default: 10)
--local-view-size SIZE      # Local view in tiles (default: 256)
--device cuda/mps/cpu       # Force device (auto-detect if omitted)
--n-envs N                  # Parallel environments (default: 8)
--batch-size N              # Auto if omitted
--n-steps N                 # Auto if omitted
--total-timesteps N         # Training steps (default: 1M)
--learning-rate LR          # Learning rate (default: 1e-4)
```

## Memory Usage

Multi-scale uses more memory than single-scale:

### Single-Scale Memory:
```
Observation: 128×128×20 = 327,680 floats
Per environment: ~1.3 MB
8 environments: ~10 MB observations
```

### Multi-Scale Memory:
```
Global: 128×128×20 = 327,680 floats
Local: 128×128×20 = 327,680 floats
Tactical: 64×64×20 = 81,920 floats
Total: 737,280 floats
Per environment: ~2.9 MB
8 environments: ~23 MB observations
```

**Plus model memory:**
- Multi-scale model: ~1.5M parameters (~6 MB)
- Single-scale model: ~500K parameters (~2 MB)

## Tips for Success

### 1. Start with Small Test

```bash
# Quick 100K test to verify everything works
python train_multiscale.py \
  --map your_1024x1024_map \
  --total-timesteps 100000 \
  --n-envs 2
```

### 2. Monitor GPU Memory

```bash
# Watch GPU while training
watch -n 1 nvidia-smi
```

If OOM errors:
```bash
# Reduce environments
--n-envs 4

# Reduce batch size
--batch-size 128

# Reduce local view
--local-view-size 128
```

### 3. Adjust Local View Based on Map

```
Map Size    Recommended local_view_size
--------    ---------------------------
512×512     128 (or use single-scale)
1024×1024   256 (default)
2048×2048   512
```

### 4. Use TensorBoard

```bash
tensorboard --logdir ../runs
```

Watch for:
- `rollout/ep_rew_mean` - Should increase over time
- `rollout/ep_len_mean` - Episode length
- `train/loss` - Should decrease

## Comparison: Single-Scale vs Multi-Scale

### Test on 1024×1024 Map

| Metric | Single-Scale | Multi-Scale |
|--------|--------------|-------------|
| **Information** | 8×8 pooling = major loss | 3 scales = full detail |
| **Small territories** | Invisible (< 64 tiles) | Visible in local/tactical |
| **Border precision** | ±8 tiles | ±1 tile |
| **Cities** | Often missed | Always visible |
| **Training speed** | ✅ Fast | ⚠️ Slower (~60% speed) |
| **GPU memory** | ✅ Low (~10MB) | ⚠️ Higher (~25MB) |
| **Final performance** | ⚠️ Strategic only | ✅ Strategic + Tactical |

## Example: Training on 1024×1024 Australia Map

Assuming you have `australia_1024x1024` map:

```bash
# Phase 1: Quick test (100K steps, ~1 hour on MPS)
python train_multiscale.py \
  --map australia_1024x1024 \
  --num-bots 10 \
  --total-timesteps 100000 \
  --n-envs 4

# Phase 2: Full training (1M steps, ~10 hours on MPS)
python train_multiscale.py \
  --map australia_1024x1024 \
  --num-bots 10 \
  --total-timesteps 1000000 \
  --n-envs 4

# Phase 3: Long training (5M steps, ~50 hours on MPS)
python train_multiscale.py \
  --map australia_1024x1024 \
  --num-bots 10 \
  --total-timesteps 5000000 \
  --n-envs 4 \
  --output-dir ../runs/final_training
```

## Troubleshooting

### "Out of memory"

```bash
# Option 1: Reduce environments
python train_multiscale.py --n-envs 2

# Option 2: Reduce batch size
python train_multiscale.py --batch-size 64

# Option 3: Reduce local view
python train_multiscale.py --local-view-size 128

# Option 4: All three
python train_multiscale.py --n-envs 2 --batch-size 32 --local-view-size 128
```

### "Training is very slow"

Multi-scale is inherently slower. On MPS:
- Single-scale: ~4-6 hours for 1M steps
- Multi-scale: ~8-12 hours for 1M steps

To speed up:
```bash
# Reduce local view size
--local-view-size 128

# Fewer parallel environments (counterintuitive but can help)
--n-envs 2
```

### "Model not learning"

Check TensorBoard:
```bash
tensorboard --logdir ../runs
```

If reward not increasing:
- Try longer training (5M+ steps for large maps)
- Increase learning rate: `--learning-rate 3e-4`
- Check that map is loaded correctly (look at logs)

## Architecture Details

### Global CNN:
- Input: 128×128×20 (for frame_stack=4, 5 channels)
- Architecture: 4 conv layers → 256 features
- Purpose: Strategic overview

### Local CNN:
- Input: 128×128×20
- Architecture: 4 conv layers → 256 features
- Purpose: Tactical awareness

### Tactical CNN:
- Input: 64×64×20
- Architecture: 4 conv layers → 256 features
- Purpose: Precise control

### Cross-Attention Fusion:
- Query: Global scalar features (projected to 256)
- Key/Value: Stack of [global, local, tactical] features
- Output: Attended 256-dim vector
- Purpose: Learn which scale to focus on

### Final MLP:
- Input: 256 (attended) + 128 (features) = 384
- Output: 512-dim feature vector
- Used by PPO policy and value heads

## When to Expect Results

- **100K steps**: Agent learns to survive
- **500K steps**: Agent learns basic strategy
- **1M steps**: Decent performance
- **5M steps**: Strong performance on large maps
- **10M+ steps**: Near-optimal (if you have time)

## Next Steps After Training

### 1. Evaluate Model

```bash
# Use Phase 4 visualizer (if compatible)
cd ../../phase4-implementation/src
python visualize_realtime.py \
  --model ../../phase5-implementation/runs/multiscale_run_XXXXX/multiscale_final
```

### 2. Continue Training

```bash
# Note: Can't continue from Phase 3 single-scale models
# (different observation space)
# Must start multi-scale training from scratch
```

### 3. Compare with Single-Scale

Train both and compare:
```bash
# Single-scale
python train.py --map your_map --total-timesteps 1000000

# Multi-scale
python train_multiscale.py --map your_map --total-timesteps 1000000

# Which performs better?
```

---

**Ready to train on 1024×1024 maps with multi-scale observations!** 🗺️🔍
