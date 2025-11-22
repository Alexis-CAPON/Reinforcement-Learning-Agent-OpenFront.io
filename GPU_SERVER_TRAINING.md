# GPU Server Training Guide

This guide explains how to train the OpenFront.io RL agent on a GPU server without installing TypeScript, Node.js, or development tools.

## Solution Overview

We use **Docker** to package the entire environment (game engine + bridge + Python) into a container that can run anywhere.

## Prerequisites on GPU Server

Only these are needed:
- Docker (version 20.10+)
- NVIDIA Docker runtime (nvidia-docker2)
- NVIDIA GPU drivers
- GPU with CUDA support

### Check if you have GPU support:
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Step 1: Build Docker Image (on your local machine)

### Option A: Build and Push to Registry

```bash
# On your local machine (Mac/Linux)
cd /path/to/openfrontio-rl

# Build the image
docker build -t openfrontio-rl:latest .

# Tag for your registry (Docker Hub, AWS ECR, etc.)
docker tag openfrontio-rl:latest YOUR_REGISTRY/openfrontio-rl:latest

# Push to registry
docker push YOUR_REGISTRY/openfrontio-rl:latest
```

### Option B: Save and Transfer Image

If you can't use a registry:

```bash
# On local machine: Build and save
docker build -t openfrontio-rl:latest .
docker save openfrontio-rl:latest | gzip > openfrontio-rl.tar.gz

# Transfer to server (replace with your server details)
scp openfrontio-rl.tar.gz user@gpu-server:/path/to/destination/

# On GPU server: Load image
docker load < openfrontio-rl.tar.gz
```

## Step 2: Prepare Server Directory

On the GPU server:

```bash
# Create working directory
mkdir -p ~/openfrontio-training
cd ~/openfrontio-training

# Create directories for outputs
mkdir -p models logs runs
```

## Step 3: Training Commands

### Basic Training

```bash
docker run --gpus all \
  -v $(pwd)/models:/workspace/phase5-implementation/models \
  -v $(pwd)/logs:/workspace/phase5-implementation/logs \
  -v $(pwd)/runs:/workspace/phase5-implementation/runs \
  openfrontio-rl:latest \
  python3 train_full_game.py \
    --device cuda \
    --map australia_256x256 \
    --bots 10 \
    --timesteps 20000000
```

### Training with Custom Parameters

```bash
docker run --gpus all \
  -v $(pwd)/models:/workspace/phase5-implementation/models \
  -v $(pwd)/logs:/workspace/phase5-implementation/logs \
  -v $(pwd)/runs:/workspace/phase5-implementation/runs \
  openfrontio-rl:latest \
  python3 train_full_game.py \
    --device cuda \
    --map australia_256x256 \
    --bots 10 \
    --timesteps 50000000 \
    --lr 2e-4 \
    --batch-size 256 \
    --n-steps 4096 \
    --ent-coef 0.01
```

### Run in Background (Detached)

```bash
docker run -d --gpus all \
  --name openfrontio-training \
  -v $(pwd)/models:/workspace/phase5-implementation/models \
  -v $(pwd)/logs:/workspace/phase5-implementation/logs \
  -v $(pwd)/runs:/workspace/phase5-implementation/runs \
  openfrontio-rl:latest \
  python3 train_full_game.py \
    --device cuda \
    --map australia_256x256 \
    --bots 10 \
    --timesteps 20000000

# View logs
docker logs -f openfrontio-training

# Stop training
docker stop openfrontio-training

# Remove container (keeps data in volumes)
docker rm openfrontio-training
```

## Step 4: Monitor Training

### View Logs in Real-Time

```bash
docker logs -f openfrontio-training
```

### TensorBoard Monitoring

```bash
# Start TensorBoard in separate container
docker run -d --name tensorboard \
  -p 6006:6006 \
  -v $(pwd)/runs:/workspace/phase5-implementation/runs \
  openfrontio-rl:latest \
  tensorboard --logdir runs/ --host 0.0.0.0 --port 6006

# Access at: http://your-server-ip:6006
```

### Check GPU Usage

```bash
# On server
nvidia-smi

# Or inside container
docker exec openfrontio-training nvidia-smi
```

## Step 5: Retrieve Trained Models

### Copy from Server

```bash
# On your local machine
scp -r user@gpu-server:~/openfrontio-training/models ./trained_models/
scp -r user@gpu-server:~/openfrontio-training/runs ./training_runs/
```

### Direct from Container

```bash
# On server
docker cp openfrontio-training:/workspace/phase5-implementation/models/ppo_full_game_*/best_model.zip ./

# Then transfer to local
scp best_model.zip user@local-machine:/path/
```

## Alternative: Docker Compose (Easier Management)

Transfer `docker-compose.yml` to server:

