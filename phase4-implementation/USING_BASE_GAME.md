# Phase 4: Using the Full Base Game Client

## Overview

We've integrated Phase 4 directly with the **full base game client**, giving you:

✅ **All game features**: Alliances, gold, nukes, boats, buildings, cities
✅ **Professional UI**: Leaderboard, chat, player panels, game controls
✅ **Polished graphics**: All visual effects, animations, terrain rendering
✅ **RL Overlay**: Model state visualization on top of everything

## Architecture

```
Python Side                     Base Game Client
───────────                     ─────────────────
visualize_realtime.py           rl-index.html
     ↓                               ↓
visual_game_wrapper.py         RLGameRunner.ts
     ↓                               ↓
game_bridge_visual.ts ←─────→ RLTransport.ts
     ↓                               ↓
Full Game Engine              GameRenderer + RLOverlayLayer
                                    ↓
                            Full Game UI + RL Overlays
```

## What We Added to Base Game

### New Files in `base-game/src/client/`:

1. **RLTransport.ts**
   - Connects to Phase 4 visual bridge (instead of multiplayer server)
   - Receives game state and model state updates via WebSocket

2. **RLGameRunner.ts**
   - Initializes the game in RL mode
   - Manages renderer and overlay layer
   - Handles connection to Python bridge

3. **graphics/layers/RLOverlayLayer.ts**
   - Renders action probability arrows
   - Shows value estimates and rewards
   - Displays model internals on top of game

4. **rl-index.html**
   - Entry point for RL visualization
   - Includes play/pause/step controls
   - Toggle for overlay visibility

## Setup

### 1. Install Base Game Dependencies

```bash
cd base-game
npm install
```

### 2. Build Base Game (if needed)

```bash
cd base-game
npm run build
```

Or use dev mode for hot reload:

```bash
cd base-game
npm run dev
```

### 3. Install Phase 4 Dependencies

```bash
cd ../phase4-implementation
pip install -r requirements.txt
```

## Usage

### Start the Full Visualizer

```bash
cd phase4-implementation
python src/visualize_realtime.py \
  --model ../phase3-implementation/runs/run_TIMESTAMP/openfront_final.zip \
  --map australia \
  --crop center-512x384
```

**Command-line Options:**
- `--model` - Path to trained PPO model (required)
- `--map` - Map to use: `australia`, `world`, `europe`, `plains` (default: `australia`)
- `--crop` - Crop region: `center-WxH`, `x,y,w,h`, or `none` (default: `center-512x384`)
- `--num-bots` - Number of AI opponents (default: 10)
- `--ws-host` - WebSocket host (default: `localhost`)
- `--ws-port` - WebSocket port (default: 8765)
- `--no-browser` - Don't auto-start client dev server

This will:
1. ✅ Load the Australia map with realistic terrain
2. ✅ Crop a centered 512×384 region for focused visualization
3. ✅ Start the visual game bridge
4. ✅ Start the WebSocket server
5. ✅ Tell you to open the base game client

### Open the Game Client

Open in your browser:
```
file:///path/to/base-game/src/client/rl-index.html?ws=ws://localhost:8765
```

Or if you're running a dev server:
```
http://localhost:PORT/rl-index.html?ws=ws://localhost:8765
```

## What You'll See

### Full Game Features

Since we're using the complete base game, you get:

**🎮 Game Elements:**
- ✅ Territories with player colors
- ✅ Cities, ports, and other buildings
- ✅ Units: Infantry, boats, nukes
- ✅ Terrain: Plains, mountains, water
- ✅ Visual effects: Attacks, explosions, movements

**📊 UI Components:**
- ✅ Leaderboard (live rankings)
- ✅ Player panel (stats, gold, troops)
- ✅ Build menu (construction options)
- ✅ Alliance system (if enabled)
- ✅ Chat display
- ✅ Settings panel

**🤖 RL Overlays:**
- ✅ Action probability arrows (showing where model wants to go)
- ✅ Value function estimate
- ✅ Reward display
- ✅ Current action visualization

### Controls

**Top-right panel:**
- ▶️ **Play**: Resume game
- ⏸️ **Pause**: Pause game
- ⏭️ **Step**: Advance one frame
- ⏮️ **Reset**: Restart episode
- ☑️ **Show Model Overlay**: Toggle RL visualization

