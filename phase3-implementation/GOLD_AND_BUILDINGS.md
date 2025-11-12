# Gold and Buildings in OpenFront.io

## What You Asked

1. **"Why don't we have gold?"** - We DO have gold! It's tracked but wasn't displayed in the visualizer. ✅ **FIXED NOW!**
2. **"What can be built?"** - **Cities!** That's the only building type in OpenFront.io.

## Gold System

### How Gold Works

**Gold is the game's currency:**
- Earned automatically from your territory
- More tiles = more gold income per turn
- Used to build cities
- Cities generate even more gold (investment!)

**Gold Generation:**
```
Gold per turn = (Number of tiles you own) × (Base income rate)
Cities = Bonus income multiplier
```

### What You Can Do With Gold

**Only one thing: Build Cities!**
- Cost: ~1000 gold (varies by game settings)
- Benefit: Increases income, strengthens territory
- Strategic placement: Interior tiles (not borders)

### Gold in the RL Agent

**The agent can see gold in observations:**
- Global feature #8: `Gold / 50000` (normalized)
- Helps agent decide when to build cities
- Agent learns: "Save gold → Build city → More income → More cities"

**Now visible in HTML visualizer:**
- 💰 Gold stat card shows current gold amount
- Updates in real-time as agent earns/spends gold

## Cities

### What are Cities?

**Cities are the only building in OpenFront.io:**
- Permanent structures on tiles
- Generate bonus gold income
- Strengthen your economy
- Shown as **white center dots** on map tiles

### City Benefits

1. **Economic:**
   - Generate additional gold per turn
   - Pay for themselves over time (investment)
   - Allow building more cities (compound growth!)

2. **Strategic:**
   - Control key map locations
   - Show territory development
   - Indicate economic strength

### City Placement

**Good locations:**
- Interior tiles (safe from attack)
- Central positions (not borders)
- Connected territory regions

**Bad locations:**
- Border tiles (can be captured)
- Isolated tiles (easy targets)
- Near enemy territory (risky)

### Cities in the Agent

**Building Decision (Action Space):**
```python
# Action components:
direction = action // 10    # Which way to attack
intensity = (action % 10) // 2  # How many troops
build = action % 2          # Whether to build city (0 or 1)

# If build=1, agent tries to build city
```

**Building Logic:**
```python
# In environment.py _execute_action():
if build == 1:
    if hasattr(self.game, 'can_build_city') and self.game.can_build_city():
        location = self._find_safe_location()  # Find interior tile
        if location is not None:
            self.game.build_city(location)
```

**Now visible in visualizer:**
- 🏛️ Cities stat card shows number of cities
- White dots on map show city locations
- Updates as agent builds/loses cities

## Visualizer Updates (Just Applied!)

### Before (Missing Data):
```
Stats displayed:
- Territory %
- Tiles
- Troops
- Rank
- Action

Missing:
- Gold ❌
- Cities ❌
```

### After (Complete Data):
```
Stats displayed:
- Territory %
- Tiles
- Troops
- Gold 💰 ← NEW!
- Cities 🏛️ ← NEW!
- Rank
- Action
```

## How to See Gold and Cities

### 1. In Training Logs:
```python
# Episode info now includes (from environment.py):
info = {
    'tiles': current_state.tiles_owned,
    'troops': current_state.population,
    'territory_pct': current_state.territory_pct,
    'rank': current_state.rank,
    # Gold is in the state (not logged yet, but tracked!)
}
```

### 2. In HTML Visualizer:
```bash
# Create visualization
python src/visualize_game.py --model model.zip --num-bots 10

# Open HTML file - you'll see:
# - Territory: 12.5%
# - Tiles: 45
# - Troops: 8500
# - Gold 💰: 2340  ← NEW!
# - Cities 🏛️: 3    ← NEW!
# - Rank: 5/11
```

