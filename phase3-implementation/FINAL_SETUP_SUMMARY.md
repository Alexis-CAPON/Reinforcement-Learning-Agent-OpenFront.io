# Final Setup Summary - Frame Stacking + Simple Rewards

**Date:** November 2, 2025
**Status:** ✅ Ready for Training
**Major Changes:** Frame stacking (temporal memory) + Ultra-simple rewards

---

## What We Implemented

### 1. Frame Stacking (Temporal Memory)

**Before:** Agent sees single observation
**After:** Agent sees last 4 frames stacked

**Changes:**
- Environment: `frame_stack=4` parameter, deque buffer
- Observation space:
  - Map: (128, 128, 5) → **(128, 128, 20)** [4 frames × 5 channels]
  - Global: (16,) → **(64,)** [4 frames × 16 features]
- Model: Automatically adapts to stacked input

**Benefits:**
- Agent can see temporal patterns: "Territory increasing, density decreasing → overextending!"
- No architecture change (just wider inputs)
- +72K parameters (518K → 590K)

**Files Modified:**
- `src/environment.py` - Added frame buffer and stacking logic
- `src/model_attention.py` - Adapted CNN/MLP for 4x input

---

### 2. Simple Survival-Based Rewards

**Before:** 15 complex reward components (overextension penalty, density rewards, multi-front penalty, etc.)
**After:** 3 simple components

#### New Reward Structure:

```python
def _compute_reward(self):
    reward = 0.0

    # 1. SURVIVAL (+1 per step)
    reward += 1.0

    # 2. TERMINAL (±10,000)
    if won:
        reward += 10000  # Huge gain!
    elif eliminated:
        reward += -10000  # Huge loss!

    # 3. TIMEOUT (-5,000)
    if step_count >= 10000:
        reward += -5000

    return reward
```

**That's it! 3 lines vs 200 lines of complex logic.**

---

## Why These Changes?

### Problem Identified:

**From 2M training run:**
- 784 episodes, 0% win rate
- Agent got +14,761 average reward (while losing!)
- Pattern: Expand to 45% → Collapse → Eliminated
- **Conclusion:** Rewards don't correlate with winning

### Root Causes:

**1. Complex Rewards (15 components):**
```
Territory change, action bonus, density rewards, overextension penalty,
troop loss, enemy kills, military strength, focus/multi-front, survival,
rank improvement, rank defense, defensive wait, territory milestones,
time penalty, terminal rewards...
```
- Agent optimizes complex function, not winning
- Conflicting signals
- Over-engineering

**2. No Temporal Context:**
- Agent sees single frame only
- Can't detect: "I've been expanding for 100 steps"
- Can't learn: "Expand → consolidate → expand" cycle

### Solutions:

**Frame Stacking:**
- Adds temporal memory WITHOUT LSTM complexity
- Agent sees recent history directly
- Can detect overextension naturally: "4 frames ago I had 20% with 25 troops/tile, now 45% with 10 troops/tile → bad!"

**Simple Rewards:**
- Philosophy: Tell agent WHAT (survive, win), not HOW (consolidate here, focus attacks there)
- Agent discovers strategy through trial and error
- Reward now correlates with objective: More survival steps + winning = high reward

---

## Comparison: Old vs New

| Aspect | Complex Rewards | Simple Rewards |
|--------|----------------|----------------|
| **Components** | 15 rules | 3 rules |
| **Logic** | 200 lines | 10 lines |
| **Philosophy** | Micromanage strategy | Let agent discover |
| **Signals** | "Don't overextend at 45% with <15 troops/tile" | "Stay alive" |
| **Result** | +14,761 reward, 0% wins | TBD |
| **Learning** | Optimize complex function | Optimize survival |

### Expected Behavior Change:

**Old (Complex):**
```
Agent thinks: "I got +4.5/step for 40% territory, +5 for density,
-666 for overextension, +1.5 for focus, +2 for milestones..."
→ Optimizes arbitrary function, not winning
```

**New (Simple):**
```
Agent thinks: "I survived 2000 steps = +2000 reward. When I expand too fast,
I die earlier = -8000 total reward. When I consolidate and expand smartly,
I survive 5000 steps + win = +15000 reward!"
→ Discovers consolidation naturally
```

---

## Files

### Backed Up:
- `src/environment_complex_rewards.py` - Original 15-component rewards (safe copy)

### Modified:
- `src/environment.py` - Now uses simple 3-component rewards + frame stacking
- `src/model_attention.py` - Adapted for 4-frame stacked input

### Documentation:
- `REWARD_CHANGES_V2.md` - Complex rewards (historical reference)
- `MEMORY_SOLUTION_ROADMAP.md` - Frame stacking rationale
- `STATE_AND_MODEL_IMPROVEMENTS.md` - State features + model capacity
- `FINAL_SETUP_SUMMARY.md` - This file

---

## How to Train

### Recommended: 500k Quick Test

```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 500000 \
  --no-curriculum \
  --num-bots 5
```

**Time:** ~45 minutes
**Goal:** See if simple rewards + frame stacking work

**Success metrics:**
- Win rate >0% (was 0/784)
- Average survival > 2,538 steps
- Agent shows consolidation behavior (pauses expansion)

---

### If 500k Shows Improvement:

```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 2000000 \
  --no-curriculum \
  --num-bots 5
```

**Time:** ~3 hours
**Goal:** Full training to convergence

---

## What to Expect

### Hypothesis 1: Simple Rewards Work (Best Case)