**Game UI** (all base game features work):
- Click to select tiles
- Use build menu to see what the AI could build
- View leaderboard for rankings
- See all player stats

## Features Available

### Basic Game Mechanics
- ✅ Territory control
- ✅ Troop movement
- ✅ Attacks and defenses
- ✅ Resource gathering (gold)
- ✅ Population growth

### Advanced Features
- ✅ **Buildings**: Cities, ports, factories
- ✅ **Units**: Infantry, boats, nukes, trains
- ✅ **Alliances**: See alliance formations
- ✅ **Gold Economy**: Resource management
- ✅ **Tech/Buildings**: Construction system

### Visual Features
- ✅ Smooth animations
- ✅ Particle effects
- ✅ Terrain rendering
- ✅ Unit movements
- ✅ Attack visualizations

## Advantages Over Phase 4 Simple Client

| Feature | Phase 4 Simple | Phase 4 + Base Game |
|---------|----------------|---------------------|
| **Rendering** | Basic tiles (4px) | Professional graphics |
| **UI** | Minimal metrics panel | Full game UI |
| **Features** | Territory only | Cities, boats, nukes, alliances |
| **Animations** | None | Full animations |
| **Polish** | Basic | Production-quality |
| **Code** | ~2000 lines custom | ~300 lines + base game |

## Customization

### Modify RL Overlay

Edit `base-game/src/client/graphics/layers/RLOverlayLayer.ts`:

```typescript
// Change arrow colors
const color = isSelected ? 0x00ff00 : 0xffffff;

// Adjust arrow size
const length = radius + prob * 50;

// Add custom visualizations
this.drawCustomOverlay();
```

### Add More Metrics

Edit `RLOverlayLayer.ts` to add more model information:

```typescript
// In updateMetrics()
this.metricsText.text = [
  `Value: ${this.modelState.value_estimate.toFixed(2)}`,
  `Reward: ${this.modelState.reward.toFixed(2)}`,
  `Cumulative: ${this.modelState.cumulative_reward.toFixed(2)}`,
  `Action: ${this.modelState.action.direction}`,
  // Add custom metrics here
  `My Custom Metric: ${myValue}`,
].join('\n');
```

### Toggle Different Overlays

You can add multiple visualization modes:

```typescript
eventBus.on('rl-show-heatmap', () => {
  this.drawObservationHeatmap();
});

eventBus.on('rl-show-attention', () => {
  this.drawAttentionWeights();
});
```

## Troubleshooting

### "Cannot find module RLGameRunner"

Make sure you've built the base game or are running in dev mode:

```bash
cd base-game
npm run build
# or
npm run dev
```

### "WebSocket connection failed"

Make sure Python server is running:

```bash
cd phase4-implementation
python src/visualize_realtime.py --model path/to/model.zip
```

### "Game doesn't render"

Check browser console for errors. Make sure:
1. WebSocket is connected (check console log)
2. Game state is being received (check network tab)
3. No JavaScript errors (check console)

### Want original multiplayer mode?

Just open the regular `index.html` instead of `rl-index.html`:
```
base-game/src/client/index.html
```

## Next Steps

### Add More Overlays

1. **Observation Heatmap**: Show what tiles the model focuses on
2. **Value Map**: Show value estimates for different regions
3. **Attention Visualization**: If using attention models
4. **Prediction Trails**: Show predicted future positions

### Enhanced Controls

1. **Speed control**: Slider for playback speed
2. **Frame seeking**: Jump to specific game states
3. **Recording**: Save and replay sessions
4. **Comparison**: Side-by-side model comparison

### Integration with Training

1. **Live training visualization**: Watch model improve in real-time
2. **Checkpoint comparison**: Compare different training checkpoints
3. **A/B testing**: Compare two models simultaneously

## Summary

By using the full base game client, you get:
- ✅ **Professional quality** visualization
- ✅ **All game features** (alliances, gold, nukes, boats, buildings)
- ✅ **Minimal custom code** (~300 lines vs 2000+)
- ✅ **Easy maintenance** (updates to base game automatically available)
- ✅ **Familiar interface** (if you've played OpenFront.io)

This is the **proper** way to build the Phase 4 visualizer! 🎉
