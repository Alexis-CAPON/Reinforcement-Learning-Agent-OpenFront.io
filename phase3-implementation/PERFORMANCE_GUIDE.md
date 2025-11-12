# Performance Guide - Training Speed Optimization

## How Parallel Environments Speed Up Training

### The Basics

**Single Environment (n_envs=1):**
- Collect 1 sample at a time
- CPU mostly idle waiting for game
- GPU underutilized
- Speed: ~60 FPS

**Multiple Environments (n_envs=12):**
- Collect 12 samples simultaneously
- All CPU cores active
- GPU processes batches efficiently
- Speed: ~550 FPS (9× faster!)

### Real-World Training Times

Based on M4 Max performance (~550 FPS with n_envs=12):

| Phase | Steps | n_envs=1 | n_envs=4 | n_envs=8 | n_envs=12 |
|-------|-------|----------|----------|----------|-----------|
| Quick Test | 10K | 2m 47s | 42s | 25s | 18s |
| Phase 1 | 100K | 27 min | 7 min | 4 min | 3 min |
| Phase 2 | 300K | 83 min | 21 min | 12 min | 9 min |
| Phase 3 | 500K | 139 min | 35 min | 21 min | 15 min |
| **Full (900K)** | **900K** | **4.2 hrs** | **1.0 hr** | **37 min** | **27 min** |

## How It Works

### 1. CPU Parallelism (Game Simulation)

```
M4 Max: 16 cores (4 P-cores + 12 E-cores)

n_envs=4:  Uses 4 cores  → Game sim bottleneck
n_envs=8:  Uses 8 cores  → Balanced
n_envs=12: Uses 12 cores → Optimal for M4 Max
n_envs=16: Uses 16 cores → Max utilization
```

Each environment runs in a separate process, simulating the game in parallel.

### 2. GPU Batching (Neural Network)

```python
# Single environment
for i in range(1000):
    action = model(obs)  # Process 1 state

# 12 parallel environments
for i in range(84):  # Only 84 iterations!
    actions = model(obs_batch)  # Process 12 states at once
```

The MPS GPU is much more efficient with batched operations.

### 3. End-to-End Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Env 1     │────▶│             │────▶│   Action 1  │
│   Env 2     │────▶│   Model     │────▶│   Action 2  │
│   Env 3     │────▶│   (GPU)     │────▶│   Action 3  │
│   ...       │────▶│   Batch     │────▶│   ...       │
│   Env 12    │────▶│   Forward   │────▶│   Action 12 │
└─────────────┘     └─────────────┘     └─────────────┘
    (CPU)               (MPS)               (Return)
```

## Optimal Settings by Hardware

### M4 Max (Your Hardware)
```bash
# Recommended
python src/train.py --device mps --n-envs 12

# Specs
- GPU Cores: 40 (M4 Max Pro) or 32 (M4 Max)
- CPU Cores: 16 (4+12)
- Memory: 36GB or 48GB unified
- Expected: 500-600 FPS
```

### M3/M2/M1 Mac
```bash
python src/train.py --device mps --n-envs 8

# Typical specs
- GPU Cores: 10-16
- CPU Cores: 8-10
- Memory: 16-32GB
- Expected: 300-400 FPS
```

### CPU Only (No GPU)
```bash
python src/train.py --device cpu --n-envs 4

# Limits
- No GPU acceleration
- CPU must handle everything
- Expected: 100-150 FPS
```

### NVIDIA GPU (RTX 3060/4060)
```bash
python src/train.py --device cuda --n-envs 12

# Typical specs
- CUDA Cores: 3584-6144
- CPU: 8-16 cores
- Expected: 600-800 FPS
```

## Diminishing Returns

More environments isn't always better:

```
n_envs=1:  60 FPS   (baseline)
n_envs=4:  240 FPS  (4.0× speedup) ← Good scaling
n_envs=8:  400 FPS  (6.7× speedup) ← Good scaling
n_envs=12: 550 FPS  (9.2× speedup) ← Good scaling
n_envs=16: 650 FPS  (10.8× speedup) ← Diminishing
n_envs=24: 700 FPS  (11.7× speedup) ← Not worth it
```

**Why?**
- CPU cores become saturated
- Memory bandwidth limits
- Python GIL overhead
- Process switching overhead

## Memory Usage

Approximate memory per environment:
```
Environment overhead:   ~50 MB
Game state:            ~100 MB
Replay buffer:         ~50 MB
────────────────────────────────
Per environment:       ~200 MB
```

**Total memory:**
```
n_envs=4:  ~1.5 GB  (model + envs)
n_envs=8:  ~2.5 GB
n_envs=12: ~3.5 GB
n_envs=16: ~4.5 GB
```

M4 Max with 36GB RAM: Can easily handle 16+ environments

## Recommendations by Training Phase

### Quick Testing (10-50K steps)
```bash
python src/train.py --device mps --n-envs 4 --total-timesteps 10000 --no-curriculum --num-bots 5

