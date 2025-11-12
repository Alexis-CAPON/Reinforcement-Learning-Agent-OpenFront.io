# Phase 3 Implementation - MaskablePPO with Discrete Action Space

## Summary

Phase 3 successfully implements **MaskablePPO** from `sb3-contrib` with proper action masking. The key change was converting from a hybrid action space (Discrete + Continuous) to a pure discrete action space by discretizing the attack percentage into 5 levels.

**Status**: ✅ IMPLEMENTED AND TESTED

## The Problem

Our OpenFront.io environment has a **hybrid action space**:
```python
action_space = Dict({
    'attack_target': Discrete(9),           # Discrete: which neighbor to attack
    'attack_percentage': Box(0.0, 1.0)      # Continuous: what % of troops to send
})
```

This is a **parameterized action space** - a discrete choice (which neighbor) with continuous parameters (troop percentage).

MaskablePPO only accepts:
```python
action_space = Discrete(n)  # Pure discrete only
```

## Error Encountered

```
AssertionError: The algorithm only supports (<class 'gymnasium.spaces.discrete.Discrete'>, ...)
as action spaces but Box(0.0, [8. 1.], (2,), float32) was provided
```

This error occurs because the `FlattenActionWrapper` flattens our Dict action space into a single Box space, but MaskablePPO requires pure Discrete actions.

## What Was Implemented

Despite the limitation, the following Phase 3 infrastructure was successfully created:

### 1. Configuration: `configs/phase3_config.json`
- MaskablePPO algorithm settings
- Increased total_timesteps to 2,000,000
- Same hyperparameters as Phase 2

### 2. Wrapper: `rl_env/maskable_wrapper.py`
- Extracts `action_mask` from observation dict
- Provides `action_masks()` method required by MaskablePPO
- Removes `action_mask` from observation space (MaskablePPO requirement)

### 3. Training Script: `train_phase3.py`
- Full training pipeline with MaskablePPO
- Uses `MaskableMultiInputActorCriticPolicy`
- Proper environment wrapping chain:
  ```python
  OpenFrontIOEnv → MaskableActionWrapper → FlattenActionWrapper → Monitor
  ```

### 4. Dependencies
- Successfully installed `sb3-contrib` package

## Options Moving Forward

### Option 1: Discretize Attack Percentage ✅ RECOMMENDED
**Change action space to pure discrete:**
```python
action_space = Discrete(45)  # 9 targets × 5 percentages
# Target: 0=IDLE, 1-8=neighbors
# Percentages: 0%, 25%, 50%, 75%, 100%
```

**Pros:**
- Enables using MaskablePPO with proper action masking
- Simpler implementation (already have infrastructure)
- 5 troop percentage options still provide strategic flexibility

**Cons:**
- Loses fine-grained control over troop allocation
- Increases action space size (9 → 45 actions)

**Implementation effort:** Low (modify action space + observation space)

### Option 2: Use Parameterized Action Space Algorithm
**Algorithms designed for hybrid actions:**
- **P-DQN** (Parameterized Deep Q-Network)
- **PA-DDPG** (Parameterized Action DDPG)
- **PE-TS** (Parameterized Exploration with Thompson Sampling)

**Pros:**
- Keeps continuous attack_percentage (fine-grained control)
- Theoretically optimal for this problem type
- Can still use action masking for discrete component

**Cons:**
- More complex implementation
- May not have stable SB3-compatible implementations
- Longer development time

**Implementation effort:** High (new algorithm, custom policy, testing)

### Option 3: Continue with Phase 2 (PPO with Safety Checks)
**Keep current approach:**
- Standard PPO ignores action masks
- Environment catches invalid actions and treats as IDLE
- Model learns to avoid invalid actions through negative reward

**Pros:**
- Already working
- Simple, stable, tested

**Cons:**
- Model wastes capacity learning which actions are invalid
- Less sample efficient
- Suboptimal learning

**Implementation effort:** None (already complete)

## Recommendation

**Go with Option 1: Discretize Attack Percentage**

Reasoning:
1. **Pragmatic**: Enables proper action masking with minimal effort
2. **Strategic flexibility**: 5 percentage options (0%, 25%, 50%, 75%, 100%) cover most tactical scenarios:
   - 0% = no attack
   - 25% = probe/harass
   - 50% = balanced attack
   - 75% = strong push
   - 100% = all-in
3. **Learning efficiency**: Pure discrete space + action masking = much better sample efficiency
4. **Infrastructure ready**: All Phase 3 code is ready, just need to adjust action space

## Next Steps if Option 1 Chosen

1. **Modify action space** in environment:
   ```python
   action_space = Discrete(45)  # 9 targets × 5 percentages
   ```

2. **Update action decoding**:
   ```python
   attack_target = action // 5  # 0-8
   attack_percentage_idx = action % 5  # 0-4
   attack_percentage = [0.0, 0.25, 0.5, 0.75, 1.0][attack_percentage_idx]
   ```

3. **Update action masking**:
   ```python
   # Generate 45-element mask: 5 copies of each neighbor mask
   action_mask = np.repeat(neighbor_mask, 5)
   ```

4. **Remove FlattenActionWrapper** (no longer needed with pure Discrete)

5. **Update configs** to reflect new action space

6. **Test training** with small timesteps to validate

## Files Created

- `configs/phase3_config.json` - Phase 3 configuration
- `rl_env/maskable_wrapper.py` - Action masking wrapper
- `train_phase3.py` - MaskablePPO training script
- `PHASE3_LIMITATION.md` - This document

## Implementation Summary

Phase 3 has been **successfully implemented** with the following changes:

### Files Created/Modified:
1. **`rl_env/openfrontio_env_phase3.py`** - New Phase 3 environment with pure discrete action space
   - Action space: `Discrete(45)` instead of `Dict{Discrete(9), Box(0,1)}`
   - Action decoding: `target = action // 5`, `percentage = PERCENTAGE_VALUES[action % 5]`
   - 45-element action mask (9 targets × 5 percentages)

2. **`train_phase3.py`** - Updated to use Phase 3 environment
   - Imports `OpenFrontIOEnvPhase3` instead of `OpenFrontIOEnv`
   - Removed `FlattenActionWrapper` (no longer needed with pure Discrete)
   - Uses `MaskableActionWrapper` + `Monitor` only

3. **`configs/phase3_config.json`** - Updated configuration
   - Documented new discrete action space structure
   - Action decoding examples and percentage values
   - Updated descriptions for action_mask shape (45 elements)

### Test Results:
✅ Environment check passed (with minor warnings about obs space bounds)
✅ Training runs successfully with MaskablePPO
✅ Action masking properly enforced by algorithm
✅ Episodes complete normally with discrete actions
✅ Model learns and saves checkpoints

### Key Benefits:
- ✅ Proper action masking enforced by MaskablePPO algorithm
- ✅ No wasted model capacity on invalid actions
- ✅ Strategic flexibility maintained (5 percentage options)
- ✅ More sample-efficient learning expected
- ✅ Pure discrete action space compatible with MaskablePPO

## Next Steps

To train a full Phase 3 model:
```bash
python3 train_phase3.py --config configs/phase3_config.json
```

This will train for 2M timesteps with proper action masking. The agent should learn more efficiently than Phase 2 since it won't waste capacity learning which actions are invalid.
