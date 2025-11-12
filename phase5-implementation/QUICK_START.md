# Phase 5: Quick Start Guide

Get up and running with GPU training in 5 minutes!

## Prerequisites

- Access to a server with NVIDIA GPU
- Python 3.8+
- CUDA 11.7+ installed

## Quick Setup

### 1. Run Setup Script

```bash
cd phase5-implementation
chmod +x setup.sh
./setup.sh
```

This will:
- Check your Python version
- Detect your GPU
- Install all dependencies
- Verify the installation

### 2. Start Training

#### Option A: Command Line (Simple)

```bash
cd src
python train_gpu.py \
  --map australia_500x500 \
  --n-envs 16 \
  --total-timesteps 1000000
```

#### Option B: Jupyter Notebook (Interactive)

```bash
# Start Jupyter
jupyter notebook notebooks/gpu_training.ipynb

# Then follow the notebook instructions
```

#### Option C: Continue from Phase 3

```bash
cd src
python train_gpu.py \
  --phase3-model ../../phase3-implementation/runs/run_XXXXXX/openfront_final \
  --map australia_500x500 \
  --total-timesteps 1000000
```

### 3. Monitor Training

In a separate terminal:

```bash
cd phase5-implementation
tensorboard --logdir runs
```

Then open: http://localhost:6006

## Expected Output

When training starts, you should see:

```
======================================================================
STARTING TRAINING
======================================================================
Device: CUDA
Map: australia_500x500
Opponents: 10 bots
Self-Play: True
Total Timesteps: 1,000,000
Parallel Environments: 16
======================================================================

GPU Memory: Allocated=2.45GB, Reserved=2.58GB

Episode 1 started: australia_500x500, 10 bots
...
```

## Troubleshooting

### "CUDA out of memory"

Reduce the number of environments:

```bash
python train_gpu.py --n-envs 8  # Instead of 16
```

### "No module named 'environment_large'"

Make sure you're in the `src` directory:

```bash
cd phase5-implementation/src
python train_gpu.py ...
```

### Training is slow

Check GPU is being used:

```bash
nvidia-smi
```

You should see Python processes using GPU memory.

## What's Happening?

1. **GPU Detection**: Script automatically detects your GPU (CUDA/MPS/CPU)
2. **Environment Creation**: Creates 16 parallel game environments
3. **Model Initialization**: Creates PPO model on GPU
4. **Training Loop**:
   - Collects experiences from all environments
   - Updates policy every 2048 steps
   - Saves checkpoints every 50,000 steps
5. **Checkpointing**: Saves models to `runs/run_<timestamp>/checkpoints/`

## Training Time Estimate

| GPU | Environments | 1M Steps | Notes |
|-----|-------------|----------|-------|
| RTX 3090 | 16 | ~2-3 hours | Recommended |
| RTX 3080 | 16 | ~3-4 hours | Good |
| RTX 3070 | 8 | ~4-5 hours | Reduce n_envs |
| RTX 3060 | 8 | ~5-6 hours | Reduce n_envs |
| CPU only | 4 | ~24+ hours | Not recommended |

## After Training

### 1. Find Your Model

```bash
ls -lh runs/run_*/checkpoints/
ls runs/run_*/phase5_final.zip
```

### 2. Test with Visualizer

```bash
cd ../../phase4-implementation/src
python visualize_realtime.py \
  --model ../../phase5-implementation/runs/run_XXXXXX/phase5_final
```

### 3. Evaluate Performance

Check TensorBoard:
- Average reward (should increase)
- Episode length (should increase initially)
- Territory percentage at end

## Tips

1. **Start Small**: Try 100K timesteps first to verify everything works
   ```bash
   python train_gpu.py --total-timesteps 100000
   ```

2. **Monitor GPU Usage**: Keep `nvidia-smi` open in another terminal
   ```bash
   watch -n 1 nvidia-smi
   ```

3. **Save Often**: Checkpoints save every 50K steps automatically

4. **Compare Models**: Test different checkpoints to find the best one

## Next Steps

- Continue training for more timesteps (5M+ for best results)
- Try different maps: `world`, `europe`, `asia`
- Experiment with more opponents: `--num-bots 20`
- Compare Phase 5 vs Phase 3 performance

For detailed documentation, see [README.md](README.md)
