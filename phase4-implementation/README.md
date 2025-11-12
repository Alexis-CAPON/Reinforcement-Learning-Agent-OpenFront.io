# Phase 4: Real-Time RL Visualizer

Watch your RL model play OpenFront.io with **full game client rendering** and **real-time overlays** showing model internals!

## Overview

Phase 4 provides a sophisticated real-time visualization system where **your RL model actually plays the real game** with full terrain, mechanics, and features. The model plays on real maps (like Australia with mountains and coastlines) using the complete game engine, and we add overlay layers to show model internals:

- **Real Gameplay**: Model plays the actual game with real terrain (mountains, water, coastlines)
- **Full Game Mechanics**: All features work (gold, cities, alliances, nukes, boats)
- **Action Probabilities**: See which directions the model is considering
- **Value Estimates**: View the model's value function predictions
- **Rewards**: Track rewards in real-time
- **Observation Heatmaps**: Visualize what the model "sees" (optional)
- **Attention Weights**: If your model uses attention, see what it focuses on (optional)

**Important**: This is not a simulation - the model is playing the REAL game on REAL maps with REAL terrain affecting gameplay!

## Features

### Real Gameplay on Real Maps
- ✅ **Full Game Engine**: Complete OpenFront.io game logic running in real-time
- ✅ **Real Terrain**: Mountains, water, coastlines affect movement and strategy
- ✅ **Real Maps**: Australia (2000×1500), World, Europe with actual geographic features
- ✅ **All Mechanics**: Gold economy, city building, alliances, nukes, boats
- ✅ **Real Opponents**: AI bots using actual game AI

### Real-Time Visualization
- Uses the full OpenFront.io game client (not just simple tiles)
- Overlay system that shows model internals on top of the real gameplay
- WebSocket-based communication for low-latency updates
- Interactive controls (play, pause, step, speed)

### Model Introspection
- Extract action probability distributions
- View value function estimates
- Track cumulative rewards
- Optionally visualize attention mechanisms

### Interactive Controls
- Play/Pause/Step controls
- Speed adjustment (1x-10x)
- Toggle individual overlays on/off
- Live metrics display

## Architecture

```
┌─────────────────────────────────────────┐
│        Python RL Environment             │
│                                          │
│  1. Model predicts action                │
│  2. Extract model internals              │
│  3. Execute action in game               │
│  4. Send state to visualizer             │
└────────────────┬─────────────────────────┘
                 │ WebSocket
                 ↓
┌─────────────────────────────────────────┐
│    TypeScript Client (Browser)          │
│                                          │
│  1. Receive model state                 │
│  2. Render full game (Pixi.js)          │
│  3. Overlay model visualizations        │
│  4. Display metrics & controls          │
└─────────────────────────────────────────┘
```

## Installation

### 1. Install Python Dependencies

```bash
cd phase4-implementation
pip install -r requirements.txt
```

Required packages:
- `websockets` - WebSocket server (Python)
- `numpy` - Numerical operations
- `torch` - PyTorch for model internals
- `stable-baselines3` - RL models

**Note**: The browser uses native WebSocket support, so no JavaScript WebSocket library is needed.

### 2. Install TypeScript/JavaScript Dependencies

```bash
npm install
```

This installs:
- `pixi.js` - GPU-accelerated 2D rendering
- `vite` - Fast development server
- `typescript` - TypeScript compiler

**Note**: WebSocket support is built into modern browsers, so no additional packages are needed for WebSocket functionality.

## Usage

### Quick Start

```bash
# Run the visualizer (starts both server and client)
python src/visualize_realtime.py --model ../phase3-implementation/runs/run_TIMESTAMP/openfront_final.zip
```

This will:
1. Start the WebSocket server on `ws://localhost:8765`
2. Start the Vite dev server on `http://localhost:3000`
3. Automatically open your browser
4. Begin playing the game with visualizations

### Command-Line Options

```bash
python src/visualize_realtime.py [OPTIONS]

Required:
  --model PATH            Path to trained model (.zip file)

Optional:
  --map NAME              Map to use: australia, world, europe, plains (default: australia)
  --crop REGION           Crop region: center-WxH, x,y,w,h, or none (default: center-512x384)
  --num-bots N            Number of bot opponents (default: 10)
  --ws-host HOST          WebSocket server host (default: localhost)
  --ws-port PORT          WebSocket server port (default: 8765)
  --no-browser            Don't start the client dev server
```

**Map Options:**
- `australia` (2000×1500): Realistic Australia with coastlines and mountains (default)
- `world` (2000×1000): World map with continents
- `europe` (1500×1200): European region
- `plains`: Simple flat map