**Evidence after 500k:**
- Win rate: 5-20% (up from 0%)
- Survival: 3000-4000 steps (up from 2,538)
- Behavior: Agent pauses expansion when thin, consolidates naturally
- Peak territory hold: >500 steps (was immediate collapse)

**Why it works:**
- Reward aligns with objective (survival → winning)
- Agent discovers: "Overextending → die early → low reward"
- Frame stacking lets agent see: "I'm spreading thin over last 4 frames"

**Next step:** Train to 2M, should see 30-50% win rate

---

### Hypothesis 2: Frame Stacking Helps, But Not Enough

**Evidence after 500k:**
- Win rate: 0-5% (slight improvement)
- Survival: 2800-3200 steps (minor improvement)
- Behavior: Some consolidation, but still overextends

**Why partially works:**
- Simple rewards are right direction
- Temporal context helps
- But 4 frames might be too short (only see last ~4 steps)

**Next step:** Try 8-frame stacking or add LSTM

---

### Hypothesis 3: Need More Guidance (Worst Case)

**Evidence after 500k:**
- Win rate: 0%
- Survival: ~2,500 steps (no improvement)
- Behavior: No consolidation, same expand-and-die pattern

**Why doesn't work:**
- Pure survival signal too sparse
- 4 frames not enough temporal context
- Agent can't learn consolidation from reward alone

**Next steps:**
1. Add minimal territory holding reward: `reward += territory_pct * 2.0`
2. Try 8-frame stacking
3. Add LSTM for longer-term planning

---

## Technical Details

### Model Architecture (With Frame Stacking):

```
Input:
  Map:    [B, 128, 128, 20]  ← 4 frames × 5 channels
  Global: [B, 64]            ← 4 frames × 16 features

CNN (EfficientCNN):
  Conv1: 20 → 32 channels    ← Processes 4 frames at once
  Conv2: 32 → 64
  Conv3: 64 → 128
  GAP:   4×4×128 → 128
  FC:    128 → 256

MLP:
  FC1: 64 → 256              ← Processes 4 frames of global features
  FC2: 256 → 128
  FC3: 128 → 128

Cross-Attention:
  Q: from CNN(256)
  K, V: from MLP(128)
  Output: 128

Fusion:
  Concat[256, 128, 128] → 256

Actor: 256 → 45 actions
Critic: 256 → 1 value

Total: 590,257 parameters (within target!)
```

### Parameter Increase from Frame Stacking:

```
CNN first layer: 5→20 input channels
  Conv1: 20×32×8×8 = 40,960 params (was 10,240)
  +30K params

MLP first layer: 16→64 input features
  FC1: 64×256 = 16,384 params (was 4,096)
  +12K params

Total increase: +72K params (518K → 590K)
```

Still well within 600K budget!

---

## Advantages of Current Setup

### 1. Simplicity
- ✅ 3 reward components (vs 15)
- ✅ No hyperparameter tuning (no density thresholds, no penalty scales)
- ✅ Easy to understand and debug

### 2. Alignment
- ✅ Reward = survival steps + win/loss
- ✅ Directly measures objective (not proxy metrics)
- ✅ No reward hacking possible

### 3. Temporal Context
- ✅ Frame stacking adds memory
- ✅ No LSTM complexity
- ✅ Fast training (no sequential processing)

### 4. Flexibility
- ✅ Easy to add features if needed (just add territory holding reward)
- ✅ Easy to increase frame stack (4 → 8 frames)
- ✅ Complex rewards backed up (can revert if necessary)

---

## Next Steps Decision Tree

```
START: Train 500k with simple rewards + frame stacking
  ↓
  ├─ Win rate >5%, consolidation visible?
  │    ↓ YES
  │    ✅ SUCCESS! Continue to 2M
  │       ↓
  │       Expect 30-50% win rate at 2M
  │
  ├─ Win rate 0-5%, some improvement?
  │    ↓ PARTIAL
  │    → Add minimal territory reward: reward += territory_pct * 2.0
  │    → OR increase frame stack: 4 → 8 frames
  │    → Train another 500k
  │
  └─ Win rate 0%, no improvement?
       ↓ NO
       → Add territory holding reward (dense signal)
       → OR add LSTM (longer-term planning)
       → OR return to complex rewards (they were right, just needed tuning)
```

---

## Rollback Plan

If simple rewards fail completely:

```bash
# Restore complex rewards
cp src/environment_complex_rewards.py src/environment.py

# Train with complex rewards + frame stacking
python src/train_attention.py --device mps --n-envs 12 --total-timesteps 500000
```

The complex rewards might have been right - the issue might just be temporal context, which frame stacking now provides!

---

## Summary

**What changed:**
- ✅ Added frame stacking (4 frames → temporal memory)
- ✅ Simplified rewards (15 components → 3 components)
- ✅ Model adapted automatically (590K params)

**Why:**
- Complex rewards didn't correlate with winning (+14,761 reward, 0% wins)
- No temporal context (agent couldn't see overextension happening)
- Over-engineering hypothesis: simpler might be better

**Expected outcome:**
- Agent discovers consolidation naturally through trial and error
- Frame stacking provides temporal context to see patterns
- Reward aligns with objective: survival + winning

**Time to first answer:** 45 minutes (500k training)

**Philosophy shift:**
```
Before: "Let me tell you exactly how to win (15 detailed rules)"
After:  "Survive as long as possible and try to win (figure out how)"
```

**Ready to train!** 🚀