### 3. On the Map:
- **Cities shown as white center dots** on colored tiles
- Example: Red tile (your territory) with white center = your city

## Why Gold & Cities Matter for RL

### Learning Objectives:

**Without Cities (basic strategy):**
```
Agent learns: Attack → Expand territory → Get more troops → Attack more
```

**With Cities (advanced strategy):**
```
Agent learns:
1. Save gold (don't waste)
2. Build cities in safe spots
3. Cities = more gold
4. More gold = more cities
5. Economic power = military power
```

**This is more realistic and complex!**

## Example Agent Behavior

### Early Game (No gold):
```
Step 100:
- Territory: 5%
- Troops: 3000
- Gold: 120 💰 (not enough!)
- Cities: 0 🏛️
- Action: E @ 50% (attacking)
```

### Mid Game (Building):
```
Step 500:
- Territory: 15%
- Troops: 8500
- Gold: 1240 💰 (enough!)
- Cities: 0 🏛️
- Action: S @ 35% ⚙️ (attacking AND building!)
  → City built! Gold: 240 💰, Cities: 1 🏛️
```

### Late Game (Economic power):
```
Step 1500:
- Territory: 35%
- Troops: 25000
- Gold: 5670 💰 (rich!)
- Cities: 5 🏛️ (generating income!)
- Action: NE @ 75% (strong attacks)
```

**Cities create compound growth:**
- More cities → More gold → More cities → Economic dominance!

## Training Impact

### Reward Function:
Currently gold/cities are NOT directly rewarded, but they help indirectly:
```python
# Current rewards:
- Territory gain: +50 per 1%  ✅ (cities help hold territory)
- Enemy killed: +5000         ✅ (economic power = military power)
- Victory: +10,000            ✅ (cities help win)

# Could add (future enhancement):
- Build city: +10 per city
- Gold income: +0.001 per gold earned
```

### Agent Learning Curve:

**Phase 1 (Basics):**
- Agent learns: "Attack to expand"
- Ignores gold/cities (too complex)

**Phase 2 (Economy):**
- Agent learns: "More territory = more gold"
- Occasionally builds cities randomly

**Phase 3 (Strategy):**
- Agent learns: "Cities in safe spots = win"
- Strategic city placement
- Economic warfare!

## Technical Implementation

### Game Bridge (TypeScript):
```typescript
// Extract gold and cities
const gold = Number(this.rlPlayer.gold());
const numCities = this.rlPlayer.units().filter(u => u.type() === 'City').length;

// Return in state
return {
  gold: gold,
  num_cities: numCities,
  // ... other state
};
```

### Environment (Python):
```python
# Extract from state
if hasattr(state, 'gold'):
    features[8] = state.gold / 50000.0  # Normalize

if hasattr(state, 'num_cities'):
    features[7] = state.num_cities  # Already 0-10 range
```

### Visualizer (HTML):
```javascript
// Display in stats
<div class="stat-card">
    <div class="stat-label">Gold 💰</div>
    <div class="stat-value" style="color: #FFD700">
        ${rlPlayer.gold.toFixed(0)}
    </div>
</div>

<div class="stat-card">
    <div class="stat-label">Cities 🏛️</div>
    <div class="stat-value" style="color: #AAAAFF">
        ${rlPlayer.num_cities}
    </div>
</div>
```

## Summary

**To your questions:**

1. ✅ **Gold**: We DO have it! Now visible in visualizer (💰 stat card)
2. ✅ **Buildings**: Only cities! Now visible in visualizer (🏛️ stat card + white dots on map)

**What changed:**
- Added `gold` and `num_cities` to visual game bridge
- Added Gold 💰 stat card to HTML visualizer
- Added Cities 🏛️ stat card to HTML visualizer
- Cities already shown as white dots on map tiles

**Next time you visualize:**
```bash
python src/visualize_game.py --model model.zip --num-bots 10
```

You'll see gold accumulation and city building in action! 🎮💰🏛️
