# Phase 2 Improvements - Neighbor Troops Observation + Military Strength

## Problem Identified

The Phase 2 agent was learning to expand aggressively in all directions but **spreading itself too thin**:
- Gained many tiles quickly (+50 reward per tile)
- Failed to maintain sufficient troop density
- Got overwhelmed by counter-attacks from multiple opponents
- Lost battles due to weak military strength
- **Could not see which neighbors were dangerous**

## Solution: Two-Pronged Approach

### 1. Neighbor Troops Observation (PRIMARY)
Added enemy troop information directly to the observation space so the agent can **learn to recognize threats**.

### 2. Relative Military Strength Reward (SECONDARY)
Added reward bonus for maintaining strong army relative to enemies.

### Why This Approach?

**✅ Advantages:**
- No magic numbers or arbitrary thresholds to tune
- Naturally adapts to game dynamics
- Agent learns: "Am I stronger than my opponents?"
- Works across different player counts and map sizes

**❌ Rejected alternatives:**
- Option 1 (Fixed troop density threshold): Requires guessing magic numbers
- Option 2 (Penalty for overextension): Negative reinforcement less effective
- Option 4 (Reduce tile reward only): Doesn't actively encourage military strength

## Implementation Details

### 1. Observation Space (`rl_env/openfrontio_env.py`)

**Added neighbor_troops to observation:**

```python
self.observation_space = spaces.Dict({
    'features': spaces.Box(shape=(5,)),     # Global state
    'action_mask': spaces.Box(shape=(9,)), # Valid actions
    'neighbor_troops': spaces.Box(shape=(8,))  # NEW: Troops of each neighbor!
})
```

**Extraction logic:**

```python
# Extract neighbor troops (aligned with action space 1-8)
neighbor_troops = np.zeros(8, dtype=np.float32)
for i, neighbor in enumerate(neighbors[:8]):
    # Normalize enemy troops (0.0-1.0)
    neighbor_troops[i] = min(neighbor.get('enemy_troops', 0) / 100000.0, 1.0)
```

**What the agent sees:**
- `neighbor_troops[0]` = troops of neighbor at action 1
- `neighbor_troops[7]` = troops of neighbor at action 8
- Values normalized to [0.0, 1.0]
- **Agent can now learn: "This neighbor has way more troops than me, don't attack!"**

### 2. Game Bridge (`game_bridge/game_bridge_cached.ts`)

**Added enemy troops tracking:**

```typescript
interface GameState {
  // ... existing fields
  enemy_troops: number;  // NEW: Total troops of all enemy players
  // ...
}

// In getState() method:
const enemyTroops = this.aiPlayers.reduce((sum, ai) => sum + ai.troops(), 0);
```

### 2. Environment (`rl_env/openfrontio_env.py`)

**Added military strength bonus to reward calculation:**

```python
# 4. MILITARY STRENGTH BONUS (Phase 2 multi-player)
#    Reward for maintaining strong army relative to enemies
if self.reward_military_strength > 0:
    agent_troops = state_after.get('troops', 0)
    enemy_troops = state_after.get('enemy_troops', 0)
    num_enemies = self.num_players - 1

    # Reward if agent has more troops than average enemy
    if num_enemies > 0 and enemy_troops > 0:
        avg_enemy_troops = enemy_troops / num_enemies
        if agent_troops > avg_enemy_troops:
            reward += self.reward_military_strength  # +1.0 per step
```

### 3. Phase 2 Config (`configs/phase2_config.json`)

**Updated reward structure:**

```json
{
  "reward": {
    "per_tile_change": 50,           // Reduced from 100 (prevent overextension)
    "per_step": -0.05,               // Reduced penalty for longer episodes
    "action_bonus": 0.5,             // Keep exploration bonus
    "enemy_kill_bonus": 8000,        // Increased from 5000 (more opponents)
    "military_strength_bonus": 1.0,  // NEW: +1.0 when stronger than avg enemy
    "win_bonus": 15000,              // Increased from 10000 (harder scenario)
    "loss_penalty": -10000,
    "timeout_penalty": -7500         // Increased from -5000
  }
}
```

