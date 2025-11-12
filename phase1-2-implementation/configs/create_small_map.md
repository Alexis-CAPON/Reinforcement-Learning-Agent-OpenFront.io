# Creating a Small Training Map

For Phase 1, we need a small map (50×50 or similar) for faster training.

## Option 1: Use Existing Small Map

The base game includes several maps. Try these smaller ones:

- **Britannia** (~300×250 tiles)
- **Iceland** (~400×300 tiles)
- **Halkidiki** (larger, but well-tested)

Update `configs/phase1_config.json`:

```json
{
  "game": {
    "map_name": "Britannia",  // or "Iceland"
    ...
  }
}
```

## Option 2: Create Custom Small Map

If you need a truly minimal map (50×50), you'll need to:

### 1. Use the Map Generator

```bash
cd ../base-game/map-generator

# Check available generator scripts
ls -la
```

### 2. Generate Simple Map

Look for a map generation script or tool. The base game should have a map generation system.

Typical parameters:
- Width: 50
- Height: 50
- Spawns: 2 (player + AI)
- Terrain: Mostly plains (for simplicity)

### 3. Save Map

Save generated map to:
```
base-game/resources/maps/training_phase1.map
```

### 4. Update Config

```json
{
  "game": {
    "map_name": "training_phase1",
    ...
  }
}
```

## Recommendation for Phase 1

**Start with Britannia or Iceland** - these are small enough for fast training but large enough to be interesting.

Update the config:

```json
{
  "game": {
    "map_name": "Britannia",  // Good starting point
    "opponent_difficulty": "Easy"
  }
}
```

Then test:

```bash
python train.py train --timesteps 10000  # Quick test run
```

If episodes are too long (>10 minutes), switch to an even smaller map or reduce `max_ticks` in config.
