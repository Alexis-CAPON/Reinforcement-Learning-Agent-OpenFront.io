# Setup Guide - Phase 3 Game Bridge Integration

This guide walks you through setting up the complete game bridge for Phase 3.

## Prerequisites

- **Python 3.9+** with venv
- **Node.js 16+** with npm
- **TypeScript** (installed via npm)
- **Base game** in `../../base-game/`

## Quick Setup

```bash
cd phase3-implementation

# 1. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup TypeScript game bridge
cd game_bridge
npm install
cd ..

# 3. Test integration
python test_integration.py
```

## Detailed Setup

### 1. Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import gymnasium; print(f'Gymnasium: {gymnasium.__version__}')"
```

### 2. TypeScript Game Bridge

```bash
cd game_bridge

# Install TypeScript dependencies
npm install

# Verify tsx is available
npx tsx --version

# Test game bridge manually
npx tsx game_bridge.ts
# (Should print: [GameBridge] Ready for commands)
# Press Ctrl+C to exit

cd ..
```

### 3. Verify Base Game

The game bridge needs access to the base game source:

```bash
# Check base game exists
ls -la ../../base-game/

# Should see:
# - src/
# - tests/
# - tsconfig.json
```

If base game is missing, you'll need to set it up first.

### 4. Test Integration

```bash
# Run integration tests
python test_integration.py
```

Expected output:
```
============================================================
Phase 3 Integration Tests
============================================================

Test 1: GameWrapper Direct Test
✓ GameWrapper created
✓ Game started
✓ Spatial maps extracted
✓ Game ticks executed
✓ GameWrapper test passed!

Test 2: OpenFrontEnv Integration Test
✓ Environment created
✓ Environment reset
✓ Observation shapes correct
✓ Random actions executed
✓ Environment test passed!

Test 3: Full Episode Test
✓ Full episode test passed!

============================================================
ALL TESTS PASSED ✓
============================================================
```

## Troubleshooting

### Issue: "Game bridge not found"

**Solution:**
```bash
# Check game bridge exists
ls -la game_bridge/game_bridge.ts

# If missing, the file should be in phase3-implementation/game_bridge/
```

### Issue: "Cannot find module '../../base-game/...'"

**Solution:**
```bash
# Verify base game location
ls -la ../../base-game/src/core/game/Game.ts

# If base game is in different location, update imports in game_bridge.ts
```

### Issue: "tsx: command not found"

**Solution:**
```bash
cd game_bridge
npm install  # Installs tsx as devDependency
npx tsx --version  # Should work now
```

### Issue: "Map file not found: plains"

**Solution:**
```bash
# Check available maps
ls ../../base-game/tests/util/maps/

# Use available map name in test:
# wrapper = GameWrapper(map_name='<available-map>')
```

### Issue: Python can't import game_wrapper

**Solution:**
```bash
# Make sure you're in the phase3-implementation directory
pwd  # Should end with: /phase3-implementation

# Verify file exists
ls -la src/game_wrapper.py

# Try explicit import
python -c "import sys; sys.path.insert(0, 'src'); from game_wrapper import GameWrapper; print('OK')"
```

### Issue: TypeScript compilation errors

**Solution:**
```bash
cd game_bridge

# Check TypeScript config
cat tsconfig-esm.json

# Try compiling manually
npx tsc --noEmit game_bridge.ts

# Fix any errors shown
```

## Next Steps

Once all tests pass:

### 1. Run Short Training Test

```bash
# Test training for 10K steps (5-10 minutes)
python src/train.py --device cpu --n-envs 4 --total-timesteps 10000
```

### 2. Monitor Training

```bash
# In another terminal
tensorboard --logdir runs/

# Open browser to http://localhost:6006
```

### 3. Full Training

```bash
# Start curriculum learning (2-3 days on M4 Max)
python src/train.py --device mps --n-envs 12
```

## File Structure

After setup, you should have:

```
phase3-implementation/
├── .venv/                  # Python virtual environment
├── game_bridge/
│   ├── node_modules/       # TypeScript dependencies
│   ├── game_bridge.ts      # Game bridge implementation
│   ├── RLConfig.ts
│   ├── package.json
│   └── tsconfig-esm.json
├── src/
│   ├── environment.py      # RL environment
│   ├── game_wrapper.py     # Python ↔ TypeScript interface
│   ├── model.py
│   ├── train.py
│   └── evaluate.py
├── test_integration.py     # Integration tests
└── requirements.txt
```

## Common Workflows

### Start Fresh Training

```bash
source .venv/bin/activate
python src/train.py --device mps --n-envs 12
```

### Resume Training

```bash
source .venv/bin/activate
python src/train.py \
    --device mps \
    --n-envs 12 \
    --output-dir runs/previous_run \
    --resume
```

### Evaluate Model

```bash
source .venv/bin/activate
python src/evaluate.py \
    runs/run_20251101/openfront_final \
    --n-episodes 50 \
    --num-bots 50
```

### Test Environment Only

```bash
# Test without training
python test_environment.py

# Test with game bridge
python test_integration.py
```

## Performance Tips

### For M4 Max

```bash
# Optimal settings for M4 Max
python src/train.py \
    --device mps \
    --n-envs 12
```

### For CPU Only

```bash
# Reduce parallel envs for CPU
python src/train.py \
    --device cpu \
    --n-envs 4
```

### Memory Issues

```bash
# Reduce if out of memory
python src/train.py \
    --device mps \
    --n-envs 6  # Lower than default 8
```

## Support

If you encounter issues:

1. Check logs in `game_bridge/` stderr
2. Run `python test_integration.py` for diagnostics
3. Check `IMPLEMENTATION_STATUS.md` for known issues
4. Review base game setup in `../../base-game/`

## Success Criteria

You're ready to train when:
- ✓ `test_integration.py` passes all tests
- ✓ Environment can reset and step
- ✓ Spatial maps are extracted correctly
- ✓ Actions execute without errors
- ✓ Short training run (10K steps) completes

Then proceed with full training!
