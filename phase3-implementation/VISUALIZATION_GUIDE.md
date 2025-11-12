# Visualization Guide - Watch Your Agent Play!

This guide explains how to visualize your trained RL agent playing OpenFront.io.

## Quick Start

### 1. Watch Your Model Play (HTML Game Visualization) ⭐

**Best option - see the actual game map rendered!**

```bash
# Create interactive HTML visualization
python src/visualize_game.py --model runs/run_TIMESTAMP/openfront_final.zip --num-bots 10

# Output: visualizations/battle_royale_RESULT_TIMESTAMP.html
# Open in your browser to watch!
```

**Features:**
- Full game map rendering with Canvas
- Live leaderboard showing all players
- Interactive controls (play, pause, speed control)
- Frame-by-frame playback
- Territory colors for all players
- Cities and mountains displayed

### 2. Watch Your Model Play (Terminal Output)

```bash
# Play 1 game with 10 bots
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip

# Play 5 games with 25 bots
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip --num-games 5 --num-bots 25

# Slow-motion playback (0.1 second per step)
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip --step-delay 0.1
```

**Output Example:**
```
================================================================================
🎮 GAME START - 10 Opponents
================================================================================
[Step     0] Territory:   0.5% | Population:   5000 | Rank:  5/11 | Action: E   @100%     | Reward:  +0.12
[Step   100] Territory:   3.2% | Population:  12450 | Rank:  3/11 | Action: NE  @ 50%     | Reward:  +2.45
[Step   200] Territory:   8.7% | Population:  28900 | Rank:  2/11 | Action: S   @ 75% 🏗️  | Reward:  +5.31
...

================================================================================
📊 GAME OVER
================================================================================
Result: 🏆 VICTORY
Survival Time: 4,523 steps
Total Reward: +342.56
Max Territory: 82.3%
Max Population: 45,678
Best Rank: 1/11
Final Rank: 1/11

Action Distribution:
  E   :  1234 ( 27.3%)
  N   :   987 ( 21.8%)
  NE  :   765 ( 16.9%)
  S   :   654 ( 14.5%)
  ...
```

### 2. Save and Replay Terminal Games

```bash
# Play and save replay data
python src/play_game.py runs/run_TIMESTAMP/openfront_final.zip --save-replays

# Replays saved to: replays/replay_TIMESTAMP.json
```

### 3. Visualize Terminal Replays

```bash
# Summary statistics
python src/visualize_replay.py replays/replay_TIMESTAMP.json --mode summary

# Create graphs (requires matplotlib)
python src/visualize_replay.py replays/replay_TIMESTAMP.json --mode graphs

# Frame-by-frame playback
python src/visualize_replay.py replays/replay_TIMESTAMP.json --mode play

# All visualizations
python src/visualize_replay.py replays/replay_TIMESTAMP.json --mode all
```

## Visualization Modes

### HTML Game Visualization (`visualize_game.py`) ⭐ RECOMMENDED

**Features:**
- Full game map rendered with HTML Canvas
- See exactly what the agent sees
- Interactive playback controls
- Live leaderboard showing all players
- Frame-by-frame navigation
- Speed control (1x-20x)

**How it works:**
1. Loads your trained model
2. Plays a full game using the visual game bridge
3. Records every Nth frame (map state + all players)
4. Generates an interactive HTML file
5. Open in browser to watch!

**Use Cases:**
- Demo/presentations
- Understanding agent strategy
- Debugging behavior
- Creating videos/screenshots
- Analyzing territory control patterns

**Command Options:**
```bash
python src/visualize_game.py [OPTIONS]

Required:
  --model PATH            Path to trained model (.zip)

Options:
  --num-bots N            Number of bot opponents (default: 10)
  --frame-skip N          Record every Nth frame (default: 50)
  --output PATH           Custom output HTML path
```

**Examples:**
```bash
# Quick visualization (10 bots)
python src/visualize_game.py --model model.zip --num-bots 10

# Medium difficulty (25 bots)
python src/visualize_game.py --model model.zip --num-bots 25 --frame-skip 25

# Full battle royale (50 bots)
python src/visualize_game.py --model model.zip --num-bots 50 --frame-skip 100

# Custom output location
python src/visualize_game.py --model model.zip --output my_replay.html
```

**HTML Features:**
- **Map Canvas**: Shows territories with player colors
- **Leaderboard**: Real-time rankings by tiles owned
- **Stats Cards**: Territory %, tiles, troops, rank, action
- **Playback Controls**:
  - Play/Pause
  - Reset (go to start)
  - Step (advance one frame)
  - Speed controls (1x-20x)
  - Frame slider (jump to any frame)
