# State Space & Model Capacity Analysis

**Date:** November 1, 2025
**Question:** Does our model have enough parameters? Is the state space sufficient?

---

## TL;DR - Assessment

| Component | Status | Verdict |
|-----------|--------|---------|
| **Model capacity (518K)** | ⚠️ Adequate but tight | Could benefit from 1-2M params |
| **State space (before)** | ❌ Missing key features | 4-5 features unused! |
| **State space (after)** | ✅ Much improved | All 16 features now meaningful |
| **Main issue** | ✅ Was rewards, not capacity | Agent demonstrated complex learning |

---

## Model Capacity Analysis (518K Parameters)

### Comparison to Similar Tasks

| Task | Complexity | Typical Params |
|------|------------|----------------|
| Atari games | Low-Medium | 1-3M |
| OpenFront.io Phase 3 | **Medium-High** | **518K** (ours) |
| StarCraft 2 micro | High | 5-10M |
| Full Dota 2 | Very High | 150M+ |

### What Agent Must Learn

1. **Spatial patterns** (CNN + attention)
   - Border identification
   - Threat detection
   - Expansion opportunities
   - ~200K params allocated ✅

2. **Strategic timing** (Global features + MLP)
   - When to expand vs consolidate
   - When to attack vs wait
   - Resource management
   - ~150K params allocated ⚠️ (might be tight)

3. **Multi-step planning**
   - Expand → Consolidate → Expand cycle
   - Long-term positioning
   - **No temporal memory (LSTM)** ❌

4. **Opponent modeling** (5 bots)
   - Predict enemy behaviors
   - Adapt to threats
   - Limited capacity ⚠️

### Evidence from 2M Training

**✅ What worked:**
- Agent expanded from 0% → 45% territory (complex spatial reasoning)
- Maintained Rank 1 for 2400+ steps (competitive play)
- Made direction-based attack decisions (strategic choice)

