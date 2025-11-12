#!/bin/bash
# Setup script for Phase 1 implementation

set -e  # Exit on error

echo "========================================"
echo "OpenFront.io RL - Phase 1 Setup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Found: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found!"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Found: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found!"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

# Check TypeScript
echo -n "Checking TypeScript... "
if command -v tsc &> /dev/null; then
    TSC_VERSION=$(tsc --version)
    echo -e "${GREEN}✓${NC} Found: $TSC_VERSION"
else
    echo -e "${YELLOW}⚠${NC} TypeScript not found. Installing..."
    npm install -g typescript
    echo -e "${GREEN}✓${NC} TypeScript installed"
fi

echo ""
echo "========================================"
echo "Installing Dependencies"
echo "========================================"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Python dependencies installed"

# Compile TypeScript game bridge
echo ""
echo "Compiling TypeScript game bridge..."
cd game_bridge

# Try compiling with npx tsc
npx --yes typescript@latest game_bridge.ts --target ES2020 --module commonjs --moduleResolution node --esModuleInterop --skipLibCheck --resolveJsonModule 2>&1 | grep -v "Your user's .npmrc"

if [ -f "game_bridge.js" ]; then
    echo -e "${GREEN}✓${NC} Game bridge compiled successfully"
else
    echo -e "${YELLOW}⚠${NC} TypeScript compilation had issues, checking if JS files exist anyway..."
    if [ -f "RLConfig.js" ]; then
        echo -e "${YELLOW}⚠${NC} Some JS files exist, may work but verify later"
    else
        echo -e "${RED}✗${NC} Game bridge compilation failed"
        exit 1
    fi
fi
cd ..

# Check base game
echo ""
echo "Checking base game..."
if [ -d "../base-game" ]; then
    echo -e "${GREEN}✓${NC} Base game found"

    # Check if base game has node_modules
    if [ ! -d "../base-game/node_modules" ]; then
        echo -e "${YELLOW}⚠${NC} Base game dependencies not installed. Installing..."
        cd ../base-game
        npm install
        cd ../phase1-implementation
        echo -e "${GREEN}✓${NC} Base game dependencies installed"
    else
        echo -e "${GREEN}✓${NC} Base game dependencies already installed"
    fi
else
    echo -e "${RED}✗${NC} Base game not found at ../base-game"
    echo "Please ensure the base game is in the correct location"
    exit 1
fi

echo ""
echo "========================================"
echo "Creating Output Directories"
echo "========================================"
echo ""

mkdir -p runs
mkdir -p checkpoints
mkdir -p logs/tensorboard

echo -e "${GREEN}✓${NC} Output directories created"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Test the environment:"
echo "   cd rl_env && python3 openfrontio_env.py"
echo ""
echo "2. Run a quick training test:"
echo "   python3 train.py train --timesteps 1000"
echo ""
echo "3. Start full training:"
echo "   python3 train.py train"
echo ""
echo "4. Monitor with TensorBoard:"
echo "   tensorboard --logdir runs/"
echo ""
