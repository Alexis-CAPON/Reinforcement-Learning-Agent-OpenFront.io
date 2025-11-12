# Continuous Action Space Implementation

## Overview

Transitioned from discrete action space to **hybrid continuous action space** where the model learns both:
1. **Which neighbor to attack** (discrete)
2. **What percentage of troops to send** (continuous)

This gives the model full control over attack strategy and removes all artificial constraints.

## Motivation

### Problems with Fixed Attack Strategy

**Old approach**:
- Fixed trigger threshold: "Only attack when >70% of max troops"
- Fixed reserve ratio: "Always keep 25% in reserve"
- Fixed attack size: "Always send 50% of available troops"
- Result: Model couldn't learn optimal strategy, just which targets to pick

**Issues**:
1. Agent started with 24k troops but needed 70k to attack → long wait
2. Enemy expanded freely while agent waited for threshold
3. Model had no control over aggression level
4. Artificial constraints prevented learning

### New Approach: Learnable Everything

**Model now controls**:
- ✅ When to attack (by choosing target or IDLE)
- ✅ How aggressively to attack (percentage 0.0-1.0)
- ✅ Troop conservation strategy (learned through rewards)

**No artificial constraints**:
- ❌ No trigger threshold
- ❌ No reserve ratio
- ❌ No fixed attack percentages

## Action Space Design

### Type
```python
action_space = Dict({
    'attack_target': Discrete(9),           # 0=IDLE, 1-8=attack neighbors
    'attack_percentage': Box(0.0, 1.0, shape=(1,))  # % of troops to send
})
```

### Examples

**Conservative attack**:
```python
{
    'attack_target': 3,          # Attack neighbor 3
    'attack_percentage': [0.1]   # Send 10% of troops
}
```

**Aggressive attack**:
```python
{
    'attack_target': 5,          # Attack neighbor 5
    'attack_percentage': [0.8]   # Send 80% of troops
}
```

**No attack**:
```python
{
    'attack_target': 0,          # IDLE
    'attack_percentage': [0.0]   # Percentage ignored when IDLE
}
```

## Implementation Details

### Environment (openfrontio_env.py)

**Action parsing**:
```python
attack_target = int(action['attack_target'])
attack_percentage = float(action['attack_percentage'][0])  # Extract scalar

# Clip to valid range
attack_percentage = np.clip(attack_percentage, 0.0, 1.0)

# Execute if not IDLE and percentage > 1%
if attack_target > 0 and attack_percentage >= 0.01:
    self.game.attack_tile(
        player_id=1,
        tile_x=neighbor['tile_x'],
        tile_y=neighbor['tile_y'],
        attack_percentage=attack_percentage
    )
```

### Game Bridges (game_bridge_cached.ts, game_bridge_visual.ts)

**Attack execution** (NO constraints):
```typescript
attackTile(tile_x: number, tile_y: number, attack_percentage: number = 0.5) {
    const currentTroops = this.rlPlayer.troops();
    const attackTroops = Math.floor(currentTroops * attack_percentage);

    if (attackTroops < 1) {
        return;  // Only constraint: minimum 1 troop
    }

    this.game.addExecution(
        new AttackExecution(attackTroops, this.rlPlayer, targetId)
    );
}
```

**What was removed**:
```typescript
// ❌ REMOVED: Trigger threshold
// if (currentTroops < maxTroops * 0.7) return;

// ❌ REMOVED: Reserve ratio
// const reserve = maxTroops * 0.25;
// const availableToSend = currentTroops - reserve;

// ❌ REMOVED: Fixed attack size
// const attackTroops = Math.floor(availableToSend * 0.5);

// ✅ NEW: Model controls everything
const attackTroops = Math.floor(currentTroops * attack_percentage);
```

## Learning Dynamics

### How Model Learns Optimal Strategy

**Through dense rewards**:
```python
# Territorial control (main objective)
reward += state['tiles_owned'] * 2.0           # Reward for holding territory
reward -= state['enemy_tiles'] * 0.5           # Penalty for enemy expansion

# Tile changes (immediate feedback)
reward += tiles_gained * 50                    # Big reward for expansion
reward -= tiles_lost * 50                      # Big penalty for losses

# Troop management
reward += troop_increase * 0.01                # Reward for building army
```

