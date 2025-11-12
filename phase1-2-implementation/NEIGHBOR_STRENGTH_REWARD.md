# Neighbor Military Strength Reward - Critical Addition

## The Key Insight

**Your main problem is the guys next to you!**

In multi-player scenarios, distant enemies don't pose immediate threats. The critical challenge is maintaining military superiority over **neighboring** players who can directly attack your territory.

## Two-Tier Reward System

### Tier 1: Global Military Strength (Background awareness)
- **Reward**: +1.0 per step
- **Condition**: `agent_troops > avg(all_enemy_troops)`
- **Purpose**: Strategic overview - "Am I generally doing well?"

### Tier 2: Neighbor Military Strength (CRITICAL!)
- **Reward**: +5.0 per step (5x more important!)
- **Condition**: `agent_troops > neighbor_enemy_troops / 2`
- **Purpose**: Tactical defense - "Can I defend against my neighbors?"

## Why 5x More Important?

Over a 10,000-step episode:
- If you maintain neighbor superiority: **+50,000 reward** 🔥
- If you maintain global superiority: +10,000 reward
- Win bonus: +15,000
- Tile expansion (50 tiles): +2,500

**The neighbor strength bonus is by far the largest reward component**, teaching the agent that local military dominance is the key to survival.

## Implementation

### 1. Game Bridge - Track Neighboring Players

```typescript
// Find all enemy players that share a border with us
const borderTiles = Array.from(this.rlPlayer.borderTiles());
const neighboringPlayerIds = new Set<number>();

for (const borderTile of borderTiles) {
  // Check all 4 adjacent tiles
  for (const offset of [{dx:0,dy:-1}, {dx:0,dy:1}, {dx:-1,dy:0}, {dx:1,dy:0}]) {
    const adjTile = this.game.ref(x + offset.dx, y + offset.dy);
    const owner = this.game.owner(adjTile);
    if (owner.isPlayer() && owner.id() !== this.rlPlayer.id()) {
      neighboringPlayerIds.add(owner.id());
    }
  }
}

// Sum total troops of neighboring enemies
const neighborEnemyTroops = this.aiPlayers
  .filter(ai => neighboringPlayerIds.has(ai.id()))
  .reduce((sum, ai) => sum + ai.troops(), 0);
```

### 2. Environment - Dual Reward Calculation

```python
# Global strength (minor reward)
if agent_troops > enemy_troops / num_enemies:
    reward += 1.0

# Neighbor strength (MAJOR reward)
if neighbor_enemy_troops > 0:
    if agent_troops > neighbor_enemy_troops / 2:
        reward += 5.0  # 5x more valuable!
```

## Expected Behavior Changes

### Before (only global strength):
1. Agent expands rapidly
2. Might be stronger than "average" enemy overall
3. But has 3 neighbors each with 80% of agent's troops
4. Gets attacked from multiple sides
5. Loses due to local weakness despite global strength

### After (with neighbor strength priority):
1. Agent checks: "Do my neighbors threaten me?"
2. If weak vs neighbors → build troops, defensive play
3. If strong vs neighbors → safe to expand
4. Maintains local military superiority
5. Survives and eliminates neighbors one by one

## Configuration

```json
{
  "reward": {
    "military_strength_bonus": 1.0,      // Global awareness
    "neighbor_strength_bonus": 5.0,      // LOCAL PRIORITY 🎯
    "per_tile_change": 50,               // Still rewards expansion
    "enemy_kill_bonus": 8000             // Big bonus for eliminations
  }
}
```

## Balance of Incentives (10,000-step episode)

Assuming agent plays well:

| Reward Source | Per Step | Total | Purpose |
|--------------|----------|-------|---------|
| **Neighbor strength** | +5.0 | **+50,000** | **Survive immediate threats** |
| Global strength | +1.0 | +10,000 | Strategic awareness |
| Tile expansion (50 tiles) | +50/tile | +2,500 | Territory growth |
| Kill enemies (3 kills) | +8000/kill | +24,000 | Eliminate opponents |
| Win bonus | - | +15,000 | Victory |
| **TOTAL** | - | **~101,500** | Full success |

**Key takeaway**: Neighbor strength (50k) dominates all other rewards except kills + win (39k combined).

## Why This Works Better Than Thresholds

**❌ Fixed threshold approach:**
- "Maintain 500 troops per tile"
- Problem: What if enemy has 1000 per tile? Or 200?
- Arbitrary number that doesn't adapt

**✅ Relative neighbor approach:**
- "Be stronger than your neighbors"
- Adapts to game dynamics
- No magic numbers to tune
- Focuses on actual threats

## Testing Expectations

### Metrics to Monitor:
1. **Neighbor strength bonus frequency** - should be high (70%+ of steps)
2. **Survival time** - should increase significantly
3. **Deaths to neighbors vs distant enemies** - should decrease
4. **Average troop count** - should be higher
5. **Expansion rate** - should be slower but more sustainable

### Behavioral Changes:
- Agent pauses expansion when neighbors are strong
- Agent builds up troops before attacking neighbors
- Agent prioritizes defending border tiles
- Agent eliminates weak neighbors quickly

## Tuning Guide

If agent is too passive (doesn't expand):
- Reduce `neighbor_strength_bonus` to 3.0-4.0
- Increase `per_tile_change` to 60-75

If agent still overextends:
- Increase `neighbor_strength_bonus` to 7.0-10.0
- Reduce `per_tile_change` to 30-40

Current value (5.0) should provide good balance.

## Files Modified

1. `game_bridge/game_bridge_cached.ts` - Added `neighbor_enemy_troops` tracking
2. `rl_env/openfrontio_env.py` - Added neighbor strength reward calculation
3. `configs/phase2_config.json` - Added `neighbor_strength_bonus: 5.0`

## Summary

**The neighbor strength reward solves the overextension problem by teaching the agent:**

> "Your main threat is not the player across the map - it's the player next to you.
> Stay stronger than your neighbors, and you'll survive and win."

This is the MOST IMPORTANT reward in Phase 2. It receives 5x the weight of global strength because local threats determine survival in multi-agent scenarios.
