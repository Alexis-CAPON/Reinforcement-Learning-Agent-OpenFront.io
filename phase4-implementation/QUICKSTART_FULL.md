# Phase 4 Quick Start - Full Base Game Integration

Get the **full OpenFront.io client** with RL overlays in 3 steps!

**Your RL model plays the REAL game**: Full terrain (mountains, coastlines), all mechanics (gold, cities, alliances), real AI opponents - not a simulation!

## Step 1: Install Dependencies

```bash
# Install Python dependencies
cd phase4-implementation
pip install -r requirements.txt

# Install base game dependencies
cd ../base-game
npm install
```

## Step 2: Start the Python Bridge

```bash
cd phase4-implementation
python src/visualize_realtime.py \
  --model ../phase3-implementation/runs/run_20251102_025235/checkpoints/single_phase_final.zip \
  --map australia \
  --crop center-512x384
```

This will:
- Load the **Australia map** (2000×1500) with realistic terrain
- Crop a **512×384 centered region** from the middle (focused view)
- Show mountains, coastlines, and relief features

You'll see:
```
================================================================================
Phase 4 Real-Time Visualizer Started!
================================================================================
WebSocket server: ws://localhost:8765
Open the client in your browser to start visualization
Using centered crop: 512x384 at (744, 558)
Map: australia
================================================================================
```

## Step 3: Open the Game Client

### Option A: Direct File (Simplest)

Open in your browser:
```
file:///Users/alexis/Dev/Lehigh/projects/openfrontio-rl/base-game/src/client/rl-index.html?ws=ws://localhost:8765
```

### Option B: Dev Server (Better for development)

```bash
# In another terminal
cd base-game
npm run dev
```

Then open:
```
http://localhost:8080/rl-index.html?ws=ws://localhost:8765
```

## What You'll See

✅ **Full game map** with professional graphics
✅ **All players** with their territories
✅ **Buildings** (cities, ports, factories)
✅ **Units** (infantry, boats, nukes)
✅ **Leaderboard** showing live rankings
✅ **RL Overlays**:
   - Action probability arrows
   - Value function estimates
   - Reward tracking
   - Current action display

✅ **Controls panel**:
   - Play/Pause/Step buttons
   - Overlay toggle
   - Speed control (coming soon)

## Controls

**Top-right panel:**
- ▶️ Play - Resume game
- ⏸️ Pause - Pause game
- ⏭️ Step - Advance one frame
- ⏮️ Reset - Restart episode
- ☑️ Show Model Overlay - Toggle RL visualization

**Game UI:**
- View leaderboard
- See player stats
- Watch alliances form
- Observe gold collection
- See building construction

## Map and Cropping Options

**Available Maps:**
- `australia` (2000×1500) - Realistic Australia with coastlines and mountains (default)
- `world` (2000×1000) - World map
- `europe` (1500×1200) - Europe map
- `plains` - Simple flat map

**Crop Formats:**
- `center-WxH` - Auto-centered crop (e.g., `--crop center-512x384`)
- `x,y,w,h` - Custom coordinates (e.g., `--crop 744,558,512,384`)
- `none` - No cropping, use full map

**Examples:**
```bash
# Default: Australia with centered 512×384 crop
python src/visualize_realtime.py --model path/to/model.zip

# Larger centered crop
python src/visualize_realtime.py --model path/to/model.zip --crop center-800x600

# Custom crop region
python src/visualize_realtime.py --model path/to/model.zip --crop 500,400,640,480

# Full map, no cropping
python src/visualize_realtime.py --model path/to/model.zip --crop none

# Different map
python src/visualize_realtime.py --model path/to/model.zip --map world --crop center-512x384
```

## Troubleshooting

**"WebSocket connection failed"**
- Make sure Python server is running
- Check the WebSocket URL matches (default: ws://localhost:8765)

**"Cannot load rl-index.html"**
- Use absolute path or run from dev server
- Check file exists: `base-game/src/client/rl-index.html`

**"Black screen"**
- Check browser console for errors
- Make sure base-game dependencies are installed (`npm install`)
- Verify WebSocket is connected (check console logs)

**"No model overlay showing"**
- Make sure "Show Model Overlay" checkbox is checked
- Check that model state is being received (console should show updates)

## Next Steps

**Want to customize?**
- Edit `base-game/src/client/graphics/layers/RLOverlayLayer.ts`
- Modify arrow colors, sizes, metrics displayed

**Want more features?**
- Add observation heatmap
- Add attention visualization
- Add value map overlay
- See `USING_BASE_GAME.md` for details

**Ready for production?**
```bash
cd base-game
npm run build
# Serve dist/ folder with any static file server
```

---

**That's it! You now have the full game client with RL visualization!** 🎉

All game features (alliances, gold, nukes, boats, buildings) work automatically because we're using the complete base game.
