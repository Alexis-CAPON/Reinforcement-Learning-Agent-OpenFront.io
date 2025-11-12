# Reward Structure Changes v2 - Defensive Consolidation

**Date:** November 1, 2025
**Goal:** Fix "expand-and-die" pattern where agent reaches 45% territory then collapses
**Strategy:** Incentivize consolidation and defensive play when holding large territory

---

## Problem Identified from Visualization

**Agent Behavior:**
- ✅ Steps 0-2400: Expands aggressively from 0.5% → 45% territory (Rank 1)
- ❌ Steps 2400-4375: Loses 100 tiles/100 steps, collapses from Rank 1 → 7 (eliminated)

**Root Cause:** Agent learned "always expand" but never learned "consolidate when overextended"

---

## Changes Implemented

### 1. ⬇️ Territory Change Reward (Reduced)
**Before:** ±5 per 1%
**After:** ±2 per 1%
**Why:** Make consolidation more attractive relative to raw expansion

```python
# OLD:
reward += territory_change * 100 * 5

# NEW:
reward += territory_change * 100 * 2
```

---

### 2. ⬇️ Action Bonus (More Restrictive)
**Before:** +0.3 when troops > 3,000
**After:** +0.1 when troops > 5,000
**Why:** Encourage patience - only attack when very strong

```python
# OLD:
if not self.last_action_was_wait:
    if state.population > 3000:
        reward += 0.3

# NEW:
if not self.last_action_was_wait:
    if state.population > 5000:
        reward += 0.1
```

---

### 3. ⬆️ Density Rewards (Strengthened)
**Before:** +2.0 for optimal, -3.0 for too thin
**After:** +5.0 for optimal, -10.0 for too thin
**Why:** Make consolidation (15-35 troops/tile) much more attractive

```python
# OLD:
if 15 <= troops_per_tile <= 35:
    reward += 2.0
elif troops_per_tile < 8:
    reward -= 3.0

# NEW:
if 15 <= troops_per_tile <= 35:
    reward += 5.0  # 2.5x stronger
elif troops_per_tile < 8:
    reward -= 10.0  # 3.3x stronger penalty
```

---

### 4. 🆕 Overextension Penalty (NEW!)
**Purpose:** Heavily penalize having lots of territory but spreading too thin

**Triggers:** When territory > 20% AND troops/tile < 15

```python
if state.territory_pct > 0.20 and troops_per_tile < 15:
    overextension_factor = (15 - troops_per_tile) / 15
    overextension_penalty = -overextension_factor * 1000
    reward += overextension_penalty
```

**Examples:**
- 25% territory, 10 troops/tile → **-333 penalty**
- 40% territory, 8 troops/tile → **-466 penalty**
- 45% territory, 5 troops/tile → **-666 penalty** (disaster!)

This directly addresses the visualization pattern where agent hit 45% with very thin troops.

---

### 5. 🆕 Rank Defense Bonus (NEW!)
**Purpose:** Reward holding winning position instead of risky expansion

**Triggers:** When Rank 1 AND territory > 30%

```python
if state.rank == 1 and state.territory_pct > 0.30:
    if state.territory_pct >= prev.territory_pct:
        reward += 5.0  # Holding or gaining - excellent!
    elif state.territory_pct < prev.territory_pct - 0.02:
        reward -= 10.0  # Losing territory when winning - BAD!
```

**Why:** In visualization, agent was Rank 1 at 45% but kept attacking. This teaches: "You're winning, hold your ground!"

---

### 6. 🆕 Territory Milestone Bonuses (NEW!)
**Purpose:** Reward achieving AND maintaining strategic thresholds

```python
if state.territory_pct >= 0.30:
    reward += 2.0  # Holding 30%+ (strong position)
if state.territory_pct >= 0.40:
    reward += 3.0  # Holding 40%+ (dominating)
if state.territory_pct >= 0.50:
    reward += 5.0  # Holding 50%+ (winning position)
```

**Why:** Incentivize staying in winning territory ranges, not just reaching them once

---

## Summary Table

| Reward Component | Old Value | New Value | Change |
|------------------|-----------|-----------|--------|
| Territory change | ±5 per 1% | ±2 per 1% | -60% |
| Action bonus | +0.3@3k | +0.1@5k | -67%, higher threshold |
| Density (optimal) | +2.0 | +5.0 | +150% |
| Density (too thin) | -3.0 | -10.0 | +233% penalty |
| **Overextension penalty** | **None** | **-333 to -666** | **NEW!** |
| **Rank defense bonus** | **None** | **+5/-10** | **NEW!** |
| **Territory milestones** | **None** | **+2/+3/+5** | **NEW!** |

---

## Expected Behavior After Changes

### Early Game (0-20% territory)
- Agent still expands aggressively
- Overextension penalties not active yet
- Action bonus encourages attacks when strong

### Mid Game (20-40% territory)
- **Overextension penalties kick in** when troops < 15/tile
- Agent learns to pause expansion and consolidate
- Density rewards (+5.0) make waiting attractive
- Territory milestones reward holding 30%+

### Late Game (40%+ territory, Rank 1)
- **Rank defense bonus activates**
- Losing territory = -10 penalty (strong deterrent)
- Milestone bonuses (+3, +5) reward holding position
- Only expand when troops replenished

---

## Predicted Episode Pattern

**Before (expand-and-die):**
```
0-2400 steps:  Expand to 45% territory (Rank 1)
2400-4375:     Collapse from 45% → 0% (Rank 7, eliminated)
Result:        0% win rate
```

**After (consolidate-and-win):**
```
0-1000 steps:  Expand to 20-25% territory
1000-2500:     Consolidate (hit overextension penalties, wait/defend)
2500-4000:     Expand to 40-50% when troops strong
4000-6000:     Hold position (rank defense + milestones active)
6000+:         Push for 80% victory when dominant
Result:        Should see >0% win rate
```

---

## Key Improvements

1. **Addresses visualization pattern:** The -666 overextension penalty at 45% territory with thin troops directly targets the collapse point

2. **Balances aggression:** Still rewards early expansion, but teaches "when to stop"

3. **Rewards consolidation:** +5.0 density bonus + milestone bonuses make defensive play viable

4. **Protects winning position:** Rank defense bonus teaches "holding 40% is better than risking 45%"

5. **Maintains strategic complexity:** Agent must learn timing - when to expand vs when to consolidate

---

## Testing Recommendation

Train with same parameters:
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 2000000 \
  --no-curriculum \
  --num-bots 5
```

**Success metrics:**
- Win rate >0% (was 0/784)
- Peak territory hold time >500 steps (was immediate collapse)
- Episodes reaching 50%+ territory
- Rank 1 maintained for >1000 consecutive steps

**Expected improvement:** Agent should survive longer and occasionally win by learning the "expand → consolidate → expand → win" cycle instead of "expand → die".
