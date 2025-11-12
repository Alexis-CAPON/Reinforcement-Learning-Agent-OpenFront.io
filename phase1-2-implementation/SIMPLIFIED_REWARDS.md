# Simplified Reward System

## Overview

Transitioned from complex dense reward structure to **simplified change-based rewards** that focus on what the agent can directly control through its actions.

## Motivation

### Problems with Dense Reward System

**Old approach (v1.0.1-dense-rewards)**:
- Per-step territorial control: +2.0 × tiles_owned
- Per-step enemy penalty: -0.5 × enemy_tiles
- Tile changes: ±50
- Troop growth: +0.01 × troop_increase
- Time penalty: -0.1
- Terminal rewards: ±1,000

**Critical Issues**:
1. **Accumulation catastrophe**: Enemy penalty accumulated to -150k to -2M over 5,000 steps
2. **Terminal rewards meaningless**: Win/loss (±1,000) was only 0.4% of total reward signal
3. **Wrong credit assignment**: Rewarding STATE (having tiles) not ACTION (gaining tiles)
4. **Perverse incentives**: Agent learned "minimize enemy" instead of "maximize own territory"
5. **Debugging nightmare**: Hard to understand why rewards were so extreme

**Example catastrophic failure** (run_20251031_003801):
```
Enemy: 1,100 tiles
Agent: 10 tiles
Per-step penalty: -550
Over 5,000 steps: -2,750,000
Terminal penalty: -1,000
Total reward: ~-2,652,500 (every episode identical)
```

### New Approach: Focus on Changes

**Key insight**: Reward the agent for ACTIONS (tile changes) not STATES (having tiles).

## Reward Structure

### Formula

```python
reward = 0.0

# 1. Tile changes (direct result of agent's actions)
tile_change = tiles_after - tiles_before
reward += tile_change * 100

# 2. Small time penalty (efficiency incentive)
reward += -0.1

# 3. Terminal outcomes (meaningful!)
if won:
    reward += 10000
elif lost:
    reward += -10000
elif timeout:
    reward += -5000

return reward
```

### Reward Components

| Component | Scale | Purpose |
|-----------|-------|---------|
| **Tile gained** | +100 per tile | Immediate strong reward for expansion |
| **Tile lost** | -100 per tile | Immediate strong penalty for losses |
| **Time penalty** | -0.1 per step | Encourage efficiency without dominating |
| **Victory** | +10,000 | Make winning highly valuable |
| **Defeat** | -10,000 | Make losing strongly aversive |
| **Timeout** | -5,000 | Encourage decisive action |

## Reward Scale Analysis

### Winning Episode (5,000 steps)

Assume agent captures 50 tiles, loses 10:

```
Component              | Calculation        | Total    | % of Total
-----------------------|--------------------|----------|------------
Tile gains             | 50 × 100          | +5,000   | +33%
Tile losses            | 10 × 100          | -1,000   | -7%
Time penalty           | 5,000 × 0.1       | -500     | -3%
Victory bonus          | 1 × 10,000        | +10,000  | +67%
-----------------------|--------------------|----------|------------
TOTAL REWARD           |                    | +13,500  | 100%
```

**Key insight**: Terminal reward (winning) is **67%** of total - it matters!

### Losing Episode (5,000 steps)

Assume agent captures 20 tiles, loses 25:

```
Component              | Calculation        | Total    | % of Total
-----------------------|--------------------|----------|------------
Tile gains             | 20 × 100          | +2,000   | +17%
Tile losses            | 25 × 100          | -2,500   | -21%
Time penalty           | 5,000 × 0.1       | -500     | -4%
Defeat penalty         | 1 × -10,000       | -10,000  | -83%
-----------------------|--------------------|----------|------------
TOTAL REWARD           |                    | -11,000  | 100%
```

**Key insight**: Defeat penalty is **83%** of total - losing is BAD!

### Stalemate/Timeout (5,000 steps)

Assume agent captures 30 tiles, loses 30 (net zero):

```
Component              | Calculation        | Total    | % of Total
-----------------------|--------------------|----------|------------
Tile gains             | 30 × 100          | +3,000   | +35%
Tile losses            | 30 × 100          | -3,000   | -35%
Time penalty           | 5,000 × 0.1       | -500     | -6%
Timeout penalty        | 1 × -5,000        | -5,000   | -59%
-----------------------|--------------------|----------|------------
TOTAL REWARD           |                    | -5,500   | 100%
```

**Key insight**: Timeout is punished, but not as harshly as losing.

## Comparison with Old System

### Before (Dense Rewards)

**Typical episode** (5,000 steps, agent owns 40 tiles average, enemy owns 60):
```
Territorial control:  +400,000  (+80/step × 5,000)
Enemy penalty:        -150,000  (-30/step × 5,000)
Tile changes:         +250
Time penalty:         -500
Victory bonus:        +1,000
-------------------------
TOTAL:                +250,750

Terminal reward: 0.4% of total
```

**Problem**: Agent gets massive rewards just for EXISTING, not for ACTING.

### After (Simplified)

