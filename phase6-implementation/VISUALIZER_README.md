# Phase 6 Cities Visualizer

Watch your trained MaskablePPO agent play in real-time with a web-based visualization.

## Features

- Real-time game visualization showing territory control
- City markers on the map
- Game metrics: territory %, cities, gold, rank
- Action information: direction, intensity, cluster
- Playback controls: play/pause, speed control (0.5x, 1x, 2x)
- Automatic reconnection if connection is lost

## Quick Start

### 1. Start the Python server

Open a terminal and run:

```bash
cd phase6-implementation
python3 visualize_cities.py --model models/ppo_cities_20251202_170832/final_model.zip
```

The server will start and wait for a client connection. You should see:

```
Loading model from models/ppo_cities_20251202_170832/final_model.zip...
✓ Model loaded successfully
Creating environment: map=australia_256x256, bots=10...
✓ Environment created
WebSocket server started on ws://localhost:8765

================================================================================
PHASE 6 CITIES VISUALIZER
================================================================================
Model: models/ppo_cities_20251202_170832/final_model.zip
Map: australia_256x256
Opponents: 10 bots
WebSocket: ws://localhost:8765
================================================================================

Waiting for client connection...
```

### 2. Open the web client

In your web browser, open:

```
file:///Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase6-implementation/client.html
```

Or simply double-click `client.html` in Finder.

### 3. Watch the game!

The client will automatically connect to the server and start visualizing the game. You'll see:

- **Territory map** - Different colors for different players
  - Green = Your RL agent
  - Other colors = Enemy bots
  - Dark gray = Neutral territory
  - White markers = Cities

- **Game metrics** - Real-time stats:
  - Step count
  - Territory percentage
  - Number of cities
  - Gold amount
  - Rank (e.g., "3/11" = 3rd place out of 11 players)
  - Cumulative reward

- **Action info** - What the model is doing:
  - Direction (N, NE, E, SE, S, SW, W, NW, WAIT)
  - Intensity (0-100% of troops)
  - Cluster ID (which territory cluster is attacking)

### 4. Controls

- **▶ Play** - Resume the game (default state)
- **⏸ Pause** - Pause the game
- **0.5x** - Slow down to half speed
- **1x** - Normal speed
- **2x** - Double speed

## Options

### Use a different model

```bash
# Use a checkpoint from earlier in training
python3 visualize_cities.py --model models/ppo_cities_20251202_170832/checkpoint_500000_steps.zip

# Use a different training run
python3 visualize_cities.py --model models/ppo_cities_YYYYMMDD_HHMMSS/final_model.zip
```

### Change map or number of bots

```bash
# Different map
python3 visualize_cities.py --model models/.../final_model.zip --map world_256x256

# Fewer opponents (easier)
python3 visualize_cities.py --model models/.../final_model.zip --bots 5

# More opponents (harder)
python3 visualize_cities.py --model models/.../final_model.zip --bots 20
```

### Change WebSocket port

```bash
# Use a different port
python3 visualize_cities.py --model models/.../final_model.zip --ws-port 9000
```

Then open `client.html` and manually edit line 139 to change the port:

```javascript
const wsUrl = 'ws://localhost:9000';  // Changed from 8765
```

## Troubleshooting

### "Error: Model not found"

Make sure you're running from the `phase6-implementation` directory and the model path is correct:

```bash
# List available models
ls -la models/

# Use the correct path
python3 visualize_cities.py --model models/ppo_cities_20251202_170832/final_model.zip
```

### Client shows "Disconnected"

1. Make sure the Python server is running
2. Check that the WebSocket URL is correct (`ws://localhost:8765`)
3. Check browser console for errors (F12 → Console tab)

### Game is too fast/slow

Use the speed controls in the web client:
- 0.5x for slow motion
- 1x for normal speed
- 2x for fast forward

Or modify the delay in `visualize_cities.py` line 268:

```python
await asyncio.sleep(0.05 / self.ws_server.speed)  # Increase 0.05 to slow down
```

### Map is too small/large

The visualization downsamples the 512×512 map to 128×128 tiles at 4 pixels per tile.

To change the tile size, edit `client.html` line 145:

```javascript
const TILE_SIZE = 4;  // Increase to 6 or 8 for larger tiles
```

## Technical Details

### Architecture

1. **Python server** (`visualize_cities.py`):
   - Loads the trained MaskablePPO model
   - Runs the Phase 6 cities environment
   - Gets actions from the model with action masking
   - Broadcasts game state + model state via WebSocket
   - Handles control commands (play/pause/speed)

2. **HTML client** (`client.html`):
   - Connects to WebSocket server
   - Renders the game on HTML5 canvas
   - Displays metrics and action info
   - Sends control commands back to server

### Data Flow

```
Server → Client: game_state (every step)
  - Territory map (tiles with owner IDs)
  - Player info (colors, alive status)
  - RL player metrics (territory, cities, gold, rank)

Server → Client: model_state (every step)
  - Action taken (cluster, direction, intensity, build)
  - Reward and cumulative reward
  - Value estimate (if available)

Client → Server: control commands
  - play, pause
  - speed (0.5, 1.0, 2.0)
```

### Performance

- Game runs at ~20 ticks/second (configurable)
- WebSocket bandwidth: ~50-100 KB/s (depends on map activity)
- CPU usage: Low (single environment, no training)

## Next Steps

After watching your model play:

1. **Analyze behavior** - Watch how it expands, builds cities, handles enemies
2. **Test different models** - Compare checkpoints at 100K, 500K, 1M, 1.5M steps
3. **Experiment with parameters** - Try different maps, bot counts
4. **Record episodes** - Take notes on strategies that work/don't work
5. **Continue training** - If model isn't performing well, train longer

Enjoy watching your AI play! 🏆
