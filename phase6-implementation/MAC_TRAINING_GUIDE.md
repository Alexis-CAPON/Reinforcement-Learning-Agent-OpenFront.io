# Mac Training Guide - Phase 6

## Overview

Training Phase 6 on Mac with Apple Silicon (M1/M2/M3) using MPS (Metal Performance Shaders) GPU acceleration.

**Important**: The game bridge process leak issue affects Mac too! You'll need to monitor process buildup closely.

## Quick Start

### 1. Clean Any Existing Processes
```bash
pkill -9 -f "tsx.*game_bridge"
pkill -9 -f "train_cities.py"
```

### 2. Start Training
```bash
./train_cities_mac.sh
```

Or use the restart script with automatic cleanup:
```bash
./restart_training_mac.sh
```

### 3. Monitor Training (Every 10-15 minutes)
```bash
./monitor_training_mac.sh
```

## Training Parameters (Mac-Optimized)

```bash
python3 train_cities.py \
  --map australia_256x256 \
  --bots 10 \
  --timesteps 20000000 \
  --device mps \            # Apple Silicon GPU
  --n-envs 3 \              # 3 parallel environments (faster than 1)
  --batch-size 64 \         # Balanced for unified memory
  --n-steps 1024 \          # Moderate rollout buffer
  --n-epochs 10 \
  --lr 3e-4 \
  --gamma 0.995 \
  --gae-lambda 0.95 \
  --clip-range 0.2 \
  --ent-coef 0.02
```

### Why 3 Environments?

| Environments | Speed | Process Risk | Memory | Recommended For |
|--------------|-------|--------------|--------|-----------------|
| 1 | Slowest | Low | Lowest | GPU server (safer) |
| 3 | **Fast** | **Medium** | **Medium** | **Mac (balanced)** |
| 5+ | Fastest | High | High | Not recommended |

**3 environments is optimal for Mac**:
- ✓ 3x faster data collection than 1 environment
- ✓ Reasonable memory usage (~8-12 GB)
- ⚠ Requires monitoring for process buildup
- ⚠ Should check every 10-15 minutes

## Process Buildup Warning

### The Problem

With 3 environments, you'll have **3 game bridge processes** normally:
```
Environment 0 → Game Bridge Process 1
Environment 1 → Game Bridge Process 2
Environment 2 → Game Bridge Process 3
```

**Issue**: On episode reset, new processes spawn but old ones don't always die.

### Normal vs Problem

**Normal** (healthy training):
```
$ ./monitor_training_mac.sh
[2] Game Bridge Processes:
  ✓ Normal: 3 bridge processes (expected: 3 for 3 envs)
```

**Problem** (process leak detected):
```
$ ./monitor_training_mac.sh
[2] Game Bridge Processes:
  ✗ ALERT: 12 bridge processes! Memory leak detected!
    Expected: ~3 for 3 environments
    Run: pkill -9 -f 'tsx.*game_bridge' to clean up
```

### Timeline of Process Buildup

With 3 environments, process buildup happens **3x faster** than with 1 environment:

| Time | Processes | Status | Action |
|------|-----------|--------|--------|
| 0 min | 3 | ✓ Normal | Continue |
| 15 min | 3-6 | ✓ OK | Continue |
| 30 min | 6-9 | ⚠ Warning | Monitor closely |
| 45 min | 9-12 | ⚠ High | Consider restarting |
| 60 min | 12+ | ✗ Critical | **RESTART NOW** |

**Rule of thumb**: If you have **>6 game bridges** (2x expected), restart training.

## Monitoring Checklist

Run `./monitor_training_mac.sh` every **10-15 minutes** and check:

### 1. Game Bridge Count
- ✓ **3 processes**: Perfect
- ⚠ **4-6 processes**: OK, but monitor
- ⚠ **7-9 processes**: Warning, restart soon
- ✗ **10+ processes**: Restart immediately

### 2. Memory Usage
- ✓ **>4 GB free**: Good
- ⚠ **2-4 GB free**: OK, but monitor
- ✗ **<2 GB free**: Restart needed

### 3. CPU Usage
- ✓ **200-400%**: Normal (3 envs × ~100% each + training)
- ⚠ **>500%**: High, check for extra processes
- ✗ **<100%**: Training might be stuck

### 4. Training Progress
- ✓ **Log updated <5 min ago**: Healthy
- ⚠ **Log updated 5-15 min ago**: Might be between updates
- ✗ **Log updated >15 min ago**: Likely stuck, restart

## Manual Monitoring (Alternative)

If you prefer manual checks:

```bash
# Count game bridge processes
ps aux | grep -E "tsx.*game_bridge" | grep -v grep | wc -l

# Show process details
ps aux | grep -E "tsx|train_cities" | grep -v grep

# Watch memory
vm_stat | grep "Pages free"

# Monitor in real-time (Ctrl+C to exit)
watch -n 10 "ps aux | grep -E 'tsx|train_cities' | grep -v grep | wc -l"
```

## When to Restart Training

### Automatic Restart (Recommended)

**Symptoms**:
- >6 game bridge processes
- <2 GB free memory
- Training stuck (no progress for >15 minutes)

