#!/bin/bash
# Restart Training Script - Cleans up and starts fresh training
# Usage: ./restart_training.sh

echo "======================================================================"
echo "Phase 6 Training - Clean Restart"
echo "======================================================================"
echo ""

# Step 1: Kill existing processes
echo "[1] Cleaning up existing processes..."
pkill -9 -f "train_cities.py" 2>/dev/null
pkill -9 -f "tsx.*game_bridge" 2>/dev/null
pkill -9 -f "npx tsx" 2>/dev/null
sleep 2

REMAINING=$(ps aux | grep -E "tsx|game_bridge|train_cities" | grep -v grep | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "  ✓ All processes cleaned up"
else
    echo "  ⚠ Warning: $REMAINING processes still running"
    ps aux | grep -E "tsx|game_bridge|train_cities" | grep -v grep
fi

echo ""

# Step 2: Check GPU availability (if on GPU server)
if command -v nvidia-smi &> /dev/null; then
    echo "[2] Checking GPU availability..."
    nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | while IFS=, read -r idx mem_free; do
        echo "  GPU $idx: $mem_free free"
    done
    echo ""

    # Recommend GPU based on free memory
    BEST_GPU=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | sort -t, -k2 -rn | head -1 | cut -d, -f1)
    echo "  Recommended GPU: $BEST_GPU"
    export CUDA_VISIBLE_DEVICES=$BEST_GPU
    echo "  Set CUDA_VISIBLE_DEVICES=$BEST_GPU"
    echo ""
fi

# Step 3: Run training with improved parameters
echo "[3] Starting training..."
echo "  Map: australia_256x256"
echo "  Bots: 10"
echo "  Timesteps: 20,000,000"
echo "  Device: cuda (GPU $CUDA_VISIBLE_DEVICES)"
echo "  Environments: 1"
echo "  Batch size: 32 (memory optimized)"
echo "  N steps: 512 (memory optimized)"
echo ""

echo "======================================================================"
echo "Training will start in 3 seconds..."
echo "Press Ctrl+C to cancel"
echo "======================================================================"
sleep 3

# Enable PyTorch memory optimization
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Start training
python3 train_cities.py \
  --map australia_256x256 \
  --bots 10 \
  --timesteps 20000000 \
  --device cuda \
  --n-envs 1 \
  --batch-size 32 \
  --n-steps 512 \
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
