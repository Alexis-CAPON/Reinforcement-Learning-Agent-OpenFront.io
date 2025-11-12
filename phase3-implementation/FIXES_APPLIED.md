# Fixes Applied - Idle Agent Problem

## Problem Identified

**Agent was only doing WAIT actions** - not attacking or expanding territory.

From visualization: Agent sits idle for entire game, gets eliminated without taking any actions.

## Root Cause

This is a classic RL problem called "learned passivity":
1. **Short-term safety bias**: WAIT doesn't risk losing troops
2. **Weak reward signals**: Small rewards for expansion vs large penalties for loss
3. **Low exploration**: Agent not trying enough actions (entropy too low)
4. **Local optimum trap**: "Do nothing" appears safest in short term

## Solutions Applied

### 1. Reward Structure Overhaul ✅

Adapted proven reward design from Phase 1-2:

**Changes in `src/environment.py`:**

```python
# BEFORE (passive rewards):
- Territory change: ±100 per 1%
- No action bonus
- Very sparse rewards

# AFTER (active rewards from phase1-2):
- Territory change: ±50 per 1% (5000 per full change)
- Action bonus: +0.5 for non-WAIT actions ← KEY FIX!
- Enemy kill bonus: +5000 per elimination
- Military strength: +1.0 if in top half
- Time penalty: -0.1 (encourage efficiency)

# Terminal rewards:
- Victory: +10,000
- Defeat: -10,000
- Timeout: -5,000
```

**Key Addition - Action Bonus:**
```python
# Track WAIT actions
self.last_action_was_wait = (direction == 8)

# Reward non-WAIT actions
if not self.last_action_was_wait:
    reward += 0.5  # Encourages exploration!
```

This breaks the IDLE trap by making every non-WAIT action slightly positive.

### 2. Increased Exploration ✅

**Changes in `src/train.py`:**

```python
# BEFORE:
ent_coef=0.02  # Low exploration

# AFTER:
ent_coef=0.05  # 2.5x more exploration!
```

Higher entropy coefficient forces the model to explore more actions instead of converging to WAIT too quickly.

### 3. Enhanced Episode Logging ✅

**Changes in `src/environment.py`:**

Added detailed episode-end logging:
```python
logger.info(
    f"Episode {self.episode_count} ended: {result}\n"
    f"  Steps: {self.step_count}\n"
    f"  Tiles: {info['episode']['tiles']}\n"
    f"  Troops: {info['episode']['troops']}\n"
    f"  Territory: {info['episode']['territory_pct']*100:.1f}%\n"
    f"  Rank: {info['episode']['rank']}/{self.num_bots+1}\n"
    f"  Total Reward: {reward:.2f}"
)
```

**New file: `src/training_callback.py`:**

Custom callback that logs:
- Every episode with full details (tiles, troops, territory, rank)
- Aggregate stats every 10 episodes
- Win rate tracking
- Best performance metrics

### 4. Info Dictionary Enhancement ✅

**Changes in `src/environment.py` step() method:**

```python
info = {
    'step': self.step_count,
    'direction': self.directions[direction],
    'intensity': self.intensities[intensity_idx],
    'build': bool(build),
    'tiles': getattr(current_state, 'tiles_owned', 0),
    'troops': getattr(current_state, 'population', 0),
    'territory_pct': getattr(current_state, 'territory_pct', 0),
    'rank': getattr(current_state, 'rank', 0),
}

if terminated:
    info['episode'] = {
        'r': reward,
        'l': self.step_count,
        'tiles': ...,
        'troops': ...,
        'territory_pct': ...,
        'rank': ...,
        'won': ...,
    }
```

This provides detailed metrics for monitoring and logging.

## Expected Improvements

### Before Fixes (run_20251101_194915):
- ❌ Actions: 95%+ WAIT
- ❌ Territory: 0-2% (no expansion)
- ❌ Rewards: -2000 to -4300 (very negative)
- ❌ Episode length: ~2500 steps (just survives passively)
- ❌ Learning: Getting worse (-109% change)

### After Fixes (Expected):
- ✅ Actions: Mix of N, NE, E, SE, S, SW, W, NW (varied)
- ✅ Territory: 5-20% (active expansion)
- ✅ Rewards: -500 to +2000 (much better range)
- ✅ Episode length: Varies (dies fighting, not idling)
- ✅ Learning: Improving over time

## Files Modified

