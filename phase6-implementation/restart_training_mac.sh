#!/bin/bash
# Restart Training Script for Mac - Cleans up and starts fresh training
# Usage: ./restart_training_mac.sh

echo "======================================================================"
echo "Phase 6 Training - Clean Restart (Mac)"
echo "======================================================================"
echo ""

# Step 1: Kill existing processes
echo "[1] Cleaning up existing processes..."
pkill -9 -f "train_cities.py" 2>/dev/null
pkill -9 -f "train_full_game.py" 2>/dev/null
pkill -9 -f "tsx.*game_bridge" 2>/dev/null
pkill -9 -f "npx tsx" 2>/dev/null
sleep 2

REMAINING=$(ps aux | grep -E "tsx|game_bridge|train_cities" | grep -v grep | wc -l | tr -d ' ')
if [ "$REMAINING" -eq 0 ]; then
    echo "  ✓ All processes cleaned up"
else
    echo "  ⚠ Warning: $REMAINING processes still running"
    ps aux | grep -E "tsx|game_bridge|train_cities" | grep -v grep
    echo ""
    echo "  Attempting force cleanup..."
    sleep 1
    pkill -9 -f "tsx.*game_bridge"
fi

echo ""

# Step 2: Check system resources
echo "[2] Checking system resources..."

# Memory check
if command -v vm_stat &> /dev/null; then
    VM_STAT=$(vm_stat)
    PAGE_SIZE=4096
    PAGES_FREE=$(echo "$VM_STAT" | grep "Pages free" | awk '{print $3}' | tr -d '.')
    MEM_FREE_GB=$(echo "scale=2; $PAGES_FREE * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    echo "  Free Memory: ${MEM_FREE_GB} GB"

    if (( $(echo "$MEM_FREE_GB < 4.0" | bc -l) )); then
        echo "  ⚠ Warning: Low free memory. Consider closing other applications."
    else
        echo "  ✓ Sufficient memory available"
    fi
fi

# CPU check
CPU_COUNT=$(sysctl -n hw.ncpu)
echo "  Available CPUs: $CPU_COUNT"

# Check for MPS (Metal) availability
echo "  MPS (Metal): Checking..."
python3 -c "import torch; print('  ✓ MPS available' if torch.backends.mps.is_available() else '  ✗ MPS not available')" 2>/dev/null || echo "  ? Could not check MPS availability"

echo ""

# Step 3: Run training with Mac-optimized parameters
# Default: 8 environments (adjust based on your Mac's RAM)
N_ENVS=${1:-8}

echo "[3] Starting training..."
echo "  Device: Apple Silicon GPU (MPS)"
echo "  Map: australia_256x256"
echo "  Bots: 10"
echo "  Timesteps: 4,000,000 (~7-8 hours at your speed)"
echo "  Environments: $N_ENVS (Phase 3 used 10 successfully)"
echo "  Batch size: 128"
echo "  N steps: 2048"
echo ""
echo "  💡 TIP: Monitor occasionally with './monitor_training_mac.sh'"
echo "  Expected: ~$N_ENVS game bridge processes normally"
echo "  Restart if: >$((N_ENVS * 2)) processes (indicates leak)"
echo ""

echo "======================================================================"
echo "Training will start in 3 seconds..."
echo "Press Ctrl+C to cancel"
echo "======================================================================"
sleep 3

# Start training
python3 train_cities.py \
  --map australia_256x256 \
  --bots 10 \
  --timesteps 4000000 \
  --device mps \
  --n-envs $N_ENVS \
  --batch-size 128 \
  --n-steps 2048 \
  --n-epochs 10 \
  --lr 3e-4 \
  --gamma 0.995 \
  --gae-lambda 0.95 \
  --clip-range 0.2 \
  --ent-coef 0.02

echo ""
echo "======================================================================"
echo "Training completed or interrupted"
echo "======================================================================"

# Check for orphaned processes
REMAINING=$(ps aux | grep -E "tsx|game_bridge" | grep -v grep | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠ Warning: $REMAINING game bridge processes still running"
    echo "Run: pkill -9 -f 'tsx.*game_bridge' to clean up"
fi
