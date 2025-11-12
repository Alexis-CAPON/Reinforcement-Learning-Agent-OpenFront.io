# Attack Execution Fix - CRITICAL BUG RESOLVED

## Problem

**Agent actions were not affecting territory** - visualizer showed actions like "N @ 100%" but tiles never changed.

**Symptoms:**
- Actions displayed correctly in visualizer
- Troops accumulated (+330/turn)
- Territory stayed constant (e.g., stuck at 52 tiles, 0.5%)
- Game tick was working (troops growing)
- **Attacks were NOT being executed**

## Root Cause

**Wrong AttackExecution constructor signature!**

Phase3 was using a completely different constructor than phase1-2:

### Phase3 (BROKEN):
```typescript
new AttackExecution(
  this.rlPlayer.id(),           // ❌ Player ID (number)
  sourceUnits.map(u => u.id()), // ❌ Unit IDs (array)
  targetId,
  targetTile,
  attackTroops
)
```

### Phase1-2 (WORKING):
```typescript
new AttackExecution(
  attackTroops,      // ✅ Number of troops to attack with
  this.rlPlayer,     // ✅ Player OBJECT (not ID!)
  targetId           // ✅ Target player ID
)
```

## The Fix

**File:** `game_bridge/game_bridge_visual.ts`

**Line 372-376:** Changed AttackExecution constructor

```typescript
// BEFORE (BROKEN):
const attack = new AttackExecution(
  this.rlPlayer.id(),
  sourceUnits.map(u => u.id()),
  targetId,
  targetTile,
  attackTroops
);

// AFTER (FIXED):
const attack = new AttackExecution(
  attackTroops,      // startTroops
  this.rlPlayer,     // _owner (Player object, not ID!)
  targetId           // _targetID
);
```

## AttackExecution Constructor Signature

From `base-game/src/core/execution/AttackExecution.js` line 7:

```javascript
constructor(
  startTroops = null,    // Number: troops to attack with
  _owner,                // Player: attacking player OBJECT
  _targetID,             // Number: target player ID
  sourceTile = null,     // Optional: for boat attacks
  removeTroops = true    // Optional: whether to remove troops from owner
)
```

**Key insight:** The second parameter must be the **Player object**, not player ID!

## Testing Results

### Before Fix (debug_visualizer.py):
```
Step 1: Action = N @ 50%
   → Tiles: 52 (change: +0)  ❌
   → Troops: 25330 (change: +330)

Step 2: Action = E @ 50%
   → Tiles: 52 (change: +0)  ❌
   → Troops: 25660 (change: +330)
```

**Territory never changed despite actions!**

### After Fix (debug_visualizer.py):
```
Step 1: Action = N @ 50%
   → Tiles: 52 (change: +0)
   → Troops: 12500 (change: -12500)  ← Attack initiated

Step 2: Action = E @ 50%
   → Tiles: 53 (change: +1)  ✅ TERRITORY CHANGED!
   → Troops: 6478 (change: -6022)

Step 3: Action = N @ 50%
   → Tiles: 54 (change: +1)  ✅ TERRITORY CHANGED!
   → Troops: 3391 (change: -3087)

Steps 4-10: Territory expanding every turn! ✅
   → Final: 61 tiles (+9 tiles from 52)
```

**Attacks now working perfectly!**

### Full Episode Test (visualize_game.py):

**Model:** `runs/run_20251101_194915/checkpoints/single_phase_final.zip`

**Results:**
- **Start:** 52 tiles (0.5% territory)
- **Step 500:** 552 tiles (5.5% territory) - 10x growth!
- **Step 1000:** 1118 tiles (11.2% territory)
- **Step 1700:** 2548 tiles (25.5% territory) - **PEAK!** 🎯
- **Step 2839:** 0 tiles (eliminated)

**Agent actively expanded to 25.5% territory before being eliminated!**

This is **MASSIVE improvement** compared to before when agent stayed at 52 tiles forever.

## Why This Fix is Critical

Without this fix, the entire RL training pipeline was broken:

1. ❌ **Attacks didn't work** → Territory never changed
2. ❌ **Rewards didn't make sense** → Territory change reward always 0
3. ❌ **Agent couldn't learn** → No feedback for actions
4. ❌ **Visualizer was misleading** → Showed actions but nothing happened

With this fix:

1. ✅ **Attacks work** → Territory expands when attacking
2. ✅ **Rewards are meaningful** → Territory change reward is non-zero
3. ✅ **Agent can learn** → Gets proper feedback for actions
4. ✅ **Visualizer is accurate** → Shows real gameplay

## Impact on Training

### Previous Training (run_20251101_194915):

This run was trained with **broken attacks**:
- Agent learned IDLE behavior (95% WAIT actions)
- No territory expansion (stuck at 0-2%)
- Negative rewards (-2000 to -4300)
- Learning getting worse (-109% improvement)

**But even with broken attacks,** the visualizer now shows this model **CAN expand territory** when attacks work! It reached 25.5% territory in the test.

### Future Training:

With **working attacks** + **improved rewards** (from FIXES_APPLIED.md):

Expected improvements:
- ✅ Agent takes active actions (action bonus +0.5)
- ✅ Territory expands (reward ±5000 per full map)
- ✅ Learns to attack effectively (immediate feedback)
- ✅ Better final performance (positive rewards)

## Files Modified

1. **`game_bridge/game_bridge_visual.ts`**
   - Fixed `attackDirection()` method (line 372-376)
   - Changed AttackExecution constructor to match phase1-2
   - Added better logging for attack debugging

## Comparison with Phase1-2

Phase3 now uses the **exact same** AttackExecution constructor as phase1-2:

**Phase1-2:** `game_bridge/game_bridge_visual.ts` line 409-411
```typescript
this.game.addExecution(
  new AttackExecution(attackTroops, this.rlPlayer, targetId)
);
```

**Phase3 (after fix):** `game_bridge/game_bridge_visual.ts` line 372-376
```typescript
const attack = new AttackExecution(
  attackTroops,
  this.rlPlayer,
  targetId
);
this.game.addExecution(attack);
```

**Identical constructor signatures!** ✅

## How We Found This Bug

1. User reported: "actions say N @ 100% but territory doesn't change"
2. Created `debug_visualizer.py` to test attack execution
3. Confirmed: attacks shown but tiles never changed
4. Compared phase3 with phase1-2 working implementation
5. Found constructor signature mismatch
6. Fixed by matching phase1-2 exactly
7. Verified with debug test: attacks now work!

## Lessons Learned

1. **Always compare with working implementation** - Phase1-2 had the answer!
2. **Player object vs Player ID** - Common mistake in game engine APIs
3. **Test incrementally** - Debug script caught the issue immediately
4. **Visualization is critical** - Without visualizer, bug would be invisible

## Next Steps

With attacks now working:

1. ✅ **Attack execution fixed** (this document)
2. ✅ **Improved rewards applied** (FIXES_APPLIED.md)
3. 🔄 **Run new training** with both fixes:
   ```bash
   python src/train.py --device mps --n-envs 12 --total-timesteps 100000 --no-curriculum --num-bots 10
   ```
4. 📊 **Visualize new model** to confirm active play
5. 📈 **Scale up training** if performance improves (500K steps, more bots)

## Visualization

**HTML replay:** `visualizations/attack_fix_test.html`

Shows the agent actively attacking and expanding from 0.5% to 25.5% territory!

Open in browser to watch the full replay.

---

**Status:** ✅ FIXED (November 1, 2025)

**Impact:** CRITICAL - Enables entire RL training pipeline