**Crop Formats:**
- `center-WxH`: Auto-centered crop (e.g., `center-512x384`)
- `x,y,w,h`: Custom coordinates (e.g., `744,558,512,384`)
- `none`: No cropping, use full map

See `MAP_CROPPING.md` for detailed information about maps and cropping.

### Examples

**Basic usage (Australia map with centered crop):**
```bash
python src/visualize_realtime.py \
  --model ../phase3-implementation/runs/run_20250103_120000/openfront_final.zip \
  --map australia \
  --crop center-512x384
```

**Larger crop for more context:**
```bash
python src/visualize_realtime.py \
  --model model.zip \
  --map australia \
  --crop center-800x600
```

**Custom region focus:**
```bash
python src/visualize_realtime.py \
  --model model.zip \
  --map australia \
  --crop 500,400,640,480
```

**Battle royale with 50 bots on world map:**
```bash
python src/visualize_realtime.py \
  --model model.zip \
  --map world \
  --crop center-1000x500 \
  --num-bots 50
```

**Full map, no cropping:**
```bash
python src/visualize_realtime.py \
  --model model.zip \
  --map australia \
  --crop none
```

**Custom WebSocket port:**
```bash
python src/visualize_realtime.py \
  --model model.zip \
  --ws-port 9000
```

**Manual client (for development):**
```bash
# Terminal 1: Start Python server
python src/visualize_realtime.py --model model.zip --no-browser

# Terminal 2: Start client manually
npm run dev
```

## Visualizer Controls

### Playback Controls

Located in the top-right panel:

- **▶️ Play**: Resume playback
- **⏸️ Pause**: Pause playback
- **⏭️ Step**: Advance one step (when paused)
- **⏮️ Reset**: Restart the episode
- **Speed**: Adjust playback speed (1x-10x)

### Overlay Toggles

Toggle different overlays on/off:

- **Observation Heatmap**: Shows what tiles the model focuses on (semi-transparent red overlay)
- **Action Probabilities**: Arrows showing direction probabilities (enabled by default)
- **Value Estimates**: Displays value function estimate (enabled by default)
- **Attention Map**: Shows attention weights if model uses attention
- **Metrics Display**: Live metrics panel in bottom-left (enabled by default)

### Live Metrics Panel

Bottom-left panel shows:

- **Step**: Current game step
- **Reward**: Last step reward
- **Cumulative**: Total accumulated reward
- **Value**: Model's value estimate
- **Action**: Current action (direction, intensity, build)

## Overlay Visualizations

### Action Probability Arrows

White/green arrows emanating from the center of the map:
- **Length**: Proportional to probability
- **Thickness**: Proportional to probability
- **Color**: White = not selected, Green = selected action
- **Opacity**: Based on probability (minimum 20%)
- **Labels**: Percentage near each arrow

**Intensity indicator** shows troop commitment percentage

**Build indicator** shows "🏗️ BUILD" when building a city

### Value Display

Top-left overlay showing:
- **Value**: Model's estimated future return
- **Reward**: Immediate reward from last action
- **Cumulative**: Sum of all rewards so far

### Observation Heatmap (Optional)

Semi-transparent red overlay showing observation intensities:
- **Brighter red**: Higher importance to the model
- **Darker**: Lower importance
- **Transparent**: No observation data

### Attention Map (Optional)

If your model uses attention mechanisms, this shows which parts of the map the model is "paying attention to"

## How It Works

### Data Flow

1. **Model Prediction** (`model_state_extractor.py`)
   - Model predicts action from observation
   - Extract probability distributions
   - Get value function estimate
   - Extract attention weights (if available)

2. **WebSocket Transmission** (`websocket_server.py`)
   - Package model state as JSON
   - Send via WebSocket to client
   - Low latency (~1-5ms)

3. **Client Rendering** (`Main.ts` + `RLOverlayLayer.ts`)
   - Receive model state
   - Update overlay graphics
   - Render with Pixi.js
   - Update metrics display

### Model State Extraction

The `ModelStateExtractor` class extracts internal states from PPO models:

```python
action, details = extractor.predict_with_details(observation)

details = {
    'direction_probs': [0.1, 0.2, ...],  # 9 directions
    'intensity_probs': [0.1, 0.3, ...],   # 5 intensities
    'build_prob': 0.05,
    'value_estimate': 123.45,
    'direction': 'E',
    'intensity': 0.50,
    'build': False,
    'attention_weights': [[...], [...]]   # Optional
}
```

