# Phase 3 - Current Implementation State

**Date:** November 3, 2025
**Status:** Training infrastructure complete, needs strategic guidance improvements

---

## Overview

Phase 3 implements a reinforcement learning agent for OpenFront.io battle royale using:
- **Algorithm:** PPO (Proximal Policy Optimization)
- **Architecture:** CNN + MLP with attention mechanisms + frame stacking
- **Objective:** Survive longest and win 1v50 battle royale
- **Framework:** Stable-Baselines3 + Gymnasium

---

## 1. Environment (`src/environment.py`)

### Observation Space

**Multi-modal input (Dict space):**

#### Map Observation: `[128, 128, 20]`
- **Size:** 128×128 grid (downsampled from 512×512)
- **Channels (5 per frame × 4 frames = 20 total):**
  1. **Own territory** (1.0 = owned, 0.0 = not owned)
  2. **Enemy territory** (1.0 = enemy, 0.0 = not enemy)
  3. **Troop density** (normalized troops per tile)
  4. **Border regions** (1.0 = border, 0.0 = interior)
  5. **Cities/resources** (1.0 = city, 0.0 = empty)
- **Frame stacking:** Last 4 frames stacked → temporal context

#### Global Features: `[64]` (16 features × 4 frames)

Per-frame features (16):
0. Population / max_population
1. Max population / 100000
2. Population growth rate
3. Territory percentage
4. Territory change (momentum)
5. Rank / 50
6. Border pressure / 10
7. **Troops per tile ratio** (density - critical for consolidation)
8. Territory momentum (expansion/contraction rate)
9. Time alive / max_time
10. Game progress (0-1)
11. Nearest threat / 128
12. Recent attack intensity
13. Multi-front indicator (number of active fronts)
14. Rank position (percentile, 1.0 = winning)
15. **Overextension flag** (0.0-1.0, higher = worse)

**Total observation:** 327,680 + 64 = 327,744 values per observation

---

### Action Space

**Discrete: 45 actions** (9 directions × 5 intensities)

**Directions (9):**
- 0: HOLD (no expansion)
- 1-8: Expand in 8 cardinal/diagonal directions

**Intensities (5):**
- 0: Very weak (10% troops)
- 1: Weak (25% troops)
- 2: Medium (50% troops)
- 3: Strong (75% troops)
- 4: Very strong (90% troops)

**Action mapping:** `action = direction * 5 + intensity`

---

### Reward Structure (Current)

**Simple logarithmic survival rewards:**

```python
def _compute_reward(self):
    reward = 0.0

    # 1. LOGARITHMIC SURVIVAL (every step, rank-based)
    #    Exponentially increasing rewards for late-game survival
    if rank and total_players:
        rank_percentile = 1.0 - (rank / total_players)

        # Logarithmic multiplier (increases with time)
        if step_count < 1000:
            multiplier = 1.0   # Early game
        elif step_count < 2500:
            multiplier = 2.0   # Mid game (2x)
        elif step_count < 5000:
            multiplier = 4.0   # Late game (4x)
        else:
            multiplier = 8.0   # End game (8x!)

        reward += rank_percentile * multiplier

    # 2. TERMINAL (win bonus only)
    if territory_pct >= 0.80:
        reward += 10000  # Victory!
    # NO LOSS PENALTY (removed - constant noise at 0% win rate)

    # 3. TIMEOUT
    if step_count >= 10000:
        reward += -5000

    return reward
```

**Example rewards (Rank 1/6 = 83.3 percentile):**
- Step 500: +0.83/step
- Step 1500: +1.67/step (2x)
- Step 3000: +3.33/step (4x)
- Step 6000: +6.67/step (8x)

**Cumulative if maintain Rank 1 for 5000 steps:**
- 0-1000: +830
- 1000-2500: +2,505
- 2500-5000: +8,325
- **Total: ~11,660** (comparable to win bonus!)

---

### Episode Termination

**Done when:**
1. Agent eliminated (all territory lost)
2. Agent wins (≥80% territory)
3. Timeout (10,000 steps)

