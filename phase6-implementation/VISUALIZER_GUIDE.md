# Phase 6 Cities Visualizer Guide

Watch your trained Phase 6 model play in real-time with the full game visualization (cities displayed as in the actual game).

## Quick Start

### Step 1: Install dependencies

```bash
cd phase6-implementation
pip install websockets
```

### Step 2: Run the visualizer (automatic mode)

The visualizer now automatically starts the dev server and opens your browser:

```bash
python3 src/visualize_realtime_cities.py --model models/ppo_cities_20251202_170832/final_model.zip
```

The script will:
1. Load your trained model
2. Start the game client dev server automatically
3. Open your browser to the correct URL
4. Start the game visualization

You should see the browser open automatically to:
```
http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia
```

**If the browser doesn't open automatically**, just manually navigate to that URL.

### Alternative: Manual mode

If you prefer to start the dev server manually (or if automatic mode fails):

1. Start the dev server in a separate terminal:
```bash
cd ../base-game
npm run dev
```

2. Run the visualizer without auto-launch:
```bash
cd phase6-implementation
python3 src/visualize_realtime_cities.py \
    --model models/ppo_cities_20251202_170832/final_model.zip \
    --no-browser
```

3. Open your browser to:
```
http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia
```

## What You'll See

- **Full game map** with territory colors
- **Cities** displayed as white markers (just like in the actual game)
- **Real-time metrics** panel showing:
  - Step count
  - Reward
  - Cumulative reward
  - Value estimate
  - Current action (direction, intensity)
- **Live game state** updating every tick

## Controls

The Phase 4 client includes:
- **Play/Pause** controls
- **Speed control** (0.5x, 1x, 2x)
- **Overlay toggles** for visualization layers

## Options

### Use a different model

```bash
python3 src/visualize_realtime_cities.py --model models/ppo_cities_20251202_170832/checkpoint_500000_steps.zip
```

### Change map or number of bots

```bash
python3 src/visualize_realtime_cities.py \
    --model models/.../final_model.zip \
    --map world_256x256 \
    --num-bots 20
```

### Custom WebSocket port

```bash
python3 src/visualize_realtime_cities.py \
    --model models/.../final_model.zip \
    --ws-port 9876
```

Then update the browser URL:
```
http://localhost:9000/rl-index.html?ws=ws://localhost:9876&map=australia_256x256
```

### Crop region (zoom to specific area)

```bash
# Center crop 800x600
python3 src/visualize_realtime_cities.py \
    --model models/.../final_model.zip \
    --crop center-800x600

# Custom crop (x, y, width, height)
python3 src/visualize_realtime_cities.py \
    --model models/.../final_model.zip \
    --crop 744,558,512,384
```

## Architecture

### Components

1. **Python Server** (`src/visualize_realtime_cities.py`):
   - Loads MaskablePPO model
   - Runs VisualGameWrapper (connects to game_bridge_visual.ts)
   - Gets actions from model
   - Broadcasts game state via WebSocket

2. **Visual Game Bridge** (`game_bridge/game_bridge_visual.ts`):
   - TypeScript bridge to actual game engine
   - Provides full visual state (all tiles, cities, players)
   - Runs in Node.js subprocess

3. **WebSocket Server** (`src/websocket_server.py`):
   - Broadcasts game updates to connected clients
   - Handles control commands (play/pause/speed)

4. **Web Client** (`client/` from Phase 4):
   - PIXI.js-based game renderer
   - WebSocket client for real-time updates
   - Displays cities as they appear in actual game

### Data Flow

```
Model → Action → VisualGameWrapper → game_bridge_visual.ts → Game Engine
                                                                    ↓
Client ← WebSocket ← Python Server ← Full Visual State (tiles + cities)
```

## Troubleshooting

### Port 9000 already in use

If you see this message:
```
✓ Dev server already running on port 9000
  Using existing server at http://localhost:9000
```

This means the dev server is already running, which is **GOOD**! The script will automatically use the existing server and your browser will open and connect to it.

If you want to start fresh and restart the dev server, you can kill the existing process first:
```bash
# Find the process using port 9000
lsof -ti:9000

# Kill it (replace <PID> with the number from above)
kill <PID>

# Then run the visualizer again
python3 src/visualize_realtime_cities.py --model models/.../final_model.zip
```

### "Error: Model not found"

Make sure you're running from `phase6-implementation` directory:

```bash
cd phase6-implementation
ls models/  # Check available models
python3 src/visualize_realtime_cities.py --model models/YOUR_MODEL/final_model.zip
```

### "Cannot find module '../game_bridge_visual.ts'"

Make sure the visual game bridge was copied correctly:

```bash
ls game_bridge/
# Should show: game_bridge.ts  game_bridge_visual.ts
```

### Client shows "Disconnected"

1. Check Python server is running and waiting for connections
2. Check WebSocket URL in browser matches server (default: `ws://localhost:8765`)
3. Check browser console (F12) for errors

### "npm run dev" fails

Make sure you're in the `base-game` directory and have installed dependencies:

```bash
cd ../../base-game
npm install
npm run dev
```

### Cities not showing

The visual game bridge should automatically mark city tiles. Check the Python server output for:

```
Sending initial state: tick=X, tiles=Y
```

If tiles count is 0, there may be an issue with the game bridge.

## Performance

- **Frame rate**: ~20-30 FPS (configurable in server)
- **Latency**: <50ms (local WebSocket)
- **CPU usage**: Low (single environment, no training)
- **Memory**: ~500MB for game + model

## Known Issues

1. **First connection delay**: The visual game bridge takes ~1-2 seconds to initialize
2. **Large maps**: Full map (2000x1500) may be slow in browser. Use crop for better performance.
3. **Multiple episodes**: Currently runs one episode. Restart server for new episode.

## Next Steps

- Watch different model checkpoints to see learning progression
- Try different maps and bot counts
- Record episodes for analysis
- Compare strategies between different training runs

Enjoy watching your AI play! 🎮