## Comparison with Phase 3

| Feature | Phase 3 | Phase 4 |
|---------|---------|---------|
| **Rendering** | Simple HTML Canvas | Full Pixi.js game client |
| **Updates** | Offline (HTML file) | Real-time (WebSocket) |
| **Model Internals** | None | Full introspection |
| **Interactivity** | Playback only | Play/pause/step/speed |
| **Overlays** | None | Multiple overlay types |
| **File Size** | 50-200MB HTML | Streaming (no file) |
| **Use Case** | Reviewing past games | Real-time debugging |

## Troubleshooting

### "Failed to connect to WebSocket"

Make sure the Python server is running:
```bash
python src/visualize_realtime.py --model model.zip
```

If using custom ports, make sure they match:
```bash
# Python
python src/visualize_realtime.py --model model.zip --ws-port 9000

# Browser URL
http://localhost:3000?ws=ws://localhost:9000
```

### "Module not found: websockets"

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### "npm: command not found"

Install Node.js: https://nodejs.org/

### Client won't start

Try manual startup:
```bash
npm install
npm run dev
```

### Overlay not showing

1. Check that the overlay is enabled in the control panel
2. Make sure the model is actually running (not paused)
3. Check browser console for errors (F12)

### Performance Issues

If visualization is slow:
1. Reduce playback speed
2. Reduce number of bots (`--num-bots`)
3. Disable unused overlays
4. Close other browser tabs

## Development

### Project Structure

```
phase4-implementation/
├── client/                    # TypeScript client
│   ├── index.html            # HTML entry point
│   ├── Main.ts               # Main application
│   ├── RLTypes.ts            # Type definitions
│   ├── RLWebSocketClient.ts  # WebSocket client
│   ├── graphics/
│   │   └── layers/
│   │       └── RLOverlayLayer.ts  # Overlay rendering
│   └── ui/
│       └── RLControlPanel.ts  # Control panel
├── src/                       # Python server
│   ├── visualize_realtime.py # Main entry point
│   ├── websocket_server.py   # WebSocket server
│   └── model_state_extractor.py  # Model introspection
├── package.json              # NPM dependencies
├── tsconfig.json             # TypeScript config
├── vite.config.ts            # Vite config
└── requirements.txt          # Python dependencies
```

### Building for Production

```bash
# Build client
npm run build

# Output will be in dist/
```

### Adding Custom Overlays

1. Create a new layer in `client/graphics/layers/`
2. Extend the `RLOverlayLayer` class
3. Add toggle in `RLControlPanel.ts`
4. Update `RLTypes.ts` with new state types
5. Send new data from Python via WebSocket

### Extending Model State Extraction

Edit `src/model_state_extractor.py`:

```python
def predict_with_details(self, observation):
    # ... existing code ...

    # Add custom extraction
    details['my_custom_metric'] = extract_my_metric(obs)

    return action, details
```

Then update client to visualize the new metric.

## Advanced Usage

### Recording Sessions

While Phase 4 focuses on real-time visualization, you can still record sessions:

```python
# Add to visualize_realtime.py
import json

# During episode
session_data = []
session_data.append({
    'tick': step,
    'state': model_state,
    'reward': reward
})

# After episode
with open('session.json', 'w') as f:
    json.dump(session_data, f)
```

### Custom Visualizations

You can create custom overlay layers by extending `RLOverlayLayer`:

```typescript
class MyCustomLayer {
  update(data: any) {
    // Custom visualization logic
  }

  draw(viewport: Viewport) {
    // Custom rendering
  }
}
```

### Integration with TensorBoard

Export metrics to TensorBoard for analysis:

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/phase4')
writer.add_scalar('Reward', reward, step)
writer.add_scalar('Value', value, step)
```

## Future Enhancements

Potential improvements for Phase 4:

- **Replay Mode**: Save and replay sessions like Phase 3
- **Multi-Agent**: Visualize multiple RL agents simultaneously
- **Heatmap Improvements**: Better observation visualization
- **Model Comparison**: Side-by-side comparison of different models
- **Export**: Export visualizations as video
- **VR/3D**: 3D visualization of the game state

## See Also

- **Phase 3**: Offline HTML visualization (simpler but complete)
- **Base Game**: Original OpenFront.io game client
- **IMPLEMENTATION_ROADMAP.md**: Full project overview

## License

Same as the base OpenFront.io project.

## Support

For issues or questions:
1. Check this README
2. Check browser console (F12) for errors
3. Check Python terminal output
4. Review the code in `client/` and `src/`

Happy visualizing! 🎮🤖