---

## 2. Model Architecture (`src/model_attention.py`)

### BattleRoyaleExtractorWithAttention

**Total parameters: 590,257 (within 600K budget)**

#### CNN Branch (EfficientCNN)
```
Input: [B, 20, 128, 128]  ← 4 frames × 5 channels
  ↓
Conv1: 20 → 32 channels (8×8, stride 4)  → [B, 32, 32, 32]
  + BatchNorm + ReLU + Spatial Attention
  ↓
Conv2: 32 → 64 channels (4×4, stride 4)  → [B, 64, 8, 8]
  + BatchNorm + ReLU + Spatial Attention
  ↓
Conv3: 64 → 128 channels (4×4, stride 2) → [B, 128, 4, 4]
  + BatchNorm + ReLU + Spatial Attention
  ↓
Global Average Pooling → [B, 128]
  ↓
FC: 128 → 256 features
```

**Parameters:** ~270K (spatial attention included)

#### MLP Branch
```
Input: [B, 64]  ← 4 frames × 16 features
  ↓
FC1: 64 → 256
  + ReLU
  ↓
FC2: 256 → 128
  + ReLU
  ↓
FC3: 128 → 128
  + ReLU
```

**Parameters:** ~50K

#### Cross-Attention Fusion
```
Q = map_features (256)
K, V = global_features (128)
  ↓
Attention → 128 features
```

**Parameters:** ~50K

#### Final Fusion
```
Concat[map(256), global(128), cross_attn(128)] → 512
  ↓
FC: 512 → 256
  + ReLU + Dropout(0.1)
```

**Parameters:** ~130K

#### Actor-Critic Heads (in PPO policy)
```
Actor:  256 → 128 → 45 (actions)
Critic: 256 → 128 → 1  (value)
```

**Parameters:** ~90K

---

### Key Features

**1. Spatial Attention:**
- Focuses on borders, cities, threats
- Applied after each conv layer
- Learns what map regions matter

**2. Cross-Attention:**
- Links map features with global stats
- "Given my rank, where should I attack?"
- "Which border is most important?"

**3. Frame Stacking:**
- 4 frames of history
- Temporal context without LSTM
- Agent sees recent patterns

**4. Global Average Pooling:**
- Reduces CNN params from 6.5M → 270K
- Efficient yet powerful

---

## 3. Training Setup (`src/train_attention.py`)

### PPO Hyperparameters

```python
PPO(
    policy="MultiInputPolicy",
    learning_rate=1e-4,      # REDUCED for stability (was 3e-4)
    n_steps=1024,            # Steps per env before update
    batch_size=128,          # Minibatch size
    n_epochs=10,             # Gradient updates per rollout
    gamma=0.995,             # Discount factor (long episodes)
    gae_lambda=0.95,         # GAE parameter
    clip_range=0.2,          # PPO clipping
    ent_coef=0.005,          # REDUCED entropy (was 0.01, 0.05)
    vf_coef=0.5,             # Value loss coefficient
    max_grad_norm=0.5,       # Gradient clipping
    device='mps',            # Apple Silicon GPU
)
```

### Training Configuration

**Parallel environments:** 12 (SubprocVecEnv)
**Curriculum learning:** Disabled (train vs 5 bots directly)
**Total timesteps:** 2,000,000 (typical run)
**Checkpoint frequency:** Every 50,000 steps
**Platform:** macOS Apple Silicon (MPS)

### Why These Hyperparameters?

**Low learning rate (1e-4):**
- Prevents overshooting good policies
- More stable learning
- Slower but more reliable

**Low entropy (0.005):**
- Minimizes random exploration
- Agent sticks with discovered strategies
- Better for long-term strategic consistency

**High gamma (0.995):**
- Values future rewards highly
- Essential for 2000-7000 step episodes
- Encourages long-term planning

---

## 4. Callbacks

### CheckpointCallback
- Saves model every 50,000 steps
- Location: `runs/*/checkpoints/*/phase_name_model_STEPS_steps.zip`
- Enables rollback to any training point

