# Phase 6 Simplification Plan

## Files Copied from Phase 5
- ✓ `src/environment_cities.py` (from `environment_full_game.py`)
- ✓ `src/game_wrapper.py` (no changes needed)
- ✓ `game_bridge/game_bridge.ts` (no changes needed)
- ✓ `train_cities.py` (from `train_full_game.py`)

## Changes Needed in `environment_cities.py`

### 1. Class Name & Documentation
- **Change**: `OpenFrontEnvFullGame` → `OpenFrontEnvCities`
- **Update**: All docstrings to mention "Cities Only" instead of "Full Game"

### 2. Action Space Simplification

**FROM (Phase 5):**
```python
(5, 11, 5, 7, 2, 10, 10) = 38,500 actions
- cluster_id: 0-4
- action_type: 0-8=attack, 9=build, 10=nuke
- intensity: 0-4
- building_type: 0-6 (None, City, Port, Silo, SAM, Defense, Factory)
- nuke_type: 0-1 (Atom, Hydrogen)
- tile_x: 0-9
- tile_y: 0-9
```

**TO (Phase 6):**
```python
(5, 10, 5, 10) = 2,500 actions
- cluster_id: 0-4
- action_type: 0-7=attack, 8=WAIT, 9=BUILD_CITY
- intensity: 0-4
- tile: 0-9 (single tile index, not x,y)
```

### 3. Remove Building Types
**Keep**: City
**Remove**: Port, Missile Silo, SAM Launcher, Defense Post, Factory

Lines to change:
- Line 106: `self.building_types = ['None', 'City', 'Port', 'Missile Silo', 'SAM Launcher', 'Defense Post', 'Factory']`
  → `# Only City supported in Phase 6`

### 4. Remove Nuke Types
**Remove**: All nuke types (Atom Bomb, Hydrogen Bomb)

Lines to remove:
- Line 107: `self.nuke_types = ['Atom Bomb', 'Hydrogen Bomb']`
- All nuke-related action masking logic
- All nuke launch execution code

### 5. Observation Space Simplification

**Spatial channels** (keep simpler):
- 0: Our territory
- 1: Enemy territory
- 2: Neutral territory
- 3: Border tiles
- 4: Troop density
- 5: Our cities
- 6: Enemy cities
- 7-15: Padding/unused

**Global features** (remove):
- Ports count
- Silos count
- SAM launchers count
- Defense posts count
- Factories count
- Atom bombs available
- Hydrogen bombs available
- Can launch nuke

**Cluster features** (simplify to 4):
- tiles_count
- troop_count
- has_city
- can_afford_city

### 6. Action Execution Simplification

**Keep**:
- Attack actions (directions 0-7)
- WAIT action (8)
- BUILD_CITY action (9)

**Remove**:
- Build Port
- Build Silo
- Build SAM
- Build Defense
- Build Factory
- Launch nuke (action type 10)

### 7. Reward Simplification

**Keep**:
- Territory change
- City construction bonus
- Gold accumulation
- Survival bonus
- Win/loss bonuses

**Remove**:
- Other building bonuses
- Nuke launch bonuses

## Changes Needed in `train_cities.py`

1. Update import: `from environment_full_game import OpenFrontEnvFullGame` → `from environment_cities import OpenFrontEnvCities`
2. Update comments/descriptions
3. Update action space size in logs (38,500 → 2,500)
4. Remove references to nukes and extra buildings

## No Changes Needed

- ✓ `game_wrapper.py` - Already supports cities, works as-is
- ✓ `game_bridge.ts` - Already supports city building, works as-is

## Testing Plan

1. Test environment creation
2. Test action masking (verify 2,500 action space)
3. Test city building
4. Test short training run (500 steps)
5. Compare speed with Phase 5
