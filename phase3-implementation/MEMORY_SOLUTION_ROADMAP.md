# Memory & Planning Solution Roadmap

**Date:** November 1, 2025
**Question:** Do we need LSTM/memory for agent to learn consolidation?

---

## Problem Statement

**Current architecture:** Single-step Markov (no memory)
- Observation(t) → Action(t)
- No memory of past actions
- No multi-step planning
- Each decision independent

**Observed failure:**
- Agent expands continuously (0→45%)
- Never pauses to consolidate
- Collapses when overextended

**Question:** Is this a memory problem or reward/observability problem?

---

## Root Cause Analysis

### Evidence Memory Might NOT Be the Issue

1. **Agent demonstrated sequential learning:**
   - Expanded from 0% → 45% over 2400 steps (coherent strategy)
   - Maintained Rank 1 (consistent performance)
   - Made directional attacks (not random)

2. **We just fixed observability:**
   - Added troops/tile feature (explicit overextension signal)
   - Added overextension flag (binary warning)
   - Added territory momentum (expansion velocity)

3. **We just fixed rewards:**
   - Overextension penalty (-666 at 45% with thin troops)
   - Rank defense bonus (+5 hold, -10 lose when winning)
   - Stronger density rewards (+5.0 for optimal)

**Hypothesis:** Agent learned sequential strategy (expansion), just learned WRONG one because:
- ❌ Rewards didn't incentivize consolidation (NOW FIXED)
- ❌ Couldn't observe overextension directly (NOW FIXED)
- ⚠️ Might lack memory (STILL UNKNOWN)

---

## Staged Solution Approach

### Stage 1: Test Current Setup (PRIORITY)

**Action:** Train 500k-2M with new rewards + new features
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 500000 \
  --no-curriculum \
  --num-bots 5
```

**Success criteria:**
- ✅ Win rate >0% (was 0%)
- ✅ Survives >5000 steps (was ~4000)
- ✅ Shows consolidation behavior (pauses expansion when overextended)
- ✅ Holds territory >500 steps (was immediate collapse)

**If successful:** Memory might not be needed! Explicit features + rewards sufficient.

**If fails:** Proceed to Stage 2

**Time investment:** 45 min - 3 hours

---

### Stage 2: Add Frame Stacking (IF NEEDED)

**Easiest memory solution - try this BEFORE LSTM**

#### Implementation

```python
# In environment.py

class OpenFrontEnv(gym.Env):
    def __init__(self, ..., frame_stack: int = 4):
        self.frame_stack = frame_stack
        self.frame_buffer = deque(maxlen=frame_stack)

        # Update observation space
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 5 * frame_stack), dtype=np.float32),  # 20 channels
            'global': spaces.Box(-np.inf, np.inf, (16 * frame_stack,), dtype=np.float32)  # 64 features
        })

    def reset(self, ...):
        obs, info = ...
        # Fill buffer with initial observation
        for _ in range(self.frame_stack):
            self.frame_buffer.append(obs)
        return self._stack_frames(), info

    def step(self, action):
        obs, reward, terminated, truncated, info = ...
        self.frame_buffer.append(obs)
        return self._stack_frames(), reward, terminated, truncated, info

    def _stack_frames(self):
        # Stack last 4 observations
        stacked_map = np.concatenate([f['map'] for f in self.frame_buffer], axis=2)  # [128,128,20]
        stacked_global = np.concatenate([f['global'] for f in self.frame_buffer])  # [64]
        return {'map': stacked_map, 'global': stacked_global}
```

#### Architecture Changes

**CNN needs to accept more channels:**
```python
# OLD:
self.conv1 = nn.Conv2d(5, 32, kernel_size=8, ...)  # 5 channels

# NEW:
self.conv1 = nn.Conv2d(20, 32, kernel_size=8, ...)  # 20 channels (4 frames × 5)
```

**MLP needs more inputs:**
```python
# OLD:
self.mlp = nn.Linear(16, 128)  # 16 features

# NEW:
self.mlp = nn.Linear(64, 128)  # 64 features (4 frames × 16)
```

#### Expected Behavior

Agent can now see:
- **Frame t:** Territory = 40%, troops/tile = 15
- **Frame t-1:** Territory = 38%, troops/tile = 16
- **Frame t-2:** Territory = 36%, troops/tile = 17
- **Frame t-3:** Territory = 34%, troops/tile = 18

**Pattern visible:** "Territory increasing, density decreasing → overextending!"

#### Pros & Cons

**Pros:**
- ✅ Very easy (30 lines of code)
- ✅ No new architecture (just wider inputs)
- ✅ Works with PPO out-of-box
- ✅ Fast (no sequential processing)

**Cons:**
- ❌ 4x memory usage
- ❌ Limited history (only 4 steps)
- ❌ Dumb concatenation (no learned memory)
- ❌ CNN must process 4x more channels

**Params impact:**
- Conv1: 5→20 channels input: +6K params
- MLP: 16→64 input: +6K params
- **Total: +12K params** (negligible)

**Time investment:** 1-2 hours implementation + 3 hours training

---

### Stage 3: Add LSTM (IF FRAME STACKING FAILS)

**More powerful but harder to implement**

#### Architecture

```python
class BattleRoyaleExtractorWithLSTM(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=256):
        super().__init__(observation_space, features_dim)

        # Same CNN and MLP as before
        self.cnn = EfficientCNN(...)
        self.mlp = nn.Sequential(...)
        self.cross_attn = CrossAttentionFusion(...)
        self.fusion = nn.Sequential(...)  # Output: 256 features

        # NEW: LSTM layer
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=256,
            num_layers=1,
            batch_first=True
        )

        # Hidden state storage (per environment)
        self.hidden_states = {}  # env_id -> (h, c)

    def forward(self, observations):
        batch_size = observations['map'].shape[0]

        # Process through CNN+MLP+Fusion (same as before)
        map_feat = self.cnn(observations['map'])
        global_feat = self.mlp(observations['global'])
        cross_feat = self.cross_attn(map_feat, global_feat)
        fused = self.fusion(torch.cat([map_feat, global_feat, cross_feat], dim=1))  # [B, 256]

        # LSTM forward
        # Need to manage hidden states per environment
        lstm_out, new_hidden = self.lstm(
            fused.unsqueeze(1),  # [B, 1, 256] (sequence length = 1)
            self._get_hidden_states(batch_size)
        )

        # Update hidden states
        self._update_hidden_states(new_hidden)

        return lstm_out.squeeze(1)  # [B, 256]

    def _get_hidden_states(self, batch_size):
        # Retrieve or initialize LSTM hidden states
        # Complex: need to track which environment is which
        ...

    def reset_hidden_states(self, env_ids):
        # Reset LSTM state when episode ends
        ...
