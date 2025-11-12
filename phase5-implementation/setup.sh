#!/bin/bash
# Phase 5 Setup Script
# Run this to set up the Phase 5 environment

set -e

echo "=========================================="
echo "Phase 5 Setup Script"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.8+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"

# Check CUDA availability
echo -e "\n${YELLOW}Checking CUDA availability...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
else
    echo -e "${YELLOW}⚠ No NVIDIA GPU detected (will use CPU)${NC}"
fi

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p models logs runs notebooks
echo -e "${GREEN}✓ Directories created${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
echo "This may take several minutes..."

if command -v nvidia-smi &> /dev/null; then
    echo "Installing with CUDA support..."
    pip install -r requirements.txt
    pip install torch --index-url https://download.pytorch.org/whl/cu117
else
    echo "Installing CPU version..."
    pip install -r requirements.txt
    pip install torch
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Verify installation
echo -e "\n${YELLOW}Verifying installation...${NC}"
python3 << EOF
import torch
import gymnasium
import stable_baselines3

print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Gymnasium: {gymnasium.__version__}")
print(f"Stable-Baselines3: {stable_baselines3.__version__}")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Installation verified${NC}"
else
    echo -e "${RED}✗ Verification failed${NC}"
    exit 1
fi

# Summary
echo -e "\n=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "=========================================="
echo ""
echo "Next steps:"
echo "1. Start training:"
echo "   cd src && python train_gpu.py --map australia_500x500"
echo ""
echo "2. Or use Jupyter notebook:"
echo "   jupyter notebook notebooks/gpu_training.ipynb"
echo ""
echo "3. Monitor training:"
echo "   tensorboard --logdir runs"
echo ""
echo "For more information, see README.md"
echo ""