- **Player Colors**: Distinct colors for up to 40 players
- **Terrain**: Mountains (gray), neutral (dark), player territories (colored)
- **Cities**: Marked with white centers

**Performance Tips:**
- Use `--frame-skip 50` for faster recording and smaller files
- For 50 bots, use `--frame-skip 100` to keep file size manageable
- HTML files can be 50-200MB for long games (normal)
- Works offline - no internet needed to view

### Terminal Play Mode (`play_game.py`)

**Features:**
- Real-time statistics every 100 steps
- Action explanations (direction, intensity, build)
- Final game summary with action distribution
- Optional replay saving

**Use Cases:**
- Quick model testing
- Performance evaluation
- Behavior analysis
- Demo/presentation

**Command Options:**
```bash
python src/play_game.py MODEL_PATH [OPTIONS]

Required:
  MODEL_PATH              Path to trained model (.zip)

Options:
  --num-games N           Number of games to play (default: 1)
  --num-bots N            Number of bot opponents (default: 10)
  --step-delay SECONDS    Delay between steps (default: 0.0)
  --save-replays          Save replay JSON files
```

**Example - Test Different Difficulties:**
```bash
# Easy (5 bots)
python src/play_game.py model.zip --num-bots 5 --num-games 10

# Medium (25 bots)
python src/play_game.py model.zip --num-bots 25 --num-games 10

# Hard (50 bots)
python src/play_game.py model.zip --num-bots 50 --num-games 10
```

### Replay Visualization (`visualize_replay.py`)

**Features:**
- Summary statistics with win/loss
- Territory, population, rank graphs (matplotlib)
- Frame-by-frame ASCII playback
- Action distribution analysis

**Use Cases:**
- Analyze specific games
- Create presentation graphics
- Debug agent behavior
- Compare different models

**Command Options:**
```bash
python src/visualize_replay.py REPLAY_PATH [OPTIONS]

Required:
  REPLAY_PATH            Path to replay JSON file

Options:
  --mode MODE            Visualization mode:
                         - summary: Print statistics
                         - graphs: Create matplotlib graphs
                         - play: Frame-by-frame playback
                         - all: All modes (default)
  --frame-delay SECONDS  Delay in play mode (default: 0.1)
```

**Example - Create Publication Graphics:**
```bash
# Generate high-quality graphs
python src/visualize_replay.py replays/replay_best_game.json --mode graphs

# Output: replays/replay_TIMESTAMP_stats.png
```

## Understanding the Output

### Live Statistics

**Territory Bar:**
```
Territory: [████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 32.5%
```
- Filled blocks (█): Your territory
- Empty blocks (░): Unclaimed/enemy territory
- Percentage: Your control of the map

**Population:**
- Current troop count
- Higher = more attack/defense capacity
- Optimal: 40-50% of max for growth

