# Quick Start Guide - Phase 1

Get up and running in 5 minutes!

## Prerequisites

- Node.js 18+
- Python 3.9+
- ~5GB free disk space

## Installation (2 minutes)

```bash
cd phase1-implementation

# Run automated setup
./setup.sh
```

This will:
- ✓ Install Python dependencies
- ✓ Compile TypeScript game bridge
- ✓ Verify base game installation
- ✓ Create output directories

## Quick Test (1 minute)

Test that everything works:

```bash
# Test environment
cd rl_env
python3 openfrontio_env.py
```

You should see output like:
```
Testing OpenFrontIOEnv...
1. Resetting environment...
Observation features: [0.05 0.25 0.1 0.08 0.0]
Action mask: [1 1 1 0 0 0 0 0 0]
...
Test complete!
```

## Start Training (2 minutes to start, 3-5 hours to complete)

```bash
cd ..  # Back to phase1-implementation/

# Start training
python3 train.py train
```

Training will run for 200,000 timesteps (~3-5 hours).

## Monitor Training

In a new terminal:

```bash
cd phase1-implementation

# Start TensorBoard
tensorboard --logdir runs/

# Open http://localhost:6006 in your browser
```

## Expected Results

After training completes:

- **Win Rate**: 40-50% vs Easy AI
- **Training Time**: 3-5 hours
- **Model Size**: ~1MB
- **Best Model**: Saved in `runs/run_YYYYMMDD_HHMMSS/best_model/`

## Evaluate Your Agent

```bash
# Find your trained model
ls runs/

# Evaluate (replace with your run directory)
python3 train.py eval \
  --model runs/run_20241026_123456/best_model/best_model.zip \
  --episodes 20
```

## Troubleshooting

### "Game bridge not found"
```bash
cd game_bridge
tsc game_bridge.ts
cd ..
```

### "Cannot import openfrontio_env"
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/rl_env
```

### "Node.js module not found"
```bash
cd ../base-game
npm install
cd ../phase1-implementation
```

## What's Next?

Once you achieve 40%+ win rate:

1. **Analyze Results**: Check TensorBoard for learning curves
2. **Hyperparameter Tuning**: Adjust `configs/phase1_config.json`
3. **Extended Training**: Try `--timesteps 500000` for better performance
4. **Phase 2**: Move to enhanced observations and curriculum learning

## Need Help?

- Check `README.md` for detailed documentation
- Review `configs/phase1_config.json` for all parameters
- Look at training logs in `runs/*/logs/`

## Key Files

- `train.py` - Training and evaluation
- `rl_env/openfrontio_env.py` - Gymnasium environment
- `rl_env/game_wrapper.py` - Game interface
- `configs/phase1_config.json` - All settings
- `game_bridge/game_bridge.ts` - TypeScript bridge

Happy training! 🎮🤖
