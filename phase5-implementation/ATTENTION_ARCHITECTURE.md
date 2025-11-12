# Multi-Scale Attention Architecture

Phase 5 now includes spatial and channel attention mechanisms inspired by AlphaStar and other state-of-the-art RL systems for complex strategy games.

## Architecture Overview

```
Input Observations (3 scales)
    ↓
Global Map (128×128) ──→ AttentionCNN ──→ 256 features
Local Map (128×128)  ──→ AttentionCNN ──→ 256 features  ─┐
Tactical Map (64×64) ──→ AttentionCNN ──→ 256 features   │
                                                          ├──→ Cross-Attention
Global Features ─────→ MLP ───────────→ 128 features    │         ↓
                                                          └─→ Fusion → Policy/Value
```

## Attention Mechanisms

### 1. Spatial Attention

**Purpose**: Focus on important spatial regions (borders, enemy concentrations, threats)

**How it works**:
- Generates attention weights over H×W spatial dimensions
- Uses 1×1 convolutions to create attention map
- Applies spatial softmax to normalize weights
- Multiplies features by attention map

**Example**: On a border-focused layer, attention weights will be high near enemy borders and low in the interior of your territory.

```python
attention = softmax(conv(features))  # (B, 1, H, W)
attended = features * attention      # Focus on important areas
```

### 2. Channel Attention

**Purpose**: Learn which feature channels are most important

**How it works**:
- Global average pooling to get channel importance
- FC layers to generate per-channel weights
- Sigmoid activation for 0-1 weights
- Multiplies each channel by its importance weight

**Example**: May learn to focus on "enemy territory" channel while downweighting "neutral territory" channel during aggressive play.

```python
pooled = avg_pool(features)          # (B, C)
weights = sigmoid(fc(pooled))        # (B, C)
attended = features * weights        # Focus on important channels
```

### 3. Attention CNN Branch

Each spatial scale (global, local, tactical) uses a CNN with interleaved attention:

```
Conv Layer 1 → ReLU → BatchNorm → Spatial Attention
    ↓
Conv Layer 2 → ReLU → BatchNorm → Channel Attention
    ↓
Conv Layer 3 → ReLU → BatchNorm → Spatial Attention
    ↓
Conv Layer 4 → ReLU → BatchNorm → Channel Attention
    ↓
Flatten → FC → 256 features
```

**Why interleave?**
- Spatial attention focuses on WHERE to look
- Channel attention focuses on WHAT to look for
- Alternating allows progressive refinement

### 4. Cross-Attention Fusion

**Purpose**: Learn which spatial scale is most relevant for current game state

**How it works**:
- Query: Global scalar features (game state)
- Key/Value: Stack of [global, local, tactical] spatial features
- Multi-head attention (8 heads) learns scale importance
- Learnable scale weights allow model to prefer certain scales

```python
# Project all features to 256-dim attention space
global_proj = proj(global_spatial)
local_proj = proj(local_spatial)
tactical_proj = proj(tactical_spatial)
query = proj(global_features)

# Stack spatial features
spatial_kv = stack([global_proj, local_proj, tactical_proj])

# Cross-attention: which scale matters most?
attended = cross_attention(query, spatial_kv, spatial_kv)
```

**Example**: During early game expansion (lots of territory), global scale may have high attention. During late-game border conflicts, tactical scale may dominate.

## Model Parameters

**Without Attention** (baseline multi-scale):
- Parameters: ~1.5M
- Memory: ~6 MB model + 23 MB observations (8 envs)

**With Attention** (current implementation):
- Parameters: ~2.0M (+33%)
- Memory: ~8 MB model + 23 MB observations (8 envs)

**Trade-off**:
- ✅ Better focus on relevant features
- ✅ Potential for improved performance on complex maps
- ⚠️ Slightly more memory usage
- ⚠️ Slightly slower training (~10-15%)

## Usage

### Training with Attention (Default)

```bash
cd phase5-implementation/src

# Train on 1024×1024 map
python train_multiscale.py \
  --map your_1024x1024_map \
  --num-bots 10 \
  --total-timesteps 1000000
```

The script now uses `MultiScaleExtractorWithAttention` by default.

### If You Want Non-Attention Version

If you want to compare or use the simpler version without attention:

1. Edit `train_multiscale.py`
2. Change import:
   ```python
   from model_multiscale import MultiScaleExtractor
   ```
3. Change model creation:
   ```python
   'features_extractor_class': MultiScaleExtractor,
   ```

## Expected Benefits

### 1. Better Border Focus
Spatial attention should learn to focus on borders where attacks happen, rather than wasting compute on interior tiles.

### 2. Dynamic Scale Selection
Cross-attention allows model to dynamically choose which observation scale matters most:
- Early game: Global view (finding expansion opportunities)
- Mid game: Local view (managing multiple fronts)
- Late game: Tactical view (precise border control)

### 3. Feature Discrimination
Channel attention helps model learn which map features are most relevant:
- Aggressive agent: Focus on enemy territory channels
- Defensive agent: Focus on border threat channels
- Expansionist: Focus on neutral territory channels

## Monitoring Attention

While training, you can inspect attention patterns (requires custom logging):

```python
# In your evaluation code
obs = env.get_observation()
with torch.no_grad():
    features = model.policy.features_extractor(obs)
    # Access attention weights from intermediate layers
```

Consider adding TensorBoard logging of attention weights to visualize:
- Which spatial regions get high attention
- Which channels are most important
- Which scales dominate in different game phases

## Comparison: No Attention vs Attention

| Aspect | No Attention | With Attention |
|--------|--------------|----------------|
| **Parameters** | 1.5M | 2.0M |
| **Training Speed** | Baseline | ~85% speed |
| **Memory** | Baseline | +2 MB |
| **Border Precision** | Good | Better (focused) |
| **Scale Fusion** | Concatenation | Learned attention |
| **Interpretability** | Low | Medium (can visualize) |

## Troubleshooting

### Out of Memory

If attention version causes OOM:

```bash
# Reduce environments
python train_multiscale.py --n-envs 4

# Reduce batch size
python train_multiscale.py --batch-size 64

# Or switch to non-attention version (edit train_multiscale.py)
```

### Slower Training

Attention adds ~10-15% overhead. On MPS:
- Non-attention: ~8-10 hours for 1M steps
- With attention: ~10-12 hours for 1M steps

### Not Learning Better

Attention is not a magic bullet. It helps if:
- ✅ Map has complex spatial patterns
- ✅ Strategic scale-switching is important
- ✅ Long training (attention needs more data to learn)

May not help if:
- ⚠️ Map is simple/small
- ⚠️ Short training (<500K steps)
- ⚠️ Single-scale already works well

## Next Steps

1. **Train baseline** (non-attention multi-scale) for 1M steps
2. **Train attention** version for 1M steps
3. **Compare performance** in actual games
4. **Visualize attention** (optional) to understand what model learned
5. **Choose best** for your use case

---

**The attention architecture is now integrated and ready to use!** 🧠✨
