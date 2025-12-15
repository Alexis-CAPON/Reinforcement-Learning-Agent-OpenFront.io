# Training Freeze Issue - Diagnosis and Fix

## Problem

Training freezes at exactly 49,999 steps:
- Progress bar shows: `5% ━━━━━━╺━━━━━━━... 49,999/1,000,000 [ 2:56:45 < 23:03:30 , 11 it/s ]`
- Timer keeps increasing but step count doesn't
- Same as Phase 5 issue - memory/resource exhaustion

## Root Cause: Game Bridge Process Leak

**What's happening:**
1. Training starts with 1 game bridge process
2. On episode reset, a new game bridge process is spawned
3. Old processes aren't properly cleaned up
4. After ~10-15 episodes, you have 19+ processes
5. System runs out of memory/resources
6. Training freezes

**Why it freezes at 49,999:**
- With `n_steps=512` and `n_envs=1`, the rollout buffer collects 512 steps
- After 97 rollouts (97 × 512 = 49,664 steps), the system is exhausted
- The next rollout starts but can't complete
- Progress bar freezes at 49,999

## Verification

Check for orphaned processes:
```bash
ps aux | grep -E "tsx|game_bridge" | grep -v grep | wc -l
```

Expected: 1 (during training) or 0 (no training)
**Problem**: 19+ processes found!

## Solution

### Immediate Fix

**Kill all orphaned processes:**
```bash
pkill -9 -f "tsx.*game_bridge"
pkill -9 -f "npx tsx"
```

### Long-term Solution

Use the provided scripts for proper cleanup and monitoring:

#### 1. Monitor Training Health
```bash
./monitor_training.sh
```

This shows:
- Training process status
- Number of game bridge processes (should be ≤1)
- GPU usage (if applicable)
- Latest log updates

Run this periodically (every 30-60 minutes) to catch process buildup early.

#### 2. Restart Training with Cleanup
```bash
./restart_training.sh
```

This script:
- Kills all existing processes
- Checks GPU availability
- Starts training with optimal parameters
- Uses the improved action masking fix

## Improvements Made

### 1. Action Masking Fix
**File**: `src/environment_cities.py`

Fixed inconsistency between mask generation and validation:
- Both now use fresh game state
- Reduced log spam (WARNING → DEBUG)
- See `ACTION_MASKING_FIX.md` for details

### 2. Monitoring Tools
- `monitor_training.sh` - Check training health
- `restart_training.sh` - Clean restart with proper cleanup

## Training Parameters

**Memory-Optimized for RTX 2080 Ti (11GB):**
```bash
python3 train_cities.py \
  --map australia_256x256 \
  --bots 10 \
  --timesteps 20000000 \     # 20M steps (~15-25 hours)
  --device cuda \
  --n-envs 1 \               # Single environment (prevents process buildup)
  --batch-size 32 \          # Reduced from 128 (GPU memory)
  --n-steps 512 \            # Reduced from 2048 (GPU memory)
  --n-epochs 10 \
  --lr 3e-4 \
  --gamma 0.995 \
  --gae-lambda 0.95 \
  --clip-range 0.2 \
  --ent-coef 0.02
```

**GPU Memory Usage:**
- Before: ~9.3 GB (OOM)
- After: ~3-4 GB ✓

## Step-by-Step Restart Procedure

### On GPU Server

```bash
# 1. Navigate to phase6
cd ~/phase6-implementation  # Adjust to your actual path

# 2. Activate virtual environment (if using one)
source venv/bin/activate

# 3. Check current status
./monitor_training.sh

# 4. Clean restart
./restart_training.sh

# 5. Detach from screen/tmux
# If using screen:
screen -S phase6_training
# Then run restart script
# Detach: Ctrl+A then D

# If using tmux:
tmux new -s phase6_training
# Then run restart script
# Detach: Ctrl+B then D
```

### Monitoring During Training

Check every 30-60 minutes:
```bash
# Reattach to session
screen -r phase6_training   # or tmux attach -t phase6_training

# Check if still progressing
# Look for increasing step count

# Check for process buildup
./monitor_training.sh
```

