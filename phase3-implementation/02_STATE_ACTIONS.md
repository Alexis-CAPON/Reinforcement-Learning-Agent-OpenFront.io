# State and Action Space

## State Representation

### Map Features [128, 128, 5]

**Channel 0: Your Territory**
- Binary mask: 1 = yours, 0 = not yours
- Shows your controlled area

**Channel 1: Enemy Density**
- Float [0, 1]: Number of enemies in area / max enemies
- Aggregates all 50+ opponents
- Hot spots = many enemies nearby

**Channel 2: Neutral Territory**
- Binary mask: 1 = unclaimed, 0 = claimed
- Expansion opportunities

**Channel 3: Your Troop Density**
- Float [0, 1]: Your troops / max troops per tile
- Shows your military strength

**Channel 4: Enemy Troop Density**
- Float [0, 1]: Enemy troops / max troops per tile
- Aggregates all enemy forces
- Threat assessment

**Extraction**:
```python
def extract_map(game):
    # Downsample from 512×512 to 128×128
    map_features = np.zeros((128, 128, 5), dtype=np.float32)
    
    map_features[:,:,0] = downsample(game.your_territory_mask)
    map_features[:,:,1] = downsample(game.enemy_count_map / 50)
    map_features[:,:,2] = downsample(game.neutral_mask)
    map_features[:,:,3] = downsample(game.your_troops / 10000)
    map_features[:,:,4] = downsample(game.enemy_troops / 10000)
    
    return map_features
```

### Global Features [16]

```python
global_features = [
    # Population (most critical)
    current_population / max_population,      # 0: Utilization (want 0.4-0.5)
    max_population / 100000,                  # 1: Capacity (normalized)
    population_growth_rate,                   # 2: Growing or shrinking
    
    # Territory
    your_territory_percentage,                # 3: % of map controlled
    territory_change_last_10_steps,           # 4: Expanding or losing
    
    # Position
    estimated_rank / 50,                      # 5: Placement (1st=0, 50th=1)
    num_adjacent_enemies / 10,                # 6: Border pressure
    
    # Resources
    num_cities,                               # 7: Economic infrastructure
    gold / 50000,                             # 8: Current gold (normalized)
    
    # Survival
    time_alive / max_game_time,               # 9: How long survived
    
    # Game phase
    game_progress,                            # 10: 0=start, 1=end
    
    # Threats
    nearest_large_enemy_distance / 128,       # 11: Closest threat
    
    # Reserved for future
    0, 0, 0, 0                                # 12-15: Unused
]
```

### Complete Observation

```python
observation = {
    'map': np.array([128, 128, 5], dtype=np.float32),    # 0.5 MB
    'global': np.array([16], dtype=np.float32)           # 64 bytes
}
```

## Action Space

### Three Components

**1. Direction [9 options]**
- 0: North
- 1: Northeast  
- 2: East
- 3: Southeast
- 4: South
- 5: Southwest
- 6: West
- 7: Northwest
- 8: Wait (no attack)

**2. Intensity [5 options]**
- 0: 20% of population
- 1: 35% of population
- 2: 50% of population
- 3: 75% of population
- 4: 100% of population

**3. Build City [2 options]**
- 0: Don't build
- 1: Build city (if can afford)

### Action Execution

```python
def execute_action(game, action):
    direction = action['direction']
    intensity = [0.20, 0.35, 0.50, 0.75, 1.00][action['intensity']]
    build = action['build']
    
    # 1. Attack in direction
    if direction < 8:  # Not waiting
        target = find_territory_in_direction(game, direction)
        if target and is_enemy_or_neutral(target):
            troops = int(game.your_population * intensity)
            game.attack(target, troops)
    
    # 2. Build city
    if build == 1 and game.gold >= CITY_COST:
        location = find_safe_interior_location(game)
        if location:
            game.build_city(location)
```

### Action Masking

```python
def create_action_mask(game):
    mask = np.ones(90, dtype=bool)  # All valid by default
    
    # Can't attack if no population
    if game.your_population < 100:
        mask[0:72] = False  # Disable all attack actions (9×5×2 - build)
    
    # Can't build if no gold
    if game.gold < CITY_COST:
        mask[::2] = False  # Disable all "build=1" actions
    
    # Can't attack in direction with no enemies/neutrals
    for direction in range(8):
        if not has_target_in_direction(game, direction):
            # Disable this direction for all intensities
            start = direction * 10  # 5 intensities × 2 build options
            mask[start:start+10] = False
    
    return mask
```

## Gymnasium Space Definition

```python
from gymnasium import spaces

observation_space = spaces.Dict({
    'map': spaces.Box(
        low=0.0, high=1.0,
        shape=(128, 128, 5),
        dtype=np.float32
    ),
    'global': spaces.Box(
        low=-np.inf, high=np.inf,
        shape=(16,),
        dtype=np.float32
    )
})

# Flattened action space for SB3
action_space = spaces.Discrete(90)  # 9 × 5 × 2

# Or multi-discrete
action_space = spaces.MultiDiscrete([9, 5, 2])
```

## Key Design Choices

**Why direction-based?**
- No need to select specific territory (512×512 = 262K options)
- Natural for expansion ("push east", "retreat west")
- Fast to compute and execute

**Why aggregate enemies?**
- Can't track 50+ opponents individually
- Only care about "where are enemies" not "who is player #23"
- Much smaller state space

**Why 128×128 resolution?**
- Balance between detail and speed
- Enough to see spatial patterns
- 4× smaller than 512×512

**Why these global features?**
- Population ratio: Core mechanic (40-50% optimal)
- Territory %: Win condition (80%)
- Rank: Survival instinct
- Border pressure: Tactical awareness

---

**Next**: [03_REWARD_TRAINING.md](03_REWARD_TRAINING.md)
