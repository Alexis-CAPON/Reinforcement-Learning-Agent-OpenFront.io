# Phase 5: All Training Options

Phase 5 provides multiple training approaches for different map sizes and strategic requirements. This guide helps you choose the right one.

## Quick Decision Tree

```
Start here:

1. What's your map size?
   └─ ≤512×512 → Single-scale (train.py)
   └─ ≥1024×1024 → Multi-scale (train_multiscale.py)

2. Do you have disconnected territories often?
   └─ No → Use standard training
   └─ Yes → Use cluster-aware (train_clusters.py)

3. Do you want attention mechanisms?
   └─ No → Use default
   └─ Yes → model_multiscale_attention.py
```

## Option 1: Single-Scale Training (Standard)

**File**: `train.py`
**Environment**: `environment.py`
**Model**: Default CNN

### When to Use
- ✅ Map size ≤512×512
- ✅ Simple expansion strategy
- ✅ Fast training needed
- ✅ Compatible with Phase 3 models

### Observation
```python
{
    'map': (128, 128, 20),    # Downsampled spatial
    'global': (64,)            # Global features
}
```

### Action Space
```python
Discrete(45)  # 9 directions × 5 intensities
```

### Training Command
```bash
python train.py \
  --map plains \
  --num-bots 10 \
  --total-timesteps 1000000
```

### Performance
- **Training speed**: Fast (~5 hours for 1M steps on MPS)
- **Memory**: Low (~10 MB for 8 envs)
- **Strategic depth**: Moderate
- **Best for**: Small/medium maps

---

## Option 2: Multi-Scale Training (Large Maps)

**File**: `train_multiscale.py`
**Environment**: `environment_multiscale.py`
**Model**: `model_multiscale_attention.py` (with attention)

### When to Use
- ✅ Map size ≥1024×1024
- ✅ Need tactical precision
- ✅ Complex terrain
- ✅ Have GPU memory

### Observation
```python
{
    'global_map': (128, 128, 20),   # Strategic overview
    'local_map': (128, 128, 20),    # Tactical awareness
    'tactical_map': (64, 64, 20),   # Precise control
    'global': (64,)                  # Global features
}
```

### Action Space
```python
Discrete(45)  # Same as single-scale
```

### Architecture
```
Global CNN (128×128) ──┐
Local CNN (128×128)  ──┤─→ Cross-Attention ─→ Fusion ─→ Policy
Tactical CNN (64×64) ──┘        ↑
Global Features ────────────────┘
```

### Training Command
```bash
python train_multiscale.py \
  --map australia_1024x1024 \
  --num-bots 10 \
  --local-view-size 256 \
  --total-timesteps 1000000
```

### Performance
- **Training speed**: Slower (~10-12 hours for 1M steps on MPS)
- **Memory**: Higher (~25 MB for 8 envs)
- **Strategic depth**: High (strategic + tactical)
- **Best for**: Large maps, complex terrain

---

## Option 3: Cluster-Aware Training (Split Territories)

**File**: `train_clusters.py`
**Environment**: `environment_clusters.py`
**Model**: Default CNN + action masking

### When to Use
- ✅ Territory splits are common
- ✅ Need multi-front warfare
- ✅ Strategic territory control
- ✅ Complex maps with choke points

### Observation
```python
{
    'map': (128, 128, 20),
    'global': (64,),
    'clusters': (5, 6)  # Up to 5 clusters with 6 features each
}
```

### Action Space
```python
MultiDiscrete([5, 9, 5])  # cluster_id, direction, intensity
# Total: 225 actions (with masking)
```

### Training Command
```bash
pip install sb3-contrib  # Required for MaskablePPO

python train_clusters.py \
  --map plains \
  --num-bots 10 \
  --total-timesteps 1000000
```

### Performance
- **Training speed**: Moderate (~6-7 hours for 1M steps on MPS)
- **Memory**: Low-medium (~12 MB for 8 envs)
- **Strategic depth**: Very high (cluster management)
- **Best for**: Maps with splits, multi-front warfare

---

## Combination Options

### Option 4: Multi-Scale + Clusters

Combine large map support with cluster awareness.

**Status**: Not yet implemented (TODO)

**Would provide**:
- Large map observation (3 scales)
- Cluster-aware actions
- Best of both worlds

**Implementation needed**:
- Extend `environment_multiscale.py` with cluster features
- Update observation space
- Add action masking

### Option 5: Single-Scale + Clusters

Already available via `train_clusters.py`!

Use for medium maps (512×512) with territory splits.

---

## Feature Comparison Matrix

