# Game Visualization System

Watch your trained RL agent play OpenFront.io with **actual game map rendering**, just like you'd see in the client!

## 🎮 Features

- **Real Game Map**: See the actual territory colors and map layout
- **Interactive Replay**: Play/pause, step through frames, adjust speed
- **Player Stats**: Track tiles, troops, and gold for all players
- **Episode Recording**: Save replays as HTML files to share and analyze

---

## 🚀 Quick Start

### Basic Usage

```bash
# Watch agent play and save HTML replay
python3 visualize_game.py \
  --model runs/run_20251026_225347/best_model/best_model.zip \
  --save
```

This will:
1. Load your trained model
2. Run one episode
3. Generate an interactive HTML file
4. Open it in your browser to watch!

### Custom Configuration

```bash
python3 visualize_game.py \
  --model path/to/model.zip \
  --config configs/phase1_config.json \
  --output my_replay.html
```

---

## 📊 What You'll See

The HTML visualization shows:

### 1. **Game Map**
- **Your agent** (Red): RL-controlled player
- **AI opponents** (Blue, Green, etc.): Bot players
- **Neutral territory** (Dark gray): Unclaimed tiles
- **Mountains** (Gray): Impassable terrain
- **Cities** (White dot): City tiles

### 2. **Player Stats**
- Tiles owned by each player
- Total troops
- Gold reserves
- Alive/eliminated status

### 3. **Playback Controls**
- ▶️ Play: Auto-advance through frames
- ⏸️ Pause: Stop playback
- ⏮️ Reset: Back to start
- ⏭️ Step: Advance one frame
- Speed slider: 1x to 20x speed
- Frame slider: Jump to any point

### 4. **Episode Summary**
- Final result (Win/Loss)
- Total steps taken
- Map size

---

## 🎬 Example Workflow

### Step 1: Train your model
```bash
python train.py train --config configs/phase1_config.json
```

### Step 2: Visualize best model
```bash
python3 visualize_game.py \
  --model runs/run_YYYYMMDD_HHMMSS/best_model/best_model.zip
```

### Step 3: Open generated HTML
```bash
# Output: visualization_win_20241026_153045.html
open visualization_win_20241026_153045.html
```

### Step 4: Watch and analyze!
- See where the agent expands
- Identify strategic mistakes
- Watch combat dynamics
- Understand why it won/lost

---

## 🔧 How It Works

### Architecture

```
RL Model → OpenFrontIOEnv → game_bridge_visual.ts → Full Game State
                                                      ↓
                                          HTML with Canvas Rendering
```

### Visual Bridge

The `game_bridge_visual.ts` extends the standard bridge to export:
- **Full map state**: Every tile's owner, troops, type
- **Player states**: All players' stats and colors
- **Territory visualization**: Spatial layout for rendering

### Recording Process

1. **Model predicts action** (using standard environment)
2. **Visual bridge captures full state** (all tiles, all players)
3. **Action is executed** in parallel in both systems
4. **Frame is recorded** with complete visual data
5. **HTML is generated** with embedded game states

---

## 📁 Output Files

### HTML Replay Format

The generated HTML files are self-contained:
- No external dependencies
- Pure JavaScript rendering
- Canvas-based tile map
- Works offline
- Easy to share!

Example file: `visualization_win_20241026_153045.html` (~500KB for 1000 steps)

---

## 🎯 Use Cases

### 1. **Debugging Agent Behavior**
- "Why did it lose?"
- "What territories does it prioritize?"
- "Is it playing too passively/aggressively?"

### 2. **Training Analysis**
- Compare early vs. late training episodes
- See strategic evolution over time
- Identify consistent failure modes

### 3. **Demo & Sharing**
- Show your agent to others
- Create training montages
- Document learning progress

### 4. **Research & Papers**
- Visual evidence of learned behaviors
- Side-by-side comparisons
- Illustrative examples

---

## 🛠️ Advanced Options

### Visualize Multiple Episodes

```bash
# Generate 5 replays
for i in {1..5}; do
  python3 visualize_game.py \
    --model runs/latest/best_model.zip \
    --output replay_$i.html
done
```

### Compare Different Models

```bash
# Early training
python3 visualize_game.py \
  --model runs/latest/checkpoints/ppo_10000_steps.zip \
  --output early_training.html

# Late training
python3 visualize_game.py \
  --model runs/latest/best_model.zip \
  --output late_training.html

# Compare side-by-side!
```

### Different Configurations

```bash
# 2-player game (current training)
python3 visualize_game.py --model model.zip --config configs/phase1_config.json

# 6-player game (harder)
# (After updating config)
python3 visualize_game.py --model model.zip --config configs/phase1_6player.json
```

---

## 🐛 Troubleshooting

### "Bridge not initialized"
- Make sure `npx` and `tsx` are installed: `npm install -g tsx`
- Check that `base-game/` directory exists

### "Module not found"
- Run from project root: `cd phase1-implementation`
- Check Python path includes `rl_env/`

### Slow rendering
- Reduce episode length in config (`max_steps`)
- Use faster playback speed in HTML (20x)

### Map looks wrong
- Verify correct map name in config
- Check that map file exists in `base-game/dist/maps/`

---

## 📚 Technical Details

### Tile Rendering

Each tile is rendered as a 4×4 pixel block:
- **Color**: Player owner (or neutral/mountain)
- **Brightness**: Could encode troop count (future)
- **Marker**: White dot for cities

### Performance

- ~1000 steps = ~500KB HTML file
- Renders at 60 FPS even for large maps
- Canvas-based: GPU accelerated

### Data Format

Each frame contains:
```json
{
  "step": 123,
  "action": 2,
  "reward": 156.7,
  "visual_state": {
    "tiles_owned": 65,
    "enemy_tiles": 48,
    "map_width": 50,
    "map_height": 50,
    "tiles": [
      {"x": 0, "y": 0, "owner_id": 1, "troops": 42, "is_city": false},
      ...
    ],
    "players": [
      {"id": 1, "tiles_owned": 65, "color": "#FF0000"},
      ...
    ]
  }
}
```

---

## 🚀 Future Enhancements

Possible improvements:
- [ ] Show troop movements (arrows)
- [ ] Highlight agent's decisions (borders)
- [ ] Add minimap
- [ ] Export to video (mp4)
- [ ] Real-time streaming (websockets)
- [ ] Heatmap overlays (attack probability)

---

## 📖 Related Documentation

- `README.md` - Main project documentation
- `REWARD_STRUCTURE_FIX.md` - Training improvements
- `train.py` - Training script
- `visualize.py` - Simple stats-based visualizer

---

## 🎉 Example

After running:
```bash
python3 visualize_game.py --model runs/latest/best_model.zip
```

You'll see output like:
```
================================================================================
🎬 RECORDING VISUAL EPISODE
================================================================================

Loading model: runs/latest/best_model.zip
Starting visual game bridge...
Visual bridge started!

Resetting game...
Recording episode...
  Step 50: tiles=58, enemy=45
  Step 100: tiles=67, enemy=36
  Step 150: tiles=75, enemy=28
  ...

Episode complete!
  Steps: 847
  Result: ✅ WIN
  Final tiles: 103

✅ HTML visualization saved to: visualization_win_20241026_153045.html
   Open in browser to watch the replay!

================================================================================
✅ VISUALIZATION COMPLETE!
================================================================================
```

Then open `visualization_win_20241026_153045.html` in your browser and watch your agent conquer the map! 🎮