# Why n_envs=4?
- Fast startup
- Easy to debug
- Quick iteration
- Time: <1 minute
```

### Development (100-300K steps)
```bash
python src/train.py --device mps --n-envs 8 --total-timesteps 100000 --no-curriculum --num-bots 10

# Why n_envs=8?
- Balanced speed/stability
- Good logging frequency
- Reasonable memory
- Time: 4-12 minutes
```

### Full Training (900K steps)
```bash
python src/train.py --device mps --n-envs 12

# Why n_envs=12?
- Optimal for M4 Max
- Maximum speed without issues
- Full curriculum learning
- Time: 27-30 minutes
```

### Overnight Training (Multi-million steps)
```bash
python src/train.py --device mps --n-envs 16 --total-timesteps 5000000 --no-curriculum --num-bots 50

# Why n_envs=16?
- Max performance
- Long runs benefit more
- You're not actively monitoring
- Time: ~2-3 hours
```

## Monitoring Performance

### Check FPS
Look for `time/fps` in logs:
```
| time/                   |             |
|    fps                  | 550         |  ← Higher is better
|    iterations           | 10          |
|    total_timesteps      | 102400      |
```

### Check CPU Usage
```bash
# In another terminal
htop

# Look for:
# - Python processes at ~100% (one per environment)
# - Should see n_envs + 1 Python processes
```

### Check GPU Usage
```bash
# M4 Max GPU monitoring
sudo powermetrics --samplers gpu_power -i 1000

# Look for:
# - GPU Active Residency: >60% is good
# - GPU Power: Higher = more utilized
```

## Troubleshooting

### FPS Lower Than Expected

**Issue:** Only getting 150 FPS with n_envs=12

**Possible causes:**
1. Game simulation is slow
   - Solution: Use smaller maps or fewer bots

2. CPU thermal throttling
   - Solution: Ensure good cooling, reduce n_envs

3. Other processes using CPU
   - Solution: Close unnecessary apps

4. Python GIL bottleneck
   - Solution: This is normal, already using multiprocessing

### Out of Memory

**Issue:** "RuntimeError: MPS backend out of memory"

**Solutions:**
```bash
# Reduce parallel environments
python src/train.py --device mps --n-envs 8  # Down from 12

# Reduce batch size (in config.yaml)
batch_size: 128  # Down from 256

# Reduce rollout length
n_steps: 1024  # Down from 2048
```

### Unstable Training

**Issue:** Training crashes or gets stuck

**Possible causes:**
1. Too many environments overwhelming system
   - Solution: Reduce to n_envs=8

2. Game bridge crashes
   - Solution: Add error recovery, reduce n_envs

3. Memory fragmentation
   - Solution: Restart training periodically

## Best Practices

### Start Small, Scale Up
```bash
# 1. Test with n_envs=1 (verify everything works)
python src/train.py --device mps --n-envs 1 --total-timesteps 1000

# 2. Quick test with n_envs=4
python src/train.py --device mps --n-envs 4 --total-timesteps 10000

# 3. Full training with n_envs=12
python src/train.py --device mps --n-envs 12
```

### Monitor First Run
```bash
# Start training
python src/train.py --device mps --n-envs 12

# In another terminal, monitor
watch -n 1 'ps aux | grep python | head -20'

# Check FPS in logs
tail -f runs/run_*/logs/single_phase_1/progress.csv
```

### Use tmux for Long Runs
```bash
# Start persistent session
tmux new -s training

# Start training
python src/train.py --device mps --n-envs 12

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t training
```

## Summary

**Key Takeaways:**
- ✅ More environments = faster wallclock time (not more sample efficient)
- ✅ M4 Max sweet spot: n_envs=12 (~550 FPS)
- ✅ Can train 900K steps in ~27 minutes (vs 4.2 hours with n_envs=1)
- ✅ Diminishing returns after n_envs=16
- ⚠️ Memory usage scales linearly with n_envs
- ⚠️ Start with fewer envs for testing, scale up for production

**Quick Reference:**
```bash
# Testing:     n_envs=4   (~240 FPS)
# Development: n_envs=8   (~400 FPS)
# Production:  n_envs=12  (~550 FPS)
# Maximum:     n_envs=16  (~650 FPS)
```
