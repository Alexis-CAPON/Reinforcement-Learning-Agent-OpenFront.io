# Phase 4 Already Uses Phase 3's Game Bridge!

## TL;DR

**Phase 4's game bridge is already set up correctly** - it uses the same approach as Phase 3 and exports proper `GameUpdateViewData` for the TypeScript client.

## Architecture

```
Phase 4 Visualization:
┌─────────────────────────────────────────────────────────────┐
│  Python RL Environment (Phase 3)                             │
│    ↓                                                         │
│  game_bridge_visual.ts (Phase 4)                            │
│    - Uses Phase 3's Game object                             │
│    - Exports GameUpdateViewData (proper format)             │
│    ↓                                                         │
│  WebSocket Server (websocket_server.py)                     │
│    - broadcast_game_update(visual_state, gameUpdate)        │
│    ↓                                                         │
│  TypeScript Client (RLWorkerClient.ts)                      │
│    - Receives GameUpdateViewData via WebSocket              │
│    - Passes to GameView → GameRenderer → Full UI            │
└─────────────────────────────────────────────────────────────┘
```

## What Phase 4's game_bridge_visual.ts Does

Located at: `phase4-implementation/game_bridge/game_bridge_visual.ts`

**Key features:**
1. **Uses real Game object** - Same as Phase 3's battle royale setup
2. **Exports GameUpdateViewData** - Proper format for TypeScript client
3. **Action execution** - attackDirection(), buildStructure(), etc.
4. **Backward compatibility** - Also exports simple VisualState

**Code excerpt:**
```typescript
tick(): Response {
  // Execute game tick and get updates
  const updates = this.game.executeNextTick();

  // Update player view data (same as GameRunner)
  if (this.currentTick < 3 || this.currentTick % 30 === 0) {
    this.game.players().forEach((p) => {
      this.playerViewData[p.id()] = placeName(this.game!, p);
    });
  }

  // Pack tile updates (same as GameRunner)
  const packedTileUpdates = updates[GameUpdateType.Tile].map((u: any) => u.update);
  updates[GameUpdateType.Tile] = [];

  // Create GameUpdateViewData (same format as Worker sends)
  const gameUpdateViewData: any = {
    tick: this.currentTick,
    packedTileUpdates: packedTileUpdatesNumbers,
    updates: updatesWithNumbers,
    playerNameViewData: playerNameViewDataWithNumbers,
  };

  // Return both formats
  return {
    type: 'game_update',
    gameUpdate: gameUpdateViewData,  // ← For TypeScript client
    state: visualState,              // ← Backward compat
    success: true
  };
}
```

## What Phase 4's websocket_server.py Does

Located at: `phase4-implementation/src/websocket_server.py`

**Already has the right methods:**
```python
async def broadcast_game_update(self, visual_state: Dict, game_update: Dict):
    """Broadcast both visual state and game update"""
    message = {
        'type': 'game_update',
        'tick': visual_state['tick'],
        'visual_state': visual_state,
        'gameUpdate': game_update  # ← Sent to client
    }
    await self.broadcast(message)
```

## How It All Connects

### Python Side (visualize_realtime.py):

```python
# 1. Create game wrapper (uses game_bridge_visual.ts)
game_wrapper = VisualGameWrapper(
    map_name='plains',
    num_bots=10
)

# 2. Create WebSocket server
server = RLWebSocketServer()

# 3. Game loop
while True:
    # Get action from RL model
    action = model.get_action(observation)

    # Submit action to game bridge
    game_wrapper.submit_action(action)

    # Tick game and get response
    response = game_wrapper.tick()

    # Send both gameUpdate and visual_state
    await server.broadcast_game_update(
        visual_state=response['state'],
        gameUpdate=response['gameUpdate']  # ← GameUpdateViewData
    )

    # Also send model state for overlay
    await server.broadcast_model_state(...)
```

### TypeScript Side (RLWorkerClient.ts):

```typescript
// Receive message from WebSocket
private handleMessage(message: any) {
  if (message.type === 'game_update' && message.gameUpdate) {
    // Pass GameUpdateViewData to callback
    if (this.gameUpdateCallback) {
      this.gameUpdateCallback(message.gameUpdate);
    }
  }
}
```

## Why This Works

1. **Phase 4's game bridge uses Phase 3's Game object**
   - Same battle royale setup
   - Same action execution
   - Same game mechanics

2. **Exports proper GameUpdateViewData**
   - Same format as Web Worker sends
   - Contains all player/unit/tile updates
   - Ready for GameView to consume

3. **WebSocket server already broadcasts it**
   - `broadcast_game_update()` sends gameUpdate
   - TypeScript client receives it
   - GameView processes it
   - GameRenderer displays it

## What You Need to Do

**Nothing for the bridge itself!** It's already correct. Just:

### 1. Update Your Python RL Visualization Script

Make sure it uses `visualize_realtime.py` or similar:

```python
from src.visual_game_wrapper import VisualGameWrapper
from src.websocket_server import RLWebSocketServer

# Create game wrapper
game = VisualGameWrapper(map_name='plains', num_bots=10)

# Create WebSocket server
server = RLWebSocketServer(port=8765)
await server.start()

# Game loop
while True:
    # Get model action
    action = your_model.get_action(obs)

    # Submit to game
    game.submit_action(action)

    # Tick and get updates
    response = game.tick()

    # Broadcast to client
    await server.broadcast_game_update(
        response['state'],
        response['gameUpdate']  # ← This is GameUpdateViewData!
    )

    # Send model state for overlay
    await server.broadcast_model_state(
        tick=response['tick'],
        observation=obs,
        action_dict=action_info,
        value=value,
        reward=reward,
        cumulative_reward=cum_reward
    )
```

### 2. Build the TypeScript Client

```bash
cd base-game
npm run build
```

This will bundle RLMain.ts into the output.

### 3. Run Everything

```bash
# Terminal 1: Start WebSocket server
cd phase4-implementation
python src/visualize_realtime.py  # Or your visualization script

# Terminal 2: Serve the client
cd base-game/static
python -m http.server 8080

# Browser: Open visualization
http://localhost:8080/rl-index.html?ws=ws://localhost:8765
```

## Common Issues

### "gameUpdate format is wrong"
- **Cause**: Phase 4's bridge converts BigUint64Array to number arrays for JSON
- **Solution**: RLWorkerClient accepts both formats - should work fine

### "Not seeing units/cities"
- **Cause**: GameUpdateViewData might be missing unit updates
- **Solution**: Check that `response['gameUpdate']` has `updates[GameUpdateType.Unit]`

### "Model overlay not showing"
- **Cause**: Not sending `model_state` messages
- **Solution**: Call `server.broadcast_model_state()` after each tick

## Summary

**Phase 4 is already correctly set up!** The game bridge:
- ✅ Uses Phase 3's Game object
- ✅ Exports GameUpdateViewData in proper format
- ✅ Has action execution methods
- ✅ Works with WebSocket server
- ✅ Compatible with new TypeScript client

You don't need to change the bridge itself. Just make sure your Python visualization script uses it correctly!