### DetailedLoggingCallback (`src/training_callback.py`)
Logs every 10 episodes:
- Win/loss counts and rates
- Avg/best reward, length, tiles, troops, territory, rank
- Recent trends
- Performance summary

### SaveBestModelCallback (`src/best_model_callback.py`)
**Current version: Tracks MAXIMUM episode length**
- Saves model when agent survives LONGER than ever before
- Location: `runs/*/checkpoints/*/best_model.zip`
- Captures breakthrough policies immediately

```python
if episode_length > best_episode_length:
    save_model()  # Saves longest survival run!
```

---

## 5. File Structure

```
phase3-implementation/
├── src/
│   ├── environment.py                    # Gymnasium env (rewards, obs, actions)
│   ├── environment_complex_rewards.py    # BACKUP: 15-component rewards
│   ├── model_attention.py                # CNN + Attention architecture
│   ├── model_lstm_attention.py           # LSTM version (not used - MPS crash)
│   ├── train_attention.py                # Training script (frame stacking)
│   ├── train_lstm.py                     # LSTM training (not used - MPS issue)
│   ├── training_callback.py              # Detailed logging
│   └── best_model_callback.py            # Best model tracking
│
├── runs/                                  # Training runs
│   └── run_TIMESTAMP/
│       ├── checkpoints/                   # Model checkpoints
│       │   └── phase_name/
│       │       ├── best_model.zip         # Best by episode length
│       │       └── *_steps.zip            # Regular checkpoints
│       └── logs/                          # TensorBoard logs
│
├── PHASE3_CURRENT_STATE.md               # This file
├── TRAINING_READY.md                     # Logarithmic rewards doc
├── FINAL_SETUP_SUMMARY.md                # Frame stacking doc
└── (other docs...)
```

---

## 6. Training Results (Last 2M Run)

### Final Statistics:
- **Total episodes:** 769
- **Win rate:** 0.0%
- **Average reward:** +131.2
- **Average survival:** 2,586 steps
- **Best reward:** +9,373.3
- **Longest run:** 7,172 steps

### Analysis:

**✅ Positive:**
- Agent CAN learn long survival (7,172 steps - 2.8x average!)
- Training is stable (no crashes, consistent performance)
- Architecture works (590K params, runs on MPS)

**❌ Problems:**
1. **Inconsistent:** Only 1 great run in 769 episodes
2. **No wins:** 0% win rate after 2M steps
3. **Low average reward:** +131 suggests agent ranks last most games
4. **Poor rank:** Average rank ~5/6 (near elimination)

**🤔 Root cause:**
- Pure survival rewards don't teach strategy
- Agent knows "survive = good" but not HOW to survive
- Needs guidance on territory control, consolidation, troop management

---

## 7. What Works

✅ **Training Infrastructure:**
- Parallel environments (12 envs on MPS)
- Stable training (no crashes)
- Good logging and checkpointing
- Best model tracking (now by episode length)

✅ **Model Architecture:**
- 590K parameters (efficient)
- Attention mechanisms (spatial + cross-attention)
- Frame stacking (4 frames temporal context)
- Trains fast on MPS (~3 hours for 2M steps)

✅ **Observation Space:**
- Rich state representation (map + global features)
- Includes consolidation signals (troops_per_tile, overextension_flag)
- Temporal context via frame stacking

✅ **Action Space:**
- Flexible (9 directions × 5 intensities)
- Allows hold/consolidate (action 0)

---

## 8. What Doesn't Work

❌ **Reward Structure:**
- Too simple (only survival + rank)
- Doesn't teach strategic behaviors
- Agent optimizes for "don't die immediately" instead of "win"
- No signal for territory holding, consolidation, troop management

❌ **Learning Consistency:**
- Breakthroughs are rare and random
- Can't consistently execute discovered strategies
- Policy regresses after finding good strategies

❌ **Strategic Understanding:**
- Doesn't learn when to expand vs consolidate
- Doesn't understand troop density importance
- Doesn't manage multi-front conflicts

