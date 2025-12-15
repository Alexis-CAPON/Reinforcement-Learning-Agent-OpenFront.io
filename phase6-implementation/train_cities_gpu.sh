#!/bin/bash
# GPU-optimized training script for Phase 6
# Uses memory-efficient hyperparameters for RTX 2080 Ti (11GB)

echo "==================================================================="
echo "Phase 6 GPU Training - Memory Optimized"
echo "==================================================================="
echo "GPU: RTX 2080 Ti (11GB)"
echo "Memory optimization: Reduced batch size and steps"
echo "Expected GPU usage: ~4-5 GB"
echo "==================================================================="

# Enable PyTorch memory optimization
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Select GPU 0
export CUDA_VISIBLE_DEVICES=0

# Run training with memory-efficient settings
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

echo "==================================================================="
echo "Training complete!"
echo "==================================================================="