**❌ What didn't work:**
- Failed to learn consolidation (but rewards didn't teach it!)
- Collapsed after reaching peak (overextension)
- 0% win rate (but this is a reward problem, not capacity)

### Verdict: Model Size

**518K parameters is probably adequate for basic strategy** but could benefit from:
- **1-2M parameters** for better strategic depth
- **Recurrent layers (LSTM/GRU)** for temporal planning
- **Larger cross-attention** for better map-global fusion

---

## State Space Analysis

### BEFORE: Missing Critical Information

**Global features: 16 total**
- ✅ Features 0-6: Basic stats (population, territory, rank)
- ❌ **Feature 7: UNUSED (was cities - removed)**
- ❌ **Feature 8: UNUSED (was gold - removed)**
- ✅ Features 9-11: Survival, progress, threats
- ❌ **Features 12-15: ZEROS (reserved but empty)**

**Problems identified:**
1. **No troops/tile ratio** - Agent couldn't directly see overextension!
2. **No territory momentum** - Couldn't see if expanding or contracting
3. **No aggression tracking** - No memory of recent attacks
4. **No multi-front indicator** - Couldn't see fighting multiple wars
5. **No explicit overextension flag** - Critical for new rewards!

### AFTER: All 16 Features Now Meaningful

| Feature | Name | Purpose |
|---------|------|---------|
| 0 | Population ratio | Current strength |
| 1 | Max population | Growth potential |
| 2 | Growth rate | Production speed |
| 3 | Territory % | Map control |
| 4 | Territory change | Recent gains/losses |
| 5 | Rank | Competitive position |
| 6 | Border pressure | External threats |
| **7** | **Troops per tile** | **Overextension detector!** |
| **8** | **Territory momentum** | **Expansion velocity** |
| 9 | Time alive | Game phase |
| 10 | Game progress | Match timing |
| 11 | Nearest threat | Danger proximity |
| **12** | **Attack intensity** | **Aggression level** |
| **13** | **Multi-front count** | **Strategic focus** |
| **14** | **Rank percentile** | **Win probability** |
| **15** | **Overextension flag** | **Consolidation trigger!** |

### Key Improvements

#### 1. Troops Per Tile (Feature 7) - CRITICAL!
```python
troops_per_tile = state.population / state.tiles_owned
features[7] = troops_per_tile / 50.0  # Normalize
```

**Why crucial:**
- Directly shows if agent is overextended
- Enables learning 15-35 optimal range
- Previously agent had to compute this from map channels!

#### 2. Territory Momentum (Feature 8)
```python
territory_momentum = state.territory_pct - prev.territory_pct
features[8] = territory_momentum * 100
```

**Why crucial:**
- Shows if agent is winning or losing
- Enables reactive consolidation ("I'm losing territory, stop expanding!")
- Velocity signal for strategic decisions

#### 3. Overextension Flag (Feature 15) - NEW!
```python
if territory_pct > 0.20 and troops_per_tile < 15:
    features[15] = (15 - troops_per_tile) / 15.0  # 0.0-1.0
```

**Why crucial:**
- Explicit binary signal: "You are overextended!"
- Directly aligns with overextension penalty reward
- Makes learning consolidation much easier

#### 4. Multi-Front Indicator (Feature 13)
```python
unique_fronts = len(set(recent_attack_directions[-5:]))
features[13] = unique_fronts / 8.0
```

**Why crucial:**
- Shows if fighting multiple wars
- Aligns with multi-front penalty reward
- Enables learning "focus fire" strategy

#### 5. Attack Intensity & Rank Percentile (12, 14)
- Feature 12: How aggressive agent has been recently
- Feature 14: Win probability based on rank (1.0=winning, 0.0=losing)

**Why crucial:**
- Self-awareness of play style
- Can adapt aggression to position
- "If I'm winning (0.9), hold position; if losing (0.3), take risks"

---

## Impact on Learning

### Old State (4-5 unused features)

**Agent had to infer:**
- ❌ Troops/tile from map channels (hard!)
- ❌ Overextension from multiple signals (complex!)
- ❌ Multi-front wars from implicit patterns (difficult!)

**Result:** Could learn basic expansion but struggled with nuanced strategy

### New State (all 16 features meaningful)

**Agent now sees directly:**
- ✅ "I have 12 troops/tile" (feature 7)
- ✅ "I'm overextended!" (feature 15 = 0.8)
- ✅ "I'm fighting on 4 fronts" (feature 13 = 0.5)
- ✅ "I'm losing territory fast" (feature 8 = -0.03)
- ✅ "I'm in first place" (feature 14 = 1.0)

**Result:** Should learn consolidation strategy much faster!

---

## Training Recommendations

### Option 1: Current Setup (Recommended First)
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 500000 \
  --no-curriculum \
  --num-bots 5
```

**Pros:**
- Test new rewards + new state together
- Quick iteration (~45 min)
- 518K params might be enough now

**Cons:**
- If still fails, we'll need model improvements

### Option 2: If 500k Shows Promise
```bash
# Full training
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 2000000 \
  --no-curriculum \
  --num-bots 5
```

**Expected improvement:**
- Agent should learn consolidation faster (explicit overextension flag)
- Should understand troops/tile directly (feature 7)
- Should learn multi-front penalty easier (feature 13)

### Option 3: If Still 0% Wins After 2M

**Then we need model improvements:**

1. **Increase capacity to 1-2M parameters**
   - Larger fusion layers (256 → 512)
   - More CNN channels (32→64→128 → 64→128→256)

2. **Add recurrent memory (LSTM)**
   - Remember past 10-20 timesteps
   - Learn temporal patterns ("I expanded, now consolidate")

3. **Larger cross-attention**
   - Better map-global fusion
   - More nuanced strategic understanding

---

## Expected Results with Improvements

### Before (Old rewards + Old state)
```
Steps 0-2400:   Expand to 45% (Rank 1)
Steps 2400-4375: Collapse to 0% (eliminated)
Win rate:        0%
```

### After (New rewards + New state)
```
Steps 0-1000:   Expand to 20-25%
Steps 1000-1500: CONSOLIDATE (see overextension flag!)
Steps 1500-3000: Expand to 40% when troops rebuilt
Steps 3000-4000: Hold position (see rank=1, territory=40%)
Steps 4000-6000: Push to 50-60% when strong
Result:          Should see >0% win rate
```

---

## Summary

### State Space
- **Before:** 4-5 unused features, agent had to infer key metrics
- **After:** All 16 features meaningful, explicit strategic signals
- **Improvement:** Agent should learn consolidation **much faster**

### Model Capacity
- **518K params:** Probably adequate for basic strategy
- **Evidence:** Agent learned complex expansion (0→45%)
- **Limitation:** Might struggle with long-term planning (no memory)
- **Verdict:** Try training first, upgrade to 1-2M if needed

### Recommendation
**Train 500k with new rewards + new state, then evaluate:**
- If win rate >0%: Success! Continue to 2M
- If still 0% but better survival: Increase to 2M
- If no improvement: Need larger model (1-2M params + LSTM)

### Most Likely Outcome
With explicit overextension flag (feature 15) + troops/tile (feature 7), agent should learn consolidation **significantly faster** than before. The reward structure now has direct observational support!