❌ **LSTM Option:**
- Would provide better temporal memory
- But crashes on MPS (PyTorch/Metal bug)
- Would require CPU training (slower)

---

## 9. Available But Not Active

### Complex Rewards (Backed Up)

`src/environment_complex_rewards.py` contains 15-component rewards:
1. Territory change (+/- expansion)
2. Action bonuses (hold/consolidate)
3. Density rewards (maintain troops/tile)
4. Overextension penalty (>40% territory with <15 troops/tile)
5. Troop loss penalty
6. Enemy kill bonus
7. Military strength
8. Focus/multi-front management
9. Survival rewards
10. Rank improvement/defense
11. Defensive waiting
12. Territory milestones
13. Time penalties
14. Terminal rewards
15. Shaping bonuses

**Status:** Tried without frame stacking (+14,761 avg reward, 0% wins)
**Potential:** Might work WITH frame stacking (not tested yet)

### LSTM Architecture

`src/model_lstm_attention.py` + `src/train_lstm.py`:
- RecurrentPPO with 256-unit LSTM
- Long-term temporal memory (100+ steps)
- ~800K parameters

**Status:** Crashes on MPS backend (PyTorch bug)
**Workaround:** Can train on CPU (slower but works)

---

## 10. Next Steps (Recommended)

### Option A: Add Territory Holding Reward (Quick - 1 hour)

Add ONE component to guide agent:
```python
# Add after rank reward in environment.py
reward += state.territory_pct * 2.0
```

**Expected:** 5-15% win rate, better survival

### Option B: Complex Rewards + Frame Stacking (2 hours)

Use backed-up complex rewards with current frame stacking:
```bash
cp src/environment_complex_rewards.py src/environment.py
```

**Rationale:** Complex rewards failed before, but that was WITHOUT temporal context

### Option C: LSTM on CPU (Overnight)

Train RecurrentPPO with LSTM on CPU:
```bash
python3 src/train_lstm.py --device cpu --n-envs 8 --total-timesteps 1000000
```

**Expected:** Better temporal planning, more consistent strategies

### Option D: Reduce Difficulty

Train vs 2-3 bots first, then curriculum to 5:
```bash
python3 src/train_attention.py --device mps --n-envs 12 --num-bots 2 --total-timesteps 500000
```

**Expected:** Faster learning, build confidence before scaling

---

## 11. Key Insights from Development

### What We Learned:

1. **Simple isn't always better:** Pure survival rewards are too sparse to teach strategy
2. **Temporal context matters:** Frame stacking helped but might not be enough
3. **Breakthrough vs consistency:** Agent can find good strategies but can't execute consistently
4. **Reward-objective alignment critical:** Low average reward despite surviving shows misalignment
5. **Best model tracking crucial:** Mean over 100 episodes missed breakthrough policies

### Design Decisions:

1. **Frame stacking over LSTM:** Faster training, works on MPS
2. **Low entropy:** Strategic consistency > exploration at this stage
3. **No loss penalty:** Constant negative signal at 0% win rate is noise
4. **Logarithmic survival:** Late-game exponentially more valuable
5. **Best by episode length:** More direct than reward for battle royale

---

## 12. Technical Specifications

**Hardware:** Apple Silicon (M-series) with Metal Performance Shaders
**Python:** 3.13
**Key Dependencies:**
- gymnasium
- stable-baselines3
- sb3-contrib (for RecurrentPPO - not actively used)
- torch (with MPS support)
- numpy

**Training Performance:**
- 12 parallel environments
- ~300 FPS
- 2M steps in ~3 hours on MPS
- ~45 minutes for 500K steps

**Model Size:** 31MB per checkpoint (590K params × 4 bytes/float32)

---

## Summary

Phase 3 has a **solid technical foundation** but needs **strategic guidance improvements**. The agent can survive long occasionally (7,172 steps) but can't do it consistently. The reward structure is too simple to teach complex battle royale strategies like when to expand vs consolidate.

**Recommended next action:** Add territory holding reward (simplest improvement with high success probability).
