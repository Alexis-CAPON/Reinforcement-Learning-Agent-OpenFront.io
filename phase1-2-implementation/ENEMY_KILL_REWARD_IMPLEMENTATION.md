# Enemy Kill Reward System - Implementation Summary

## Overview
Implemented a reward bonus system that gives the RL agent +5,000 reward for each enemy player it completely eliminates from the game.

## Implementation Details

### 1. Game Bridge (`game_bridge/game_bridge_cached.ts`)

**Added ConquestEvent tracking:**
- Import `GameUpdateType` from GameUpdates
- Modified `tick()` method to capture `GameUpdates` from `executeNextTick()`
- Check `ConquestEvent` updates to count eliminations by the RL agent
- Added `enemies_killed_this_tick` field to `GameState` interface

```typescript
// In tick() method:
const updates = this.game.executeNextTick();
const conquestEvents = updates[GameUpdateType.ConquestEvent] || [];

for (const event of conquestEvents) {
  if (event.conquerorId === this.rlPlayer.id()) {
    enemiesKilledThisTick++;
  }
}

state.enemies_killed_this_tick = enemiesKilledThisTick;
```

### 2. Environment (`rl_env/openfrontio_env.py`)

**Added kill bonus to reward calculation:**
- Read `enemy_kill_bonus` from config (default: 5,000)
- Check `enemies_killed_this_tick` in game state
- Add bonus to reward when enemies are eliminated

```python
# In _calculate_reward():
enemies_killed = state_after.get('enemies_killed_this_tick', 0)
if enemies_killed > 0:
    reward += enemies_killed * self.reward_enemy_kill
```

### 3. Configuration (`configs/phase1_config.json`)

**Added kill bonus parameter:**
```json
"reward": {
  "enemy_kill_bonus": 5000,
  ...
}
```

## How It Works

1. **During Gameplay**: When the RL agent captures an enemy player's last tile, eliminating them from the game
2. **ConquestEvent Triggered**: The game engine fires a `ConquestEvent` with:
   - `conquerorId`: The RL agent's player ID
   - `conqueredId`: The eliminated player's ID
   - `gold`: Bonus gold awarded
3. **Detection**: The game bridge captures this event during `tick()` and increments `enemies_killed_this_tick`
4. **Reward Calculation**: The environment reads this count and adds `5000 × enemies_killed` to the step reward
5. **Logging**: When a kill occurs, the game bridge logs: `"RL Agent eliminated player X! Gold bonus: Y"`

## Reward Structure

**Current reward system (v1.0.3):**
- Tile gained/lost: ±100 per tile
- Action taken: +0.5
- **Enemy eliminated: +5,000** ← NEW
- Time penalty: -0.1 per step
- Victory: +10,000
- Defeat: -10,000
- Timeout: -5,000

**Design rationale:**
- Kill bonus (5,000) is significant but less than win bonus (10,000)
- Encourages aggressive play that eliminates opponents
- Teaches agent that eliminating players is a key strategic goal
- Scales with number of kills (multiple enemies = multiple bonuses)

## Testing

Run the test script to verify the system is set up correctly:
```bash
python3 test_kill_reward.py
```

To see actual kills in action:
1. Train an agent that learns aggressive play
2. Watch for `[GameBridge] RL Agent eliminated player X!` messages in stderr
3. Check that episode rewards include +5000 bonuses for eliminations
4. Monitor training logs for episodes with kills (rewards will be noticeably higher)

## Future Enhancements

Potential improvements:
- Add partial elimination rewards (e.g., reducing enemy to <10% of map)
- Track kill statistics in episode info dict
- Add kill count to training callback logging
- Visualize eliminations in the HTML visualization tool
- Tune kill bonus value based on training performance

## Files Modified

1. `game_bridge/game_bridge_cached.ts` - Added ConquestEvent tracking
2. `rl_env/openfrontio_env.py` - Added kill bonus to rewards
3. `configs/phase1_config.json` - Added enemy_kill_bonus parameter
4. `test_kill_reward.py` - Test script (new file)