| Feature | Single-Scale | Multi-Scale | Clusters | Multi+Clusters |
|---------|--------------|-------------|----------|----------------|
| **Map size** | ≤512 | ≥1024 | Any | ≥1024 |
| **Action space** | 45 | 45 | 225 | 225 |
| **Observation size** | Small | Large | Medium | Very large |
| **Training speed** | Fast | Slow | Medium | Slowest |
| **Memory usage** | Low | High | Low | Highest |
| **Split territories** | ❌ Poor | ❌ Poor | ✅ Excellent | ✅ Excellent |
| **Large maps** | ❌ Poor | ✅ Excellent | ⚠️ OK | ✅ Excellent |
| **Strategic depth** | ⚠️ OK | ✅ Good | ✅ Good | ✅ Excellent |
| **Action masking** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Attention** | ❌ No | ✅ Yes | ❌ No | ✅ Yes |

---

## Hardware Recommendations

### CUDA GPU (16GB+)
```bash
# Best option: Multi-scale with attention
python train_multiscale.py \
  --device cuda \
  --n-envs 8 \
  --batch-size 256 \
  --map your_1024x1024_map
```

### Apple Silicon (MPS)
```bash
# Good option: Clusters or single-scale
python train_clusters.py \
  --device mps \
  --n-envs 4 \
  --batch-size 128
```

### CPU Only
```bash
# Best option: Single-scale
python train.py \
  --device cpu \
  --n-envs 2 \
  --batch-size 64 \
  --map small_map
```

---

## Training Time Estimates (1M steps)

| Setup | Hardware | Time |
|-------|----------|------|
| Single-scale | MPS | ~5 hours |
| Single-scale | CUDA | ~2-3 hours |
| Multi-scale | MPS | ~10-12 hours |
| Multi-scale | CUDA | ~5-6 hours |
| Clusters | MPS | ~6-7 hours |
| Clusters | CUDA | ~3-4 hours |
| Multi+Clusters | MPS | ~15-18 hours |
| Multi+Clusters | CUDA | ~8-10 hours |

---

## Recommended Workflow

### For Small Maps (256×256, australia_100x100)

```bash
# Phase 1: Quick test (100K steps, ~30 min)
python train.py --map australia_100x100 --total-timesteps 100000

# Phase 2: Full training (1M steps, ~5 hours)
python train.py --map australia_100x100 --total-timesteps 1000000
```

### For Medium Maps (512×512, plains)

```bash
# Option A: Standard (if territory stays connected)
python train.py --map plains --total-timesteps 1000000

# Option B: Clusters (if territory splits often)
python train_clusters.py --map plains --total-timesteps 1000000
```

### For Large Maps (1024×1024+)

```bash
# Phase 1: Validate (200K steps, ~2 hours)
python train_multiscale.py \
  --map australia_1024x1024 \
  --total-timesteps 200000

# Phase 2: Full training (2M steps, ~20 hours)
python train_multiscale.py \
  --map australia_1024x1024 \
  --total-timesteps 2000000
```

---

## Migration Guide

### From Phase 3 to Phase 5

**Phase 3 models ARE compatible** with:
- ✅ `train.py` (single-scale)
- ❌ `train_multiscale.py` (different obs space)
- ❌ `train_clusters.py` (different action space)

**To continue Phase 3 training**:
```bash
python train.py \
  --continue-from ../../phase3-implementation/runs/run_XXXXX/model_final \
  --map plains \
  --total-timesteps 2000000
```

### From Single-Scale to Multi-Scale

**Not directly compatible** - must train from scratch.

Different observation spaces prevent model transfer.

### From Standard to Clusters

**Not directly compatible** - must train from scratch.

Different action spaces (Discrete vs MultiDiscrete).

---

## What's Next?

### Already Implemented ✅
- Single-scale training
- Multi-scale with attention
- Cluster-aware with action masking
- GPU support (CUDA/MPS)
- Action masking (MaskablePPO)

### Not Yet Implemented ⏳
- Multi-scale + clusters combined
- Self-play training
- Boat/transport mechanics
- Hierarchical RL
- Curriculum learning

### Future Enhancements 🔮
- Meta-learning across maps
- Transfer learning
- Population-based training
- Multi-agent coordination

---

## Troubleshooting

### "Which option should I use?"

**Start with**: `train.py` (simplest)

**Upgrade to clusters if**: Territory splits are hurting performance

**Upgrade to multi-scale if**: Map is ≥1024×1024

### "Training is too slow"

1. Reduce `--n-envs`
2. Reduce `--batch-size`
3. Use simpler model (single-scale instead of multi-scale)
4. Use smaller map

### "Out of memory"

1. Reduce `--n-envs` (fewer parallel environments)
2. Reduce `--batch-size`
3. Use single-scale instead of multi-scale
4. Close other applications

### "Agent not learning"

1. Train longer (5M+ steps for complex scenarios)
2. Check TensorBoard for reward trends
3. Verify map is loading correctly
4. Try different learning rate (`--learning-rate 3e-4`)

---

**Choose your training option and start building your strategy AI!** 🚀

See individual documentation for details:
- `README_PHASE5.md` - Complete Phase 5 guide
- `MULTISCALE_TRAINING.md` - Multi-scale details
- `CLUSTER_AWARENESS.md` - Cluster system details
- `ATTENTION_ARCHITECTURE.md` - Attention mechanisms
- `QUICK_START.md` - Getting started quickly