**Typical episode** (5,000 steps, net +40 tiles):
```
Tile gains (50):      +5,000
Tile losses (10):     -1,000
Time penalty:         -500
Victory bonus:        +10,000
-------------------------
TOTAL:                +13,500

Terminal reward: 67% of total
```

**Win**: Agent only gets rewards for ACTIONS (tile changes) and OUTCOMES (win/loss).

## Advantages

### 1. **No Accumulation Problems**
- Rewards only when tiles change (not every step)
- Scales properly regardless of episode length
- No catastrophic accumulation scenarios

### 2. **Clear Credit Assignment**
- Reward appears when tile changes happen
- Direct connection between action → tile change → reward
- Model can learn "attack successful territory X → gained tiles → got reward"

### 3. **Terminal Outcomes Matter**
- Win/loss is 67-83% of total reward signal
- Agent strongly incentivized to WIN not just expand
- No confusion about ultimate objective

### 4. **Simpler to Debug**
- Only 3 components instead of 6
- Easy to understand reward values
- Can manually verify calculations

### 5. **Correct Incentive Structure**
- "Gain tiles" not "have tiles"
- "Prevent losses" not "prevent enemy from existing"
- "Win the game" not "survive long enough"

### 6. **Works for Any Episode Length**
- 100-step game: Terminal reward dominates (~95%)
- 1,000-step game: Terminal reward ~70%
- 5,000-step game: Terminal reward ~67%
- 10,000-step game: Terminal reward ~60%

Always meaningful but not overwhelming!

## What We Removed

### ❌ Territorial Control Per-Step (+2.0 × tiles)
**Why removed**: Accumulated to massive values, rewarded STATE not ACTION

### ❌ Enemy Expansion Penalty (-0.5 × enemy_tiles)
**Why removed**: Catastrophic accumulation, wrong focus (enemy instead of self)

### ❌ Troop Growth Reward (+0.01 × troops)
**Why removed**: Too indirect, not clearly connected to actions

## What We Kept

### ✅ Tile Change Rewards
- Increased from ±50 to ±100 (2× stronger)
- Now the PRIMARY per-step signal

### ✅ Time Penalty
- Kept at -0.1 (unchanged)
- Still encourages efficiency

### ✅ Terminal Rewards
- Increased from ±1,000 to ±10,000 (10× stronger)
- Now the DOMINANT signal (67-83% of total)

## Expected Learning Behavior

With simplified rewards, the model should learn:

1. **Early training**: Random exploration, frequent tile changes
2. **Mid training**: Learns that gaining tiles → positive reward
3. **Late training**: Learns that winning → massive reward, optimizes for victory
4. **Emergent strategy**: Learns to balance expansion speed vs troop preservation

The model will naturally learn optimal attack percentages through:
- Small attacks (10-20%) → slow expansion → lower intermediate rewards
- Large attacks (60-80%) → fast expansion but vulnerability → might lose tiles
- **Optimal balance emerges** from reward feedback

## Configuration

In `configs/phase1_config.json`:

```json
{
  "version": "1.0.2-simplified-rewards",
  "reward": {
    "per_tile_change": 100,
    "per_step": -0.1,
    "win_bonus": 10000,
    "loss_penalty": -10000,
    "timeout_penalty": -5000
  }
}
```

## Implementation

In `rl_env/openfrontio_env.py:_calculate_reward()`:

```python
def _calculate_reward(self, state_before, state_after) -> float:
    reward = 0.0

    # 1. Tile changes
    tile_change = state_after['tiles_owned'] - state_before['tiles_owned']
    reward += tile_change * 100

    # 2. Time penalty
    reward += -0.1

    # 3. Terminal rewards
    if state_after['has_won']:
        reward += 10000
    elif state_after['has_lost']:
        reward += -10000
    elif self.step_count >= self.max_steps:
        reward += -5000

    return reward
```

## Expected Training Results

With simplified rewards, we expect:

- **More stable training**: No catastrophic accumulation scenarios
- **Faster convergence**: Clear credit assignment accelerates learning
- **Better win rate**: Terminal rewards incentivize victory
- **Interpretable behavior**: Can understand why agent chooses actions

## Migration Notes

### Breaking Changes

Old models trained with dense rewards are **NOT COMPATIBLE** with simplified rewards. They learned a completely different value function.

**Must retrain from scratch** with new reward structure.

### Version History

- `v1.0.0`: Original sparse rewards (terminal only)
- `v1.0.1-dense-rewards`: Dense rewards with accumulation problems
- `v1.0.2-simplified-rewards`: **Current** - Simplified change-based rewards

## Next Steps

1. ✅ Implementation complete
2. 🔄 **Train new model from scratch** with simplified rewards
3. 📊 **Monitor learning**:
   - Check reward scales make sense
   - Verify win rate improves
   - Watch tile change patterns
4. 🎮 **Visualize learned strategy**:
   - See what attack percentages emerge
   - Verify agent prioritizes winning
5. 📈 **Compare performance** vs dense reward approach

The model now has clean, interpretable rewards focused on the right objectives!
