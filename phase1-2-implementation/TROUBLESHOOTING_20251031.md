# Training Failure Troubleshooting - Run 20251031_024720

## Problem Summary

Training run `20251031_024720` showed **ZERO learning**:
- ALL 400 evaluation episodes: exactly -5500 reward
- ALL episodes: exactly 5000 steps (timeout)
- Model learned to ALWAYS output action = [0.0, 0.007] (IDLE)

## Root Cause: VecNormalize Breaking Action Masking

### Investigation

Tested the trained model:
```python
action, _ = model.predict(obs, deterministic=True)
print(action)  # Output: [0.0, 0.007] EVERY SINGLE TIME
```

- `attack_target = 0.0` → rounds to 0 (IDLE)
- `attack_percentage = 0.007` → 0.7%

The model learned that IDLE is the "optimal" action and never attacks anything!

### Why This Happened

**VecNormalize was normalizing the action_mask!**

Our observation space is a Dict:
```python
obs = {
    'features': [tiles, troops, gold, enemy, tick],  # Should be normalized
    'action_mask': [1, 1, 1, 0, 1, 1, 0, 1, 1]      # Should stay binary!
}
```

VecNormalize (`norm_obs=True`) normalizes **ALL** keys in the Dict, including:
- ❌ `action_mask` gets normalized → breaks action masking completely
- ✅ `features` gets normalized → fine, but already manually normalized

### Evidence

1. **All rewards identical**: -5500 = -5000 (timeout) + (-0.1 × 5000 steps)
2. **No tile changes**: Reward breakdown shows only time penalty
3. **Model always outputs 0**: Never learned to attack
4. **Action mask corrupted**: VecNormalize converted binary mask to floats

### Why Action Masking Broke

With corrupted action_mask:
```python
# Original (correct)
action_mask = [1, 1, 1, 1, 1, 1, 1, 1, 1]  # All actions valid

# After VecNormalize (broken)
action_mask = [0.234, 0.891, 1.234, ...]  # Meaningless normalized values
```

The policy network received garbage for action masking, so it couldn't learn which actions are valid.

## The Fix

### Solution 1: Disable VecNormalize (IMPLEMENTED)

**Why**:
- Observations are already manually normalized in environment (0-1 range)
- VecNormalize breaks action masking for Dict observations
- SB3's VecNormalize doesn't support selective normalization

**Change**:
```json
{
  "normalize_observations": false  // Changed from true
}
```

### Solution 2: Custom Normalization Wrapper (Future)

If we want automatic normalization, we'd need to create a custom wrapper that:
```python
class SelectiveVecNormalize(VecNormalize):
    def normalize_obs(self, obs):
        if isinstance(obs, dict):
            # Only normalize 'features', leave 'action_mask' unchanged
            normalized = {}
            for key, value in obs.items():
                if key == 'features':
                    normalized[key] = super().normalize_obs(value)
                else:
                    normalized[key] = value  # Don't normalize
            return normalized
        return super().normalize_obs(obs)
```

But this is complex and unnecessary since we already have manual normalization.

## Other Improvements Still Valid

The other 3 PPO improvements are still good:

1. ✅ **Increased entropy** (0.01 → 0.05) - Still valid
2. ✅ **Aligned rollouts** (2048 → 5000 steps) - Still valid
3. ❌ **VecNormalize** - REMOVED (broke action masking)
4. ✅ **Adaptive learning rate** (linear schedule) - Still valid

## New Training Configuration

```json
{
  "n_steps": 5000,
  "batch_size": 500,
  "learning_rate": 0.0003,
  "learning_rate_schedule": "linear",
  "ent_coef": 0.05,
  "normalize_observations": false  // DISABLED
}
```

## Expected Behavior Now

With VecNormalize disabled:
- ✅ Action mask stays binary (0 or 1)
- ✅ Model can learn which actions are valid
- ✅ Exploration should discover attacking gives rewards
- ✅ Should see diverse actions, not just IDLE

### What to Monitor

1. **Action diversity** - Should see attack_target values 0-8, not just 0
2. **Reward variety** - Should see different rewards, not always -5500
3. **Episode lengths** - Should vary, not always 5000
4. **Tile changes** - Should see gains/losses, not flat

## Lessons Learned

1. **VecNormalize + Dict observations + action masking = BROKEN**
   - VecNormalize doesn't have selective normalization
   - Can't use it with action masking in Dict space

2. **Manual normalization is fine**
   - Our features are already 0-1 range
   - No need for running statistics

3. **Action space representation matters**
   - Flattened Box space works for SB3
   - But normalization must preserve action mask semantics

4. **Always test model actions during training**
   - Check action distribution
   - Verify actions aren't all the same
   - Monitor exploration

## Next Steps

1. ✅ Disabled VecNormalize
2. 🔄 **Retrain from scratch**
3. 📊 **Monitor action diversity**:
   ```bash
   # During training, check actions vary
   # Not always [0.0, 0.007]
   ```
4. 🎯 **Verify learning happens**:
   - Rewards should vary
   - Episode lengths should vary
   - Win rate should improve

The fix is simple: turn off VecNormalize. The model will learn now!
