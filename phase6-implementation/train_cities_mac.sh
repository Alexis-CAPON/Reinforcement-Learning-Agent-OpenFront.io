#!/bin/bash
# Mac Training Script for Phase 6 - MPS GPU acceleration
# Optimized for Apple Silicon (M1/M2/M3)

# Default: 8 environments (like Phase 3)
# Override with: ./train_cities_mac.sh 10
N_ENVS=${1:-8}

echo "===================================================================="
echo "Phase 6 Mac Training - MPS GPU Acceleration"
echo "===================================================================="
echo "Device: Apple Silicon GPU (MPS)"
echo "Environments: $N_ENVS (Phase 3 worked with 10)"
echo "Memory optimization: Moderate batch size"
echo "===================================================================="

# Check for Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "Warning: Not running on Apple Silicon (arm64)"
    echo "MPS acceleration may not be available"
fi

# Run training with Mac-optimized settings
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

echo "===================================================================="
echo "Training complete!"
echo "===================================================================="