**Rank:**
- Your position among all players
- Lower is better (Rank 1 = first place)
- Format: `Rank: 2/11` (you're 2nd out of 11 total)

**Actions:**
- Direction: N, NE, E, SE, S, SW, W, NW, WAIT
- Intensity: 20%, 35%, 50%, 75%, 100% (troops to commit)
- Build: 🏗️ indicates city construction

### Replay Graphs

**Territory Graph:**
- Shows % of map controlled over time
- Green dashed line: Victory threshold (80%)
- Rising = expanding, falling = losing ground

**Population Graph:**
- Total troop count over time
- Peaks = successful expansion
- Drops = heavy attacks

**Rank Graph:**
- Your position vs opponents
- Y-axis inverted (lower is better)
- Staying low = good performance

**Reward Graph:**
- Per-step reward (thin line)
- Cumulative reward (thick cyan line)
- Positive = learning progress

## Advanced Usage

### Compare Multiple Models

```bash
# Test baseline model
python src/play_game.py runs/run_v1/openfront_final.zip --num-games 20 --num-bots 25 > results_v1.txt

# Test improved model
python src/play_game.py runs/run_v2/openfront_final.zip --num-games 20 --num-bots 25 > results_v2.txt

# Compare win rates
grep "Wins:" results_v1.txt
grep "Wins:" results_v2.txt
```

### Create Video from Replays

If you want to create videos:

1. **Record frames:**
```bash
# Play with delay and screen record
python src/play_game.py model.zip --step-delay 0.05 --save-replays
```

2. **Use screen recording software:**
- macOS: QuickTime Player (Cmd+Shift+5)
- Linux: OBS Studio, SimpleScreenRecorder
- Windows: OBS Studio, Windows Game Bar

3. **Or create animation with matplotlib:**
```python
# Add to visualize_replay.py for custom animations
import matplotlib.animation as animation

# Create animated territory map
fig, ax = plt.subplots()
# ... animation code ...
anim = animation.FuncAnimation(fig, update_frame, frames=len(frames))
anim.save('replay.mp4', writer='ffmpeg', fps=10)
```

### Export to TensorBoard

To visualize replays in TensorBoard:

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/replay_viz')

for step, frame in enumerate(replay_data['frames']):
    writer.add_scalar('Territory', frame['territory_pct'], step)
    writer.add_scalar('Population', frame['population'], step)
    writer.add_scalar('Rank', frame['rank'], step)
    writer.add_scalar('Reward', frame['reward'], step)

writer.close()
```

Then view with:
```bash
tensorboard --logdir=runs/replay_viz
```

## Connecting to Real Game UI

The OpenFront.io game has a web interface. To connect your trained agent:

### Option 1: Local Game Server

1. **Build and run the base game:**
```bash
cd ../base-game
npm install
npm run build
npm run start
```

2. **Connect agent to server:**
```bash
# Modify game_wrapper.py to connect via WebSocket
# (See WEBSOCKET_INTEGRATION.md for details)
```

### Option 2: Headless Visualization

For faster visualization without the browser:

```bash
# The current game_bridge runs headless by default
# It's optimized for training speed, not visual rendering
```

## Performance Tips

### Fast Batch Testing

```bash
# Test 100 games quickly (no delay, no replays)
python src/play_game.py model.zip --num-games 100 --num-bots 25 > results.txt

# Extract statistics
grep "Avg" results.txt
```

### Memory-Efficient Replays

```bash
# Replays can get large for long games
# Save only important games:

# Play until first victory, then save
python src/play_game.py model.zip --num-games 1 --save-replays

# Or save only every Nth frame (modify play_game.py):
if step % 10 == 0 and self.save_replay:
    self.replay_data.append(...)
```

## Troubleshooting

### "Module not found: matplotlib"

For graphs, install matplotlib:
```bash
pip install matplotlib
```

Or use summary/play modes only:
```bash
python src/visualize_replay.py replay.json --mode summary
```

### "Game crashed during visualization"

The game bridge might timeout on long games:
```bash
# Increase timeout in game_wrapper.py:
self.process = subprocess.Popen(
    [...],
    timeout=600  # 10 minutes instead of 5
)
```

### "Model prediction is slow"

Ensure you're using the right device:
```bash
# Check device in model
python -c "from stable_baselines3 import PPO; m = PPO.load('model.zip'); print(m.device)"

# Should show: mps (M4 Max) or cuda (NVIDIA)
```

## Example Workflow

**Complete model evaluation pipeline:**

```bash
# 1. Train model
python src/train.py --device mps --n-envs 12 --total-timesteps 50000 --no-curriculum --num-bots 10

# 2. Find the saved model
MODEL_PATH="runs/run_TIMESTAMP/checkpoints/single_phase_final.zip"

# 3. Quick test (1 game)
python src/play_game.py $MODEL_PATH --num-bots 10

# 4. Thorough evaluation (20 games)
python src/play_game.py $MODEL_PATH --num-games 20 --num-bots 10 --save-replays

# 5. Analyze best replay
BEST_REPLAY=$(ls -t replays/*.json | head -1)
python src/visualize_replay.py $BEST_REPLAY --mode all

# 6. Test on harder difficulty
python src/play_game.py $MODEL_PATH --num-games 10 --num-bots 25

# 7. Generate comparison report
echo "=== Model Performance Report ===" > report.txt
echo "" >> report.txt
echo "10 bots:" >> report.txt
python src/play_game.py $MODEL_PATH --num-games 20 --num-bots 10 | grep "Avg" >> report.txt
echo "" >> report.txt
echo "25 bots:" >> report.txt
python src/play_game.py $MODEL_PATH --num-games 20 --num-bots 25 | grep "Avg" >> report.txt
cat report.txt
```

## Summary

**Quick Reference:**

| Task | Command |
|------|---------|
| Watch 1 game | `python src/play_game.py model.zip` |
| Test 10 games | `python src/play_game.py model.zip --num-games 10` |
| Save replays | `python src/play_game.py model.zip --save-replays` |
| View replay stats | `python src/visualize_replay.py replay.json --mode summary` |
| Create graphs | `python src/visualize_replay.py replay.json --mode graphs` |
| Watch replay | `python src/visualize_replay.py replay.json --mode play` |

**Next Steps:**
- Create custom visualizations by modifying the scripts
- Integrate with TensorBoard for training+evaluation analysis
- Connect to the web UI for full visual experience
- Export replays to video for presentations
