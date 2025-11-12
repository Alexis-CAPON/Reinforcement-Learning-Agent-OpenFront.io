# Phase 4 Quick Start Guide

Get started with the Phase 4 visualizer in 3 easy steps!

## Prerequisites

- Python 3.8+ with pip
- Node.js 18+ with npm
- A trained model from Phase 3

## Step 1: Install Dependencies

```bash
cd phase4-implementation

# Install Python packages
pip install -r requirements.txt

# Install Node packages
npm install
```

## Step 2: Run the Visualizer

```bash
# Replace with your actual model path
python src/visualize_realtime.py --model ../phase3-implementation/runs/run_20250103_120000/openfront_final.zip
```

This will:
1. ✅ Start the WebSocket server
2. ✅ Start the dev server
3. ✅ Open your browser automatically
4. ✅ Begin visualization!

## Step 3: Use the Controls

### Playback
- **Play**: Resume game
- **Pause**: Pause game
- **Step**: Advance one frame
- **Speed slider**: Adjust speed (1x-10x)

### Overlays
Toggle different visualizations:
- ✅ **Action Probabilities** - Arrows showing where the model wants to go
- ✅ **Value Estimates** - Model's value prediction
- ⬜ **Observation Heatmap** - What the model "sees"
- ⬜ **Attention Map** - Where the model focuses (if applicable)

### Metrics Panel (bottom-left)
Watch live metrics:
- Step count
- Current reward
- Cumulative reward
- Value estimate
- Current action

## Common Issues

**"Module not found: websockets"**
```bash
pip install websockets
```

**"npm: command not found"**
- Install Node.js from https://nodejs.org/

**Client won't open**
- Manually navigate to http://localhost:3000

**Can't find model**
- Check the path is correct
- Use absolute path if needed

## What You'll See

1. **Connection Status** (top-left): Shows if connected to Python server
2. **Control Panel** (top-right): Playback and overlay controls
3. **Game Canvas** (center): The game map with overlays
4. **Metrics Panel** (bottom-left): Live statistics
5. **Action Arrows** (overlay): Direction probabilities

## Next Steps

- Try different speeds with the speed slider
- Toggle overlays to see different visualizations
- Use pause/step to analyze specific decisions
- Try with different numbers of bots (`--num-bots`)

## Full Documentation

See [README.md](README.md) for complete documentation.

---

**Happy visualizing!** 🎮🤖
