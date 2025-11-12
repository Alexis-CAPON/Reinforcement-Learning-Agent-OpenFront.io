#!/bin/bash
# Setup script for Phase 3 implementation

echo "=========================================="
echo "OpenFront.io Phase 3 - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9+ required"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup game bridge (TypeScript)
echo "Setting up game bridge..."
cd game_bridge
if [ -f "package.json" ]; then
    npm install
    echo "✓ Game bridge dependencies installed"
else
    echo "⚠ No package.json found, skipping npm install"
fi
cd ..
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p checkpoints
mkdir -p logs
mkdir -p runs
echo "✓ Directories created"
echo ""

# Run tests
echo "Running tests..."
python test_environment.py
test_result=$?

if [ $test_result -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Setup complete! ✓"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Activate environment: source .venv/bin/activate"
    echo "  2. Test environment: python test_environment.py"
    echo "  3. Start training: python src/train.py"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "Setup completed with test failures"
    echo "=========================================="
    echo ""
    echo "Some tests failed. Please check the output above."
    echo ""
fi
