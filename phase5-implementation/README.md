# Phase 5: GPU-Enabled Training with Self-Play

Phase 5 extends the Phase 3 implementation with GPU acceleration, self-play training, and support for larger maps. This implementation is optimized for training on JupyterHub servers with GPU access.

## What's New in Phase 5

### 1. GPU Support
- **Automatic device detection** (CUDA/MPS/CPU)
- **Optimized batch sizes** and rollout lengths for GPU
- **GPU memory monitoring** and management
- **Multi-GPU support** (future)

### 2. Self-Play Training
- Train against copies of your own agent
- More challenging and adaptive opponents
- Curriculum learning through self-improvement

### 3. Large Map Support
- Support for maps from 100×100 to 1000×1000
- Adaptive downsampling for consistent observations
- Compatible with Phase 3 models (same observation space)

### 4. JupyterHub Integration
- Interactive Jupyter notebooks for training
- Real-time monitoring and control
- Easy checkpoint management

## Directory Structure

```
phase5-implementation/
├── src/
│   ├── train_gpu.py              # Main GPU training script
│   ├── environment_large.py      # Environment for large maps
│   ├── self_play_env.py          # Self-play wrapper
│   ├── model.py                  # Neural network architecture (from Phase 3)
│   └── training_callback.py      # Training callbacks (from Phase 3)
├── notebooks/
│   └── gpu_training.ipynb        # Jupyter notebook for training
├── game_bridge/                  # Game interface (symlink to Phase 3)
├── models/                       # Saved models
├── logs/                         # Training logs
├── runs/                         # Training runs
├── requirements.txt              # Dependencies with GPU support
└── README.md                     # This file
```

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA GPU with CUDA 11.7+ (recommended)
  - Minimum: 8 GB VRAM
  - Recommended: 16 GB+ VRAM
- **CPU**: 8+ cores recommended (for parallel environments)
- **RAM**: 16 GB+ recommended
- **Storage**: 10+ GB free space

### Software Requirements
- Python 3.8+
- CUDA 11.7+ (for NVIDIA GPUs)
- JupyterHub access (optional, but recommended)

## Installation

### 1. Clone Repository
```bash
cd /path/to/openfrontio-rl
```

### 2. Install Dependencies

#### Option A: CUDA 11.7 (NVIDIA GPUs)
```bash
pip install -r phase5-implementation/requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu117
```

#### Option B: CUDA 11.8 (NVIDIA GPUs)
```bash
pip install -r phase5-implementation/requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### Option C: CPU Only (Not Recommended)
```bash
pip install -r phase5-implementation/requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 3. Verify GPU Setup
```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Expected output:
```
CUDA Available: True
GPU: NVIDIA GeForce RTX 3090
```

## Usage

### Method 1: Jupyter Notebook (Recommended for JupyterHub)

1. **Open JupyterHub** and navigate to the project directory

2. **Open the training notebook:**
   ```
   phase5-implementation/notebooks/gpu_training.ipynb
   ```

3. **Follow the notebook instructions** to:
   - Check GPU availability
   - Configure training parameters
   - Load Phase 3 model (optional)
   - Start training
   - Monitor progress

4. **Adjust configuration** in Cell 3 of the notebook:
   ```python
   CONFIG = {
       'phase3_model_path': '../phase3-implementation/runs/run_20241107_120000/openfront_final',
       'map_name': 'australia_500x500',
       'num_bots': 10,
       'n_envs': 16,
       'total_timesteps': 1_000_000,
       'use_self_play': True,
   }
   ```

### Method 2: Command Line

#### Start from Scratch
```bash
cd phase5-implementation/src
python train_gpu.py \
  --map australia_500x500 \
  --n-envs 16 \
  --total-timesteps 1000000 \
  --output-dir ../runs/my_training
```

#### Continue from Phase 3 Model
```bash
python train_gpu.py \
  --map australia_500x500 \
  --n-envs 16 \
  --total-timesteps 1000000 \
  --phase3-model ../../phase3-implementation/runs/run_20241107_120000/openfront_final \
  --output-dir ../runs/continued_training
```

#### Disable Self-Play (Use Regular Bots)
```bash
python train_gpu.py \
  --map australia_500x500 \
  --n-envs 16 \
  --total-timesteps 1000000 \
  --no-self-play \
  --output-dir ../runs/no_selfplay
```

#### Force CPU (For Testing)
```bash
python train_gpu.py \
  --device cpu \
  --n-envs 4 \
  --total-timesteps 10000
```

## Configuration

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--map` | `australia_500x500` | Map to train on |
| `--num-bots` | 10 | Number of opponent bots |
| `--n-envs` | 16 | Parallel environments |
| `--total-timesteps` | 1,000,000 | Total training steps |
| `--device` | auto | Device (cuda/mps/cpu) |
| `--phase3-model` | None | Path to Phase 3 model |
| `--no-self-play` | False | Disable self-play |
| `--output-dir` | `runs/run_<timestamp>` | Output directory |

### GPU-Specific Settings

Adjust these based on your GPU memory:

| GPU VRAM | n_envs | batch_size | n_steps |
|----------|--------|------------|---------|
| 8 GB     | 8      | 256        | 1024    |
| 16 GB    | 16     | 512        | 2048    |
| 24 GB+   | 24-32  | 1024       | 4096    |