**Updated game parameters:**

```json
{
  "game": {
    "num_players": 8,        // Increased from 5
    "max_ticks": 1000        // Increased from 500
  },
  "environment": {
    "max_steps": 10000       // Increased from 5000
  },
  "training": {
    "total_timesteps": 500000,  // Increased from 200000
    "n_steps": 10000,           // Matches max_steps
    "batch_size": 2000          // Increased from 500
  }
}
```

## Reward Structure Comparison

### Phase 1 (2 players, 1v1):
- Tile change: **±100** per tile
- Action bonus: **+0.5**
- Enemy kill: **+5000**
- Time penalty: **-0.1** per step
- Win: **+10,000**

### Phase 2 (8 players, multi-agent):
- Tile change: **±50** per tile (reduced to prevent overextension)
- Action bonus: **+0.5** (unchanged)
- Enemy kill: **+8000** (increased, more opponents)
- **Military strength: +1.0** per step (NEW!)
- Time penalty: **-0.05** per step (reduced for longer episodes)
- Win: **+15,000** (increased, harder to win)

## Expected Agent Behavior

**Before (without neighbor observation + military strength):**
1. Expand rapidly in all directions (+50 per tile)
2. Spread troops thin across territory
3. Blindly attack all neighbors (can't see they're strong)
4. Get counter-attacked by stronger neighbors
5. Lose battles due to weak defenses
6. Get eliminated

**After (with neighbor observation + military strength):**
1. **SEE neighbor troops** in observation space
2. **LEARN to avoid** attacking strong neighbors
3. **LEARN to target** weak neighbors
4. Balance territory growth with army building
5. Maintain military strength (+1.0 reward/step)
6. Defend successfully against counter-attacks
7. Eliminate weaker opponents strategically
8. Win through smart target selection + military superiority

**Key Learned Behaviors:**
- "This neighbor has 0.8 (80k troops), I only have 0.01 (1k) → don't attack action 3"
- "This neighbor has 0.05 (5k troops), I have 0.15 (15k) → good target for action 5"
- "I'm weaker than average → focus on building troops, not expanding"
- "I'm stronger than average → safe to expand"

## Training Impact

**Key insight:** The agent now gets **+1.0 reward per step** when `agent_troops > avg(enemy_troops)`.

Over a 10,000-step episode where agent maintains military superiority:
- Military strength bonus: **+10,000** total
- This is comparable to tile rewards and terminal rewards
- Creates strong incentive to build and maintain strong army

**Balance of incentives:**
- Short-term: Tile expansion still rewarded (+50 each)
- Medium-term: Military strength rewarded continuously (+1.0/step)
- Long-term: Eliminating enemies (+8000) and winning (+15000)

## Testing Recommendations

1. **Monitor training metrics:**
   - Average troops per episode
   - Military strength bonus frequency
   - Win rate in 8-player scenarios
   - Episode length (should be longer with better survival)

2. **Check for new behaviors:**
   - Does agent sometimes skip attacks to build troops?
   - Does agent maintain higher troop density?
   - Does agent survive longer before elimination?
   - Does agent win more consistently?

3. **Potential tuning:**
   - If agent becomes too passive: Reduce military_strength_bonus to 0.5
   - If agent still overextends: Reduce per_tile_change to 30-40
   - If games too long: Increase time penalty to -0.1

## Files Modified

1. `game_bridge/game_bridge_cached.ts` - Added enemy_troops tracking
2. `rl_env/openfrontio_env.py` - Added military strength reward logic
3. `configs/phase2_config.json` - Updated all parameters for 8-player scenarios
4. `visualize_game.py` - Already supports dynamic player counts

## Next Steps

1. Train a new model with Phase 2 config: `python3 train.py --config configs/phase2_config.json`
2. Monitor TensorBoard for military strength impact
3. Visualize episodes to verify troop management behavior
4. Compare Phase 2 performance to Phase 1 baseline