```bash
# On local machine
scp docker-compose.yml user@gpu-server:~/openfrontio-training/

# On server
cd ~/openfrontio-training
docker-compose up -d training

# View logs
docker-compose logs -f training

# Stop
docker-compose down
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If fails, install nvidia-docker2:
# Ubuntu/Debian:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Out of Memory

Reduce batch size or n-steps:

```bash
docker run --gpus all \
  -v $(pwd)/models:/workspace/phase5-implementation/models \
  -v $(pwd)/logs:/workspace/phase5-implementation/logs \
  -v $(pwd)/runs:/workspace/phase5-implementation/runs \
  openfrontio-rl:latest \
  python3 train_full_game.py \
    --device cuda \
    --map australia_256x256 \
    --bots 5 \
    --batch-size 64 \
    --n-steps 1024
```

### Container Exits Immediately

Check logs:
```bash
docker logs openfrontio-training
```

Common issues:
- Missing game maps: Ensure base-game/resources/maps is included in image
- Python import errors: Check requirements.txt includes all dependencies
- Bridge compilation errors: Rebuild image with `--no-cache`

### Training Too Slow

Check GPU utilization:
```bash
nvidia-smi -l 1  # Update every 1 second
```

If GPU usage is low:
- Increase batch_size: `--batch-size 256` or `512`
- Use multiple parallel environments (if memory allows)
- Check if CPU is bottleneck (game simulation)

## Performance Expectations

### GPU Training Time Estimates

**NVIDIA RTX 4090 / A6000**:
- 2M steps: ~2-3 hours
- 10M steps: ~10-15 hours
- 20M steps: ~20-30 hours

**NVIDIA RTX 3090 / V100**:
- 2M steps: ~3-4 hours
- 10M steps: ~15-20 hours
- 20M steps: ~30-40 hours

**NVIDIA RTX 3080 / T4**:
- 2M steps: ~4-5 hours
- 10M steps: ~20-25 hours
- 20M steps: ~40-50 hours

## Advanced: Multi-GPU Training

If you have multiple GPUs:

```bash
# Use specific GPU
docker run --gpus '"device=0"' \
  -v $(pwd)/models:/workspace/phase5-implementation/models \
  openfrontio-rl:latest \
  python3 train_full_game.py --device cuda:0

# Run multiple training jobs on different GPUs
docker run -d --name train-gpu0 --gpus '"device=0"' \
  -v $(pwd)/models-gpu0:/workspace/phase5-implementation/models \
  openfrontio-rl:latest \
  python3 train_full_game.py --device cuda:0 --map australia_256x256

docker run -d --name train-gpu1 --gpus '"device=1"' \
  -v $(pwd)/models-gpu1:/workspace/phase5-implementation/models \
  openfrontio-rl:latest \
  python3 train_full_game.py --device cuda:1 --map australia_100x100_nt
```

## Cloud Platform Specific Instructions

### AWS EC2 with GPU

1. Launch g4dn, g5, or p3 instance
2. Use Deep Learning AMI (Ubuntu)
3. Docker and nvidia-docker pre-installed
4. Follow standard Docker commands above

### Google Cloud Platform (GCP)

1. Create VM with GPU (T4, V100, A100)
2. Install nvidia-docker:
   ```bash
   sudo apt-get update
   sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```
3. Follow standard Docker commands above

### Azure ML

1. Create compute instance with GPU
2. Use pre-built PyTorch environment
3. Follow standard Docker commands above

## Estimating Costs

### GPU Server Rental Costs (Approximate)

**Cloud Providers** (per hour):
- AWS p3.2xlarge (V100): $3.06/hour
- AWS g5.2xlarge (A10G): $1.21/hour
- GCP n1-highmem-8 + T4: $0.95/hour
- Azure NC6s_v3 (V100): $3.06/hour

**For 20M steps training (~30 hours on V100)**:
- AWS p3.2xlarge: ~$92
- AWS g5.2xlarge: ~$36
- GCP T4: ~$29

**Dedicated GPU Services**:
- Vast.ai: RTX 4090 ~$0.40/hour (~$12 for 30 hours)
- RunPod: RTX 3090 ~$0.30/hour (~$9 for 30 hours)

## Next Steps After Training

1. **Download trained models**:
   ```bash
   scp -r user@gpu-server:~/openfrontio-training/models ./
   ```

2. **Test locally**:
   ```bash
   python3 src/visualize_realtime.py \
     --model models/ppo_full_game_*/best_model.zip \
     --map australia_256x256
   ```

3. **Continue training** (resume):
   ```bash
   # Volumes preserve checkpoints, just restart container
   docker start openfrontio-training
   ```

4. **Transfer learning** (train on different map):
   ```bash
   docker run --gpus all \
     -v $(pwd)/models:/workspace/phase5-implementation/models \
     openfrontio-rl:latest \
     python3 train_full_game.py \
       --device cuda \
       --map australia_500x500 \
       --load-checkpoint models/ppo_full_game_*/best_model.zip
   ```