Modify in the training script:
```python
# In train_gpu.py, line ~238
batch_size=512 if device == 'cuda' else 256,
n_steps=2048 if device == 'cuda' else 1024,
```

## Monitoring Training

### TensorBoard

Start TensorBoard to monitor training:
```bash
tensorboard --logdir phase5-implementation/runs
```

Then open: http://localhost:6006

**Key Metrics:**
- `rollout/ep_rew_mean` - Average episode reward
- `rollout/ep_len_mean` - Average episode length
- `train/loss` - Training loss
- `train/learning_rate` - Current learning rate

### GPU Monitoring

Monitor GPU usage in real-time:
```bash
# Basic monitoring
watch -n 1 nvidia-smi

# Or install gpustat for better visualization
pip install gpustat
watch -n 1 gpustat -cp
```

### Check Training Progress

```bash
# List checkpoints
ls -lh phase5-implementation/runs/run_*/checkpoints/

# Check latest model
ls -lht phase5-implementation/runs/run_*/checkpoints/*.zip | head -1
```

## Checkpoints and Models

Training automatically saves checkpoints every 50,000 steps:

```
runs/run_<timestamp>/
├── checkpoints/
│   ├── phase5_model_50000_steps.zip
│   ├── phase5_model_100000_steps.zip
│   └── phase5_model_150000_steps.zip
├── logs/                          # TensorBoard logs
└── phase5_final.zip               # Final model
```

### Load a Checkpoint

```python
from stable_baselines3 import PPO

model = PPO.load("runs/run_20241107_150000/checkpoints/phase5_model_100000_steps")
```

## Continuing Training from Phase 3

Phase 5 models are compatible with Phase 3 models (same observation space).

To continue training from a Phase 3 model:

1. **Find your Phase 3 model:**
   ```bash
   ls ../phase3-implementation/runs/*/openfront_final.zip
   ```

2. **Start training with `--phase3-model`:**
   ```bash
   python train_gpu.py \
     --phase3-model ../phase3-implementation/runs/run_20241107_120000/openfront_final \
     --map australia_500x500 \
     --total-timesteps 1000000
   ```

3. **The training script will:**
   - Load the Phase 3 model
   - Reduce learning rate to 1e-4 (fine-tuning)
   - Continue training on the larger map

## Troubleshooting

### Out of Memory (OOM) Errors

If you get CUDA OOM errors:

1. **Reduce batch size:**
   ```python
   batch_size=256  # Instead of 512
   ```

2. **Reduce parallel environments:**
   ```bash
   --n-envs 8  # Instead of 16
   ```

3. **Reduce rollout steps:**
   ```python
   n_steps=1024  # Instead of 2048
   ```

4. **Clear CUDA cache** (in notebook):
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

### Training is Slow

1. **Check GPU is being used:**
   ```bash
   nvidia-smi
   ```

2. **Verify model is on GPU:**
   ```python
   print(model.device)  # Should print "cuda:0"
   ```

3. **Increase parallel environments** (if GPU not fully utilized):
   ```bash
   --n-envs 24  # More environments = better GPU utilization
   ```

### Phase 3 Model Won't Load

1. **Check model path is correct:**
   ```bash
   ls path/to/phase3_model.zip
   ```

2. **Verify model is compatible:**
   ```python
   from stable_baselines3 import PPO
   model = PPO.load("path/to/model")
   print(model.observation_space)  # Should match Phase 5
   ```

3. **If incompatible, start from scratch:**
   ```bash
   python train_gpu.py --map australia_500x500  # No --phase3-model
   ```

## Performance Tips

### For Maximum GPU Utilization

1. **Increase parallel environments:**
   ```bash
   --n-envs 24  # Or higher if GPU allows
   ```

2. **Increase batch size:**
   ```python
   batch_size=1024  # For GPUs with 24GB+ VRAM
   ```

3. **Use CUDA 11.8** (slightly faster than 11.7)

### For Faster Training Convergence

1. **Start from Phase 3 model:**
   ```bash
   --phase3-model path/to/phase3_model.zip
   ```

2. **Use self-play:**
   ```bash
   # (enabled by default)
   ```

3. **Train on similar map to target:**
   ```bash
   --map australia_500x500  # If testing on australia maps
   ```

## Next Steps

After training completes:

1. **Evaluate your model** using Phase 4 visualizer:
   ```bash
   cd ../phase4-implementation/src
   python visualize_realtime.py --model ../phase5-implementation/runs/run_*/phase5_final
   ```

2. **Compare with Phase 3:**
   - Win rate
   - Average survival time
   - Territory control

3. **Continue training** with more timesteps or different maps

4. **Experiment with hyperparameters:**
   - Learning rate
   - Entropy coefficient
   - Number of opponents

## Support

For issues or questions:
1. Check this README
2. Review Phase 3 documentation
3. Check TensorBoard logs for training issues
4. Monitor GPU usage for hardware issues

## References

- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PyTorch CUDA Documentation](https://pytorch.org/docs/stable/cuda.html)
- [Phase 3 Implementation](../phase3-implementation/README.md)
- [Phase 4 Visualizer](../phase4-implementation/README.md)