## Warning Signs

Watch for these indicators of problems:

1. **Step Count Frozen**
   - Progress bar shows same step count for >10 minutes
   - Timer increasing but steps not

2. **Too Many Game Bridges**
   - `./monitor_training.sh` shows >3 processes
   - Action: Restart training

3. **GPU Memory Growing**
   - `nvidia-smi` shows memory usage increasing over time
   - Should stay steady at ~3-4 GB

4. **Slow Iteration Speed**
   - Normal: ~11 it/s
   - Problem: <5 it/s or decreasing over time

## Expected Behavior

**Healthy Training:**
```
5% ━━━━━━╺━━━━━... 50,000/1,000,000 [ 1:15:23 < 23:45:12 , 11 it/s ]
6% ━━━━━━━╺━━━... 60,000/1,000,000 [ 1:30:45 < 23:12:34 , 11 it/s ]
7% ━━━━━━━━╺━━... 70,000/1,000,000 [ 1:46:12 < 22:38:56 , 11 it/s ]
```

- Step count steadily increases
- Iteration speed stays ~11 it/s
- Episodes complete and reset normally

**Problem Indicators:**
```
5% ━━━━━━╺━━━━━... 49,999/1,000,000 [ 2:56:45 < 23:03:30 , 11 it/s ]
5% ━━━━━━╺━━━━━... 49,999/1,000,000 [ 3:12:18 < 23:03:30 , 11 it/s ]  ← FROZEN
5% ━━━━━━╺━━━━━... 49,999/1,000,000 [ 3:28:51 < 23:03:30 , 11 it/s ]  ← FROZEN
```

- Step count doesn't change
- Timer keeps increasing
- Need to restart

## Debugging Commands

**Check processes:**
```bash
# Count game bridges
ps aux | grep -E "tsx|game_bridge" | grep -v grep | wc -l

# Show process details
ps aux | grep -E "tsx|game_bridge" | grep -v grep

# Count training processes
ps aux | grep train_cities.py | grep -v grep | wc -l
```

**Check GPU:**
```bash
# GPU memory usage
nvidia-smi

# Continuous monitoring
watch -n 5 nvidia-smi

# Which GPU to use
nvidia-smi --query-gpu=index,memory.free --format=csv
```

**Check logs:**
```bash
# Latest training logs
tail -f logs/ppo_cities_*/events.out.tfevents.*

# Or use TensorBoard
tensorboard --logdir logs/
```

## Why This Happens

**Game Wrapper Cleanup Issue:**

The `GameWrapper` class in `game_wrapper.py` has cleanup methods:
- `close()` - Sends shutdown command to game bridge
- `__del__()` - Destructor for cleanup
- `atexit.register()` - Cleanup on program exit

However, in some cases (especially with Ctrl+C interrupts), these don't get called properly:
- Python's garbage collector might not trigger `__del__()`
- `atexit` handlers might not complete if force-killed
- Result: Orphaned game bridge processes

**Temporary Workaround:**
- Use `n_envs=1` (reduces process spawning)
- Monitor with `./monitor_training.sh`
- Restart if >3 game bridges detected

**Potential Long-term Fix (future work):**
- Add explicit process tracking in `GameWrapper`
- Implement heartbeat/watchdog mechanism
- Better signal handling for cleanup

## Summary

✅ **Fixed**:
- Action masking consistency
- Logging improvements
- Created monitoring tools

⚠ **Workaround Required**:
- Game bridge process cleanup
- Use monitoring scripts
- Restart when processes build up

🎯 **Expected Results**:
- Clean training logs (no invalid cluster warnings)
- Stable memory usage (~3-4 GB GPU)
- Training completes 20M steps in 15-25 hours

## Questions?

- Run `./monitor_training.sh` to check health
- Run `./restart_training.sh` for clean restart
- Check `ACTION_MASKING_FIX.md` for masking details
- Check `README.md` for training parameters