**Solution**:
```bash
./restart_training_mac.sh
```

This will:
1. Kill all training and bridge processes
2. Wait 2 seconds for cleanup
3. Check system resources
4. Start fresh training

### Manual Restart

```bash
# 1. Stop training (if running in foreground)
# Press Ctrl+C

# 2. Kill all processes
pkill -9 -f "train_cities.py"
pkill -9 -f "tsx.*game_bridge"

# 3. Wait a moment
sleep 2

# 4. Verify cleanup
ps aux | grep -E "tsx|train_cities" | grep -v grep

# 5. Start training
./train_cities_mac.sh
```

## Expected Training Time

With 3 environments on Mac:

| Metric | Value |
|--------|-------|
| Total steps | 20,000,000 |
| Steps per second | ~33 (11 it/s × 3 envs) |
| **Estimated time** | **~170 hours (7 days)** |
| With restarts | ~8-9 days |

**Reality check**:
- You'll need to restart every ~1-2 hours due to process buildup
- Each restart loses a few minutes
- Budget 8-10 days for complete training
- Or train overnight and restart in morning

## Training in Background

### Using nohup

```bash
# Start training in background
nohup ./train_cities_mac.sh > training.log 2>&1 &

# Check progress
tail -f training.log

# Monitor processes
./monitor_training_mac.sh

# Stop training
pkill -f "train_cities.py"
```

### Using tmux (Recommended)

```bash
# Install tmux if needed
brew install tmux

# Start tmux session
tmux new -s phase6_training

# Inside tmux, start training
./train_cities_mac.sh

# Detach from tmux
# Press: Ctrl+B then D

# Reattach later
tmux attach -t phase6_training

# Kill session
tmux kill-session -t phase6_training
```

## Troubleshooting

### Training Not Starting

**Error**: `RuntimeError: MPS backend is not available`

**Solution**:
```bash
# Check MPS availability
python3 -c "import torch; print(torch.backends.mps.is_available())"

# If False, check PyTorch version
pip list | grep torch

# Reinstall if needed
pip install --upgrade torch torchvision torchaudio
```

### Out of Memory

**Error**: `RuntimeError: MPS out of memory`

**Solutions**:
1. Reduce environments: `--n-envs 2`
2. Reduce batch size: `--batch-size 32`
3. Reduce rollout buffer: `--n-steps 512`
4. Close other applications

### Training Freezes

**Symptom**: Progress bar stuck, no step count increase

**Diagnosis**:
```bash
./monitor_training_mac.sh
```

**Solution**: If >6 game bridges, restart:
```bash
./restart_training_mac.sh
```

### Game Bridge Won't Die

**Symptom**: `pkill` doesn't kill processes

**Solution**: Force kill with PID:
```bash
# Find PIDs
ps aux | grep "tsx.*game_bridge" | grep -v grep

# Kill each PID
kill -9 <PID>

# Or use killall
killall -9 node
killall -9 tsx
```

## Optimization Tips

### 1. Close Other Apps
Free up RAM and CPU:
- Close browsers (Safari, Chrome)
- Close Slack, Discord, etc.
- Quit unused applications

### 2. Prevent Sleep
Keep Mac awake during training:
```bash
# Prevent sleep (run in separate terminal)
caffeinate -d

# Or use GUI: System Preferences → Energy Saver → Prevent sleep
```

### 3. Monitor Temperature
Mac might throttle if too hot:
```bash
# Install stats
brew install stats

# Or check manually
sudo powermetrics --samplers smc | grep -i "CPU die temperature"
```

### 4. Adjust Environments
If unstable, reduce to 2 environments:
```bash
# Edit train_cities_mac.sh
# Change: --n-envs 3
# To: --n-envs 2
```

## Expected Performance

### With 3 Environments

**Healthy metrics**:
- Iteration speed: ~11 it/s
- CPU usage: 200-400%
- Memory: 8-12 GB used
- Game bridges: 3 processes
- GPU (MPS): Active

**After 1 hour** (if no issues):
- Steps: ~120,000
- Episodes: ~200-300
- Memory: Still stable
- Processes: 3-6 bridges

**After 2 hours** (approaching limit):
- Steps: ~240,000
- Episodes: ~400-600
- Memory: Increasing
- Processes: **6-12 bridges** ← Time to restart!

## Summary

✅ **Setup**:
- Use 3 environments for Mac (optimal speed/stability)
- Training scripts ready: `train_cities_mac.sh`, `restart_training_mac.sh`
- Monitoring ready: `monitor_training_mac.sh`

⚠ **Critical Monitoring**:
- Check every 10-15 minutes
- Restart when >6 game bridges
- Budget 8-10 days for 20M steps

🎯 **Expected Results**:
- Faster than 1 environment (3x data collection)
- Requires active monitoring
- Will need periodic restarts
- Full training: ~8-10 days with restarts

## Questions?

- Run `./monitor_training_mac.sh` to check current status
- Run `./restart_training_mac.sh` for clean restart
- See `TRAINING_FREEZE_FIX.md` for detailed process leak info
- See `ACTION_MASKING_FIX.md` for action masking improvements