1. **`src/environment.py`**
   - Added `last_action_was_wait` tracking
   - Complete reward function overhaul (phase1-2 design)
   - Enhanced episode-end logging with detailed stats
   - Improved info dictionary

2. **`src/train.py`**
   - Increased entropy coefficient (0.02 → 0.05)
   - Added DetailedLoggingCallback import

3. **`src/training_callback.py`** (NEW)
   - Custom callback for detailed episode logging
   - Aggregate statistics every 10 episodes
   - Win rate tracking
   - Performance summaries

## Testing the Fixes

### 1. Quick Test (Verify agent takes actions):
```bash
python src/train.py --device mps --n-envs 4 --total-timesteps 10000 --no-curriculum --num-bots 5

# Watch logs for:
# - "Direction: N/E/S/W" (not just WAIT)
# - Positive action bonuses in rewards
# - Territory % increasing
```

### 2. Visualize After Training:
```bash
python src/visualize_game.py --model runs/run_TIMESTAMP/checkpoints/single_phase_final.zip --num-bots 5

# Should see:
# - Agent attacking in various directions
# - Territory expanding
# - Active gameplay (not idle)
```

### 3. Full Training Run:
```bash
python src/train.py --device mps --n-envs 8 --total-timesteps 100000 --no-curriculum --num-bots 10

# Monitor logs for:
# - Improving average rewards over time
# - Increasing territory percentages
# - Better ranks achieved
# - Occasional victories
```

## Key Metrics to Monitor

During training, watch for these improvements:

1. **Episode Logs** (every episode):
   ```
   Episode X ended: 💀 ELIMINATED
     Steps: 3456
     Tiles: 15          ← Should increase over time
     Troops: 8500       ← Should stay healthy
     Territory: 8.5%    ← Should increase over time
     Rank: 8/11         ← Should improve (lower = better)
     Total Reward: -234.5  ← Should become less negative or positive
   ```

2. **Aggregate Stats** (every 10 episodes):
   ```
   TRAINING SUMMARY (Last 10 episodes)
   Total Episodes: 50
   Win Rate: 2/50 (4.0%)  ← Should increase

   Recent Performance:
     Avg Reward: +125.3    ← Should increase
     Avg Tiles: 12.5       ← Should increase
     Avg Territory: 6.8%   ← Should increase
     Avg Rank: 9.2         ← Should decrease (improve)
     Best Territory: 15.2% ← Should increase
   ```

3. **Action Distribution** (from visualization):
   - Before: 95% WAIT, 5% other
   - After: More balanced distribution across all directions

## Why These Fixes Work

1. **Action Bonus (+0.5 per non-WAIT)**:
   - Makes any action slightly positive
   - Breaks the "do nothing is safest" trap
   - Encourages agent to try attacking

2. **Territory Change Reward (±5000 per full map)**:
   - Strong immediate feedback for expansion
   - Directly rewards the main objective
   - Borrowed from phase1-2 success

3. **Enemy Kill Bonus (+5000)**:
   - Rewards aggressive play
   - Teaches that eliminating opponents is good
   - Prevents overly defensive strategies

4. **Higher Entropy (0.05)**:
   - Forces more exploration during training
   - Prevents premature convergence to WAIT
   - Gives agent chance to discover good strategies

5. **Detailed Logging**:
   - Allows immediate identification of problems
   - Tracks multiple metrics beyond just reward
   - Helps understand agent behavior patterns

## Next Steps

After verifying the fixes work:

1. **If agent now takes actions but performs poorly**:
   - Increase training time (100K → 500K steps)
   - Add curriculum learning (5 → 10 → 25 bots)
   - Fine-tune reward weights

2. **If agent takes actions and improves**:
   - Scale up to more bots (25-50)
   - Train longer (500K-1M steps)
   - Try full 3-phase curriculum

3. **If agent still mostly WAITs**:
   - Remove WAIT from action space entirely
   - Increase entropy further (0.10)
   - Add penalty for WAIT (-1.0 per step)

## Phase 1-2 Lessons Applied

This fix applies critical lessons from phase1-2:

1. **Action bonus is essential** for breaking IDLE traps
2. **Immediate rewards** (territory change) work better than delayed rewards
3. **Higher entropy** (0.05-0.10) needed for complex action spaces
4. **Kill bonuses** encourage aggressive, winning play
5. **Detailed logging** catches problems early

These were proven effective in phase1-2 which successfully learned to play and win against multiple AI opponents.