**What the model should learn**:
1. **When troop count is low** → Choose IDLE or small percentage (0.1-0.2)
2. **When troop count is high** → Can afford larger attacks (0.3-0.6)
3. **When enemy is weak** → Aggressive attack (0.6-0.9)
4. **When enemy is strong** → Conservative or IDLE
5. **Balance expansion vs preservation** → Learn from reward feedback

### Expected Emergence

The model should naturally develop strategies like:
- **Early game**: Conservative expansion (10-20% troops per attack)
- **Mid game**: Aggressive expansion when strong (30-50% troops)
- **Late game**: All-in attacks when winning, or defensive when losing
- **Adaptation**: Different strategies vs different enemy behaviors

## Advantages

### 1. **True Reinforcement Learning**
- Model learns strategy from scratch through experience
- No human biases or assumptions baked in
- Can discover novel strategies

### 2. **Flexibility**
- Can adapt to different game situations
- Can learn different strategies for different maps
- Can counter different enemy behaviors

### 3. **Smooth Exploration**
- Continuous action space allows gradual adjustments
- PPO's continuous action policy naturally explores percentages
- No discrete jumps between attack sizes

### 4. **Realistic**
- Real commanders adjust force allocation continuously
- No artificial thresholds or constraints
- Natural troop management emerges from rewards

## Training Considerations

### Hyperparameters

No changes needed to PPO hyperparameters - PPO handles continuous actions natively:
```json
{
  "algorithm": "PPO",
  "learning_rate": 0.0001,
  "gamma": 0.99,
  "gae_lambda": 0.95,
  "clip_range": 0.2,
  "ent_coef": 0.01
}
```

### Exploration

PPO will naturally explore the continuous percentage space:
- Early training: High entropy → tries random percentages
- Late training: Low entropy → converges to learned optimal percentages

### Reward Scaling

Dense rewards are now properly scaled:
- Per-step territorial rewards: ±2.0 per tile
- Tile change rewards: ±50 per tile
- Troop growth: +0.01 per troop
- Terminal: ±1000 for win/loss

These scales allow the model to learn troop management naturally without overwhelming penalties.

## Comparison

### Before (Discrete + Constraints)
```
Action: ATTACK_NEIGHBOR_3
  ↓
Check: troops >= 70,000? NO → SKIP
Check: troops >= 70,000? YES → Continue
Calculate: available = troops - 25,000
Send: min(2000, available * 0.5)
```

**Model learned**: Which targets to pick
**Model didn't learn**: When/how hard to attack

### After (Continuous + No Constraints)
```
Action: {target: 3, percentage: 0.35}
  ↓
Calculate: troops * 0.35
Send: troops * 0.35
Observe reward feedback
Adjust percentage for next time
```

**Model learns**: Everything - when, where, and how hard to attack

## Files Modified

1. `rl_env/openfrontio_env.py` - Action space changed to Dict
2. `rl_env/game_wrapper.py` - Added attack_percentage parameter
3. `game_bridge/game_bridge_cached.ts` - Removed constraints, added percentage
4. `game_bridge/game_bridge_visual.ts` - Removed constraints, added percentage
5. `configs/phase1_config.json` - Updated action space documentation

## Next Steps

1. ✅ Implementation complete
2. 🔄 **Train new model from scratch** with continuous actions
3. 📊 **Monitor learning**:
   - Watch percentage values in logs
   - Check if model learns to preserve troops
   - Verify strategic adaptation
4. 🎮 **Visualize learned strategy**:
   - See what percentages the model chooses
   - Watch how it adapts to game state
5. 📈 **Compare performance** vs old discrete+constraint approach

## Expected Results

With proper reward scaling and continuous actions:
- **Win rate**: Should improve significantly (from 0%)
- **Strategy**: Should see intelligent troop management
- **Adaptation**: Should adjust percentages based on situation
- **Learning curve**: Should be smoother than discrete approach

The model now has the freedom to learn optimal OpenFront.io strategy!
