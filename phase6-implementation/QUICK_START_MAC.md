# Quick Start - Mac Training

## TL;DR

```bash
# Start training (3 environments, MPS GPU)
./restart_training_mac.sh

# Monitor every 10-15 minutes
./monitor_training_mac.sh

# When you see >6 game bridges, restart
./restart_training_mac.sh
```

## What's Included

### Scripts
- ✅ `train_cities_mac.sh` - Start training (3 envs, MPS)
- ✅ `restart_training_mac.sh` - Clean restart with process cleanup
- ✅ `monitor_training_mac.sh` - Check training health

### Documentation
- ✅ `MAC_TRAINING_GUIDE.md` - Complete Mac training guide
- ✅ `ACTION_MASKING_FIX.md` - Action masking improvements
- ✅ `TRAINING_FREEZE_FIX.md` - Process leak diagnosis

### Improvements
- ✅ Action masking fixed (invalid cluster warnings → DEBUG level)
- ✅ Mac-optimized parameters (3 envs, batch 64, steps 1024)
- ✅ Monitoring tools for process leak detection

## Training Setup

**Parameters**:
- Device: MPS (Apple Silicon GPU)
- Environments: 3 (optimal for Mac)
- Batch size: 64
- Rollout steps: 1024
- Expected time: 8-10 days with restarts

**Why 3 environments?**
- 3x faster than 1 environment
- Reasonable memory usage (8-12 GB)
- Requires monitoring (process buildup)

## Critical: Process Monitoring

### The Issue
Game bridge processes accumulate over time:
- Normal: 3 processes (1 per environment)
- Warning: 6 processes (starting to leak)
- Critical: 10+ processes (restart needed)

### Solution
Monitor every **10-15 minutes**:
```bash
./monitor_training_mac.sh
```

When game bridges >6, restart:
```bash
./restart_training_mac.sh
```

## Step-by-Step

### 1. Pre-flight Check
```bash
# Make sure no orphaned processes
pkill -9 -f "tsx.*game_bridge"

# Check system resources
./monitor_training_mac.sh
```

Expected output:
```
[1] Training Processes: ✗ No training running
[2] Game Bridge Processes: ✓ No orphaned bridges
[3] System Memory: Free: X.XX GB
```

### 2. Start Training
```bash
./restart_training_mac.sh
```

You'll see:
```
====================================================================
Phase 6 Training - Clean Restart (Mac)
====================================================================
[1] Cleaning up existing processes...
  ✓ All processes cleaned up
[2] Checking system resources...
  ✓ Sufficient memory available
[3] Starting training...
  Device: Apple Silicon GPU (MPS)
  Environments: 3
====================================================================
```

### 3. Monitor Progress

**Initial check (after 5 minutes)**:
```bash
./monitor_training_mac.sh
```

Expected:
```
[1] Training Processes: ✓ Training running (1 process(es))
[2] Game Bridge Processes: ✓ Normal: 3 bridge processes
[3] System Memory: Free: 6-8 GB
[4] CPU Usage: 250-350% CPU
```

**Regular checks (every 10-15 minutes)**:

Set a timer and check:
- Game bridges should stay around 3-4
- Memory should stay around 6-8 GB free
- CPU should stay 200-400%

### 4. When to Restart

**Restart immediately if you see**:
- ✗ 10+ game bridge processes
- ✗ <2 GB free memory
- ✗ Training log not updated in >15 minutes
- ✗ Progress bar stuck (same step count)

**Consider restarting if you see**:
- ⚠ 6-9 game bridge processes (won't last much longer)
- ⚠ 2-4 GB free memory (getting tight)
- ⚠ CPU usage dropping (might be stuck)

**How to restart**:
```bash
# Just run the restart script
./restart_training_mac.sh
```

It handles everything:
- Kills all processes
- Waits for cleanup
- Starts fresh training

## Monitoring Automation

### Option 1: Manual Timer
Set a repeating 15-minute timer on your phone/computer and check:
```bash
./monitor_training_mac.sh
```

### Option 2: Watch Command
In a separate terminal, run:
```bash
# Update every 2 minutes
watch -n 120 "./monitor_training_mac.sh"
```

### Option 3: Cron Job (Advanced)
Auto-check every 15 minutes and email if issues:
```bash
# Add to crontab
*/15 * * * * cd /path/to/phase6-implementation && ./monitor_training_mac.sh | mail -s "Training Status" you@email.com
```

## Expected Timeline

With 3 environments and periodic restarts:

| Time | Steps | Restarts | Status |
|------|-------|----------|--------|
| 1 hour | ~120K | 0-1 | ✓ Normal |
| 6 hours | ~700K | 3-5 | ✓ Normal |
| 1 day | ~3M | 10-15 | ✓ Normal |
| 3 days | ~9M | 30-40 | ✓ Normal |
| 8 days | ~20M | 80-100 | ✓ Complete! |

**Each restart**:
- Takes ~30 seconds
- Loses ~1-2 minutes of training
- Prevents system crash

## Troubleshooting

### Training won't start
```bash
# Check MPS availability
python3 -c "import torch; print(torch.backends.mps.is_available())"

# Should print: True
```

If False, reinstall PyTorch:
```bash
pip install --upgrade torch torchvision torchaudio
```

### Too many processes stuck
```bash
# Nuclear option - kill everything
pkill -9 -f "python3.*train"
pkill -9 -f "tsx"
pkill -9 node
sleep 3

# Verify all killed
ps aux | grep -E "tsx|train_cities" | grep -v grep

# Start fresh
./restart_training_mac.sh
```

### Out of memory
Reduce environments or batch size:
```bash
# Edit train_cities_mac.sh
# Change: --n-envs 3
# To: --n-envs 2

# Or reduce batch size
# Change: --batch-size 64
# To: --batch-size 32
```

## Pro Tips

1. **Run overnight**: Start training before bed, check in morning
2. **Use tmux**: Detach and reattach without interrupting
3. **Close apps**: Free up RAM by closing browsers, etc.
4. **Prevent sleep**: Use `caffeinate -d` in another terminal
5. **Track restarts**: Keep a note of how many times you restart (should be ~80-100 total)

## Summary

✅ **Scripts ready**: All Mac training scripts created and executable
✅ **Action masking fixed**: No more spam warnings
✅ **Monitoring tools**: Easy to check training health
✅ **Documentation**: Complete guides available

🎯 **To start**:
```bash
./restart_training_mac.sh
```

⏰ **To monitor** (every 10-15 min):
```bash
./monitor_training_mac.sh
```

🔄 **To restart** (when needed):
```bash
./restart_training_mac.sh
```

📖 **For details**:
- `MAC_TRAINING_GUIDE.md` - Full guide
- `ACTION_MASKING_FIX.md` - What we fixed
- `TRAINING_FREEZE_FIX.md` - Why restarts needed

Good luck with training! 🚀
