# OpenFront.io RL Agent - Architecture Documentation

## Game Context

- **Mode**: FFA Battle Royale (50+ bots)
- **Goal**: Outlast opponents, reach 80% territory
- **Features**: Attack, expand, build cities
- **Removed**: Boats, nukes, defenses, diplomacy, alliances

## Architecture Summary

```
State:     128×128×5 map + 16 global features
Actions:   Direction (9) + Intensity (5) + Build (2)
Model:     Simple CNN + MLP (~500K params)
Algorithm: PPO
Training:  500K-1M steps = 2-4 days
```

## Why This Design?

| Challenge | Solution |
|-----------|----------|
| 50+ opponents | Aggregate info, no individual tracking |
| Battle royale | Reactive decisions, simple actions |
| Real-time | Fast inference (10ms) |
| Beat bots | Simple is enough, no need for perfect play |

## Expected Performance

- Training time: 2-4 days (M4 Max or RTX 3060)
- Win rate: 25-40% against 50 bots
- Inference: 10ms per decision

## Files

1. **01_ARCHITECTURE.md** - Network design
2. **02_STATE_ACTIONS.md** - Inputs and outputs
3. **03_REWARD_TRAINING.md** - Learning setup
4. **04_IMPLEMENTATION.md** - Code

---

**Version**: 2.0  
**Updated**: 2025-11-01