```

#### Challenges

1. **State management:** Must track LSTM hidden state per parallel environment
2. **Reset logic:** Clear hidden state when episode ends
3. **Gradient flow:** LSTMs can have vanishing gradients
4. **Debugging:** Harder to visualize what LSTM learns

#### Params Impact

```python
LSTM(256, 256, 1 layer):
  - Input gate:  256 × 256 = 65K
  - Forget gate: 256 × 256 = 65K
  - Cell gate:   256 × 256 = 65K
  - Output gate: 256 × 256 = 65K
  Total: ~260K params

New total: 518K + 260K = 778K params
```

#### Expected Behavior

LSTM learns to remember:
- "I've been expanding for 50 steps → consolidate soon"
- "My territory peaked 100 steps ago → in decline phase"
- "I've been attacking north for 20 steps → committed to that front"

**Time investment:** 1-2 days implementation + debugging + training

---

### Stage 4: Transformer (RESEARCH LEVEL)

**Only if LSTM insufficient - not recommended for initial attempt**

Skip this unless Stages 1-3 all fail.

---

## Decision Tree

```
START
  ↓
[Stage 1] Train with new rewards + new features (500k-2M)
  ↓
  ├─ Win rate >0%, consolidation visible?
  │    ↓ YES
  │    ✅ SUCCESS! Memory not needed, explicit features sufficient
  │
  └─ Still 0% wins, no consolidation?
       ↓ NO
       [Stage 2] Add frame stacking (4 frames)
         ↓
         ├─ Win rate >0%, sees temporal patterns?
         │    ↓ YES
         │    ✅ SUCCESS! Simple memory sufficient
         │
         └─ Still 0% wins?
              ↓ NO
              [Stage 3] Add LSTM (256 hidden)
                ↓
                ├─ Win rate >0%?
                │    ↓ YES
                │    ✅ SUCCESS! Learned memory working
                │
                └─ Still 0% wins?
                     ↓ NO
                     [Stage 4] Problem is elsewhere (larger model, different algorithm, etc.)
```

---

## Recommendation

### PRIORITY: Stage 1 (Current Setup)

**Rationale:**
1. We just made HUGE changes (5 new features + 6 reward improvements)
2. Agent demonstrated sequential learning (just learned wrong strategy)
3. Explicit features might be enough (overextension flag, troops/tile, etc.)
4. Test hypothesis: "Failure was reward/observability, not memory"

**Action:**
```bash
python src/train_attention.py \
  --device mps \
  --n-envs 12 \
  --total-timesteps 500000 \
  --no-curriculum \
  --num-bots 5
```

**Watch for:**
- Does agent pause expansion when overextension flag triggers?
- Does agent respond to density rewards?
- Does collapse pattern disappear?

**If Stage 1 succeeds:** We saved 1-2 weeks of LSTM implementation!

**If Stage 1 fails:** We have clear evidence memory is needed, proceed to Stage 2 (frame stacking)

---

## Technical Note: Why Explicit Features Might Be Enough

**Classic RL theory:** Need memory for partially observable environments

**Our case:**
- ✅ Full observability of current state (map + global)
- ✅ Overextension is computable from current state alone
- ✅ Optimal action (consolidate) determinable from current density

**Memory needed for:**
- ❌ Hidden enemy movements (not applicable - we see enemy troops)
- ❌ Long-term commitments (maybe - "I attacked north, keep going")
- ❌ Phase recognition (maybe - but we added momentum/intensity features)

**Counter-argument:**
- Agent needs to learn "expand → consolidate → expand" cycle
- This is temporal pattern, might need memory
- BUT: Cycle can be triggered by explicit state (overextension flag!)

**Verdict:** Memory MIGHT help, but not obviously required. Test explicit features first.

---

## Summary

| Stage | Solution | Effort | Params | When to Use |
|-------|----------|--------|--------|-------------|
| **1** | Current (new rewards + features) | None | 518K | **START HERE** |
| **2** | Frame stacking (4 frames) | Low | 530K | If Stage 1 fails |
| **3** | LSTM (hidden=256) | High | 778K | If Stage 2 fails |
| **4** | Transformer | Very High | 1M+ | Research only |

**PRIORITY:** Test Stage 1 first. Strong hypothesis that explicit features + rewards solve the problem without memory.

**Time to first answer:** 45 min (500k training)
