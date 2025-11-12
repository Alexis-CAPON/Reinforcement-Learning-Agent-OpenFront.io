# Ready to Train - Logarithmic Survival Rewards

**Date:** November 2, 2025
**Status:** ✅ READY TO TRAIN

---

## Final Configuration

### Rewards (Logarithmic + Rank-Based)

**Every 100 steps:**
- **Early game (0-1000):** rank_percentile × 100
- **Mid game (1000-2500):** rank_percentile × 200 (2x)
- **Late game (2500-5000):** rank_percentile × 400 (4x)
- **End game (5000+):** rank_percentile × 800 (8x)

**Terminal:**
- **Victory:** +20,000 (huge!)
- **Eliminated:** -20,000 (catastrophic!)
- **Timeout:** -10,000

### Example Rewards (Rank 1 throughout):

| Time | Per 100 Steps | Cumulative |
|------|---------------|------------|
| Step 500 | +83 | +415 |
| Step 1500 | +167 | +2,920 |
| Step 3000 | +333 | +11,245 |
| Step 5000 | +667 | +19,570 |
| **+ Win** | +20,000 | **+39,570** |

**Message to agent:** "Survive to late game = MASSIVE reward!"

---

## Why This Will Work

### Natural Strategy Emergence:

**Early Death (Step 500):**
- Reward: ~+400 (early survival) - 20,000 (eliminated) = **-19,600**
- Agent learns: "Dying early = terrible!"

**Mid Death (Step 2000):**
- Reward: ~+3,000 (early+mid survival) - 20,000 = **-17,000**
- Agent learns: "Dying mid-game = bad, but survived longer"

**Late Death (Step 4000):**
- Reward: ~+14,000 (early+mid+late) - 20,000 = **-6,000**
- Agent learns: "Made it far, but losing hurts less"

**Victory (Step 5000):**
- Reward: ~+19,570 (survival) + 20,000 (win) = **+39,570**
- Agent learns: "THIS IS THE GOAL!"

### Consolidation Emerges:

```
Scenario 1: Aggressive expansion at step 2000
→ Overextend → Die at step 2200
→ Reward: +3,500 - 20,000 = -16,500
→ Miss all late-game rewards (would have been +11,000 more!)

Scenario 2: Consolidate at step 2000
→ Survive → Reach step 4000
→ Reward: +14,000 (+ potential win)
→ Gained +10,500 vs Scenario 1!

Agent discovers: "Patience in mid-game = access to huge late-game rewards"
```

---

## Architecture

**Model:** BattleRoyaleExtractorWithAttention (590K params)
- Frame stacking: 4 frames (temporal memory)
- CNN: 128×128×20 → 256 features
- MLP: 64 → 128 features
- Cross-attention fusion
- Total: 590,257 parameters ✅

**Observation:**
- Map: (128, 128, 20) - 4 frames × 5 channels
- Global: (64,) - 4 frames × 16 features (including overextension flag!)

---

## Training Command

### Quick Test (500k - 45 minutes):
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 500000 \
  --no-curriculum \
  --num-bots 5
```

### Full Training (2M - 3 hours):
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 2000000 \
  --no-curriculum \
  --num-bots 5
```

---

## Expected Results

### Success Indicators (After 500k):

**Wins:**
- ✅ Win rate: 5-20% (was 0%)
- ✅ Some episodes reach step 3000+ (access late-game rewards)

**Survival:**
- ✅ Avg survival: 3000-3500 steps (was 2,538)
- ✅ Longest run: >5000 steps (was 4,123)

**Behavior:**
- ✅ Early aggression (0-1000 steps)
- ✅ Mid consolidation (1000-2500 steps) - **KEY INDICATOR**
- ✅ Late strategic play (2500+ steps)
- ✅ Less expand-and-die at step 2400

**Rewards:**
- ✅ Episodes reaching step 3000: +10,000-15,000 reward
- ✅ Winning episodes: +35,000-40,000 reward
- ✅ Early death: -15,000 to -19,000 (strong negative signal)

---

## What Logarithmic Rewards Solve

### Old Problem (Pure survival +1/step):
```
Step 2400: +2,400 reward
Overextend and die at step 2500: +2,500 - 10,000 = -7,500 total
→ Agent thinks: "I got 2,500 rewards, not too bad"
```

### New Solution (Logarithmic):
```
Step 2400: +~3,500 reward (early+mid game)
Overextend and die at step 2500: +3,600 - 20,000 = -16,400 total
→ Agent thinks: "I LOST 16,400! Plus I missed late-game rewards!"

If I had consolidated:
→ Survive to step 4000: +14,000 (early+mid+late)
→ Difference: +14,000 vs -16,400 = 30,400 reward difference!
```

**The math heavily favors reaching late game!**

---

## Files

- `src/environment.py` - **Logarithmic rewards implemented**
- `src/environment_complex_rewards.py` - Backup (15-component version)
- `src/model_attention.py` - Frame stacking model (590K params)
- `src/train_attention.py` - Training script

---

## Philosophy

**We tell the agent:**
- "Survive longer = better (exponentially so!)"
- "High rank = better at each phase"
- "Winning = MASSIVE bonus"

**Agent must discover:**
- When to expand aggressively (early game)
- When to consolidate (mid game before late-game rewards kick in)
- When to push for win (late game with strong position)
- Optimal troop density, multi-front management, strategic timing

**The logarithmic curve creates natural pressure to reach late game = natural consolidation!**

---

## Ready! 🚀

Start training and watch for:
1. **Episode lengths increasing** (2,538 → 3,000+)
2. **Mid-game consolidation** (agent pauses expansion around step 2000)
3. **Win rate >0%** (first wins should appear by 500k)
4. **Reward scaling** (later episodes getting higher rewards as they reach late game)

Good luck! This should work. 🎯
