# Attack Mechanics Fix

## Problem Discovered

Through visualization, we discovered that the RL agent was depleting its army while AI bots maintained theirs:

- **RL Agent**: Started with 24,000 troops → dropped to 25 troops in ~10 attacks
- **AI Bots**: Maintained and grew troop levels throughout the game

## Root Cause Analysis

### Original Implementation (BROKEN)
```typescript
// game_bridge_cached.ts (old)
attackTile(tile_x: number, tile_y: number) {
    const attackTroops = Math.min(1000, Math.floor(this.rlPlayer.troops() * 0.5));
    this.game.addExecution(new AttackExecution(attackTroops, this.rlPlayer, targetId));
}
```

**Problem**: Attacking with **50% of total troops EVERY SINGLE TICK**
- Attack 1: 24000 * 0.5 = 12000 troops sent → 12000 left
- Attack 2: 12000 * 0.5 = 6000 troops sent → 6000 left
- Attack 3: 6000 * 0.5 = 3000 troops sent → 3000 left
- After 10 attacks: ~25 troops remaining
- Regeneration: ~200-500 troops/tick
- Net loss: ~10,000 troops/tick spent vs 500 gained = **-9,500 troops/tick**

### AI Bot Strategy (CORRECT)

From `base-game/src/core/execution/utils/BotBehavior.ts`:

```typescript
sendAttack(target: Player | TerraNullius) {
    const maxTroops = this.game.config().maxTroops(this.player);
    const reserveRatio = target.isPlayer() ? this.reserveRatio : this.expandRatio;
    const targetTroops = maxTroops * reserveRatio;
    const troops = this.player.troops() - targetTroops;
    if (troops < 1) return;
    // Send only surplus above reserve
}
```

**Key differences**:
1. **Attack frequency**: Every 40-80 ticks (not every tick)
2. **Reserve strategy**: Keep 20-30% of maxTroops in reserve
3. **Trigger threshold**: Only attack when above 60-90% of maxTroops
4. **Attack size**: Send `(current_troops - reserve)`, not 50% of total

## Fix Implemented

### New Implementation (Both Bridges)

Updated both `game_bridge_cached.ts` and `game_bridge_visual.ts`:

```typescript
attackTile(tile_x: number, tile_y: number): void {
    if (!this.rlPlayer.canAttack(targetTile)) {
        return;
    }

    // Option 3: Trigger Threshold - Only attack when above 70% of max troops
    const maxTroops = this.maxTroops;
    const triggerRatio = 0.7;
    const currentTroops = this.rlPlayer.troops();

    if (currentTroops < maxTroops * triggerRatio) {
        this.log(`Skipping attack - troops too low (${currentTroops} < ${maxTroops * triggerRatio})`);
        return;  // Not enough troops, skip attack
    }

    // Option 2: Reserve Strategy - Keep 25% of max troops in reserve
    const reserveRatio = 0.25;
    const reserve = maxTroops * reserveRatio;
    const availableToSend = Math.max(0, currentTroops - reserve);

    if (availableToSend < 50) {
        this.log(`Skipping attack - available troops too low (${availableToSend})`);
        return;  // Not enough surplus to send
    }

    // Send 50% of available troops (after reserve), capped at 2000
    const attackTroops = Math.min(2000, Math.floor(availableToSend * 0.5));

    // Validate attackTroops is a valid number
    if (isNaN(attackTroops) || !isFinite(attackTroops) || attackTroops < 1) {
        this.log(`Invalid attack troops: ${attackTroops}, skipping attack`);
        return;
    }

    this.log(`Attacking (${tile_x}, ${tile_y}) with ${attackTroops} troops (${currentTroops} total, ${reserve} reserve)`);

    this.game.addExecution(
        new AttackExecution(attackTroops, this.rlPlayer, targetId)
    );
}
```

### Parameters

- **maxTroops**: 100,000 (default for RL agent)
- **triggerRatio**: 0.7 (only attack when above 70,000 troops)
- **reserveRatio**: 0.25 (always keep 25,000 troops safe)
- **attackTroops**: min(2000, (availableToSend * 0.5))

### Example Scenario

Starting with 80,000 troops:
1. **Trigger check**: 80,000 > 70,000 ✅ (can attack)
2. **Reserve**: 25,000 troops kept in reserve
3. **Available**: 80,000 - 25,000 = 55,000 troops
4. **Attack size**: min(2000, 55,000 * 0.5) = 2,000 troops
5. **Result**: 2,000 sent, 78,000 remain
6. **Regeneration**: ~400 troops/tick
7. **Net**: -2,000 + 400 = sustainable!

## Impact on Training

### Old Model (trained with broken mechanics)
- Learned: "Attacking depletes army → attacking is bad"
- Strategy: Avoid attacking, play passively
- Win rate: 0%

### New Model (will train with fixed mechanics)
- Will learn: "Attacking expands territory → attacking is good"
- Strategy: Aggressive expansion while maintaining army
- Expected win rate: Much higher!

## Files Modified

1. `/game_bridge/game_bridge_cached.ts` - Training environment bridge
2. `/game_bridge/game_bridge_visual.ts` - Visualization bridge
3. Both bridges now have identical attack mechanics

## Verification

Visualization now shows:
- RL Agent: 70,146 troops (maintaining and growing)
- AI Bot: 14,754 troops (normal bot behavior)
- Both with similar territory (~1,400 tiles)

The 5x difference is expected due to:
- Human PlayerType gets 3x max troop cap vs bots
- Bots get 0.6x regeneration rate
- This is intentional game design!

## Next Steps

1. ✅ Visualization fixed - shows real game mechanics
2. ✅ Training environment fixed - identical mechanics
3. 🔄 **Retrain model from scratch** with new mechanics
4. 📊 **Compare old vs new** model performance
5. 🎮 **Visualize new model** to see improved strategy

## Training Command

```bash
python train.py train --config configs/phase1_config.json
```

This will train with:
- ✅ Dense rewards (from REWARD_STRUCTURE_FIX.md)
- ✅ Sustainable attack mechanics (this fix)
- ✅ Reserve + trigger strategy
- ✅ 2-player games, 1,500 max steps
