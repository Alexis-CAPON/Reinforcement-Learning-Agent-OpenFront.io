# Phase 4 Testing/Visualization Setup - Detailed Analysis

## Executive Summary

Phase 4 is a **real-time RL visualizer** that displays trained models playing the game with full game client rendering. It differs from Phase 3 (training) in that it uses **inference mode** (deterministic policy), focuses on visualization rather than learning, and provides both the full game UI and overlay visualizations of model decisions.

---

## 1. MAP CONFIGURATION

### Map Used in Phase 4
**Default**: `australia` (maps to game internal name `Australia`)

**Available Maps in Phase 4**:
- Australia (default, full map)
- Australia_100x100 (cropped region, recommended for visualization)
- World
- Europe
- Asia
- And many others in `/base-game/map-generator/generated/maps/`

### Map Selection Method
From command line:
```bash
python src/visualize_realtime.py --model model.zip --map australia_100x100
```

URL parameter in browser:
```
http://localhost:8080/rl-index.html?map=australia_100x100
```

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/src/visualize_realtime.py` (lines 349-352)

---

## 2. OPPONENTS & GAME CONDITIONS

### Number of Bots
**Default**: 10 opponents
**Configurable**: 1-50 bots via `--num-bots` flag

From code:
```python
parser.add_argument(
    '--num-bots',
    type=int,
    default=10,
    help='Number of bot opponents (default: 10)'
)
```

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/src/visualize_realtime.py` (lines 331-334)

### Opponent Behavior
- **Bot Type**: AI_Bot_1, AI_Bot_2, ... (controlled by game engine)
- **Difficulty**: Hardcoded to `Easy` in visualization
- **Spawn Pattern**: Circular distribution around map center (or crop region)

**Code Reference**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/game_bridge/game_bridge_visual.ts` (lines 154-160)

```typescript
// RL Agent (1 player) + bots
const players: PlayerInfo[] = [new PlayerInfo('RL_Agent', PlayerType.Human, null, 'RL_Agent')];
for (let i = 1; i <= numBots; i++) {
  players.push(new PlayerInfo(`AI_Bot_${i}`, PlayerType.Bot, null, `AI_Bot_${i}`));
}
```

### Spawning Strategy
Players spawn in a **circular pattern** around map center with configurable crop region:

```typescript
// Spawn calculation (game_bridge_visual.ts, lines 215-227)
const spawnCenterX = this.cropRegion ? this.cropRegion.x + this.cropRegion.width / 2 : fullWidth / 2;
const spawnCenterY = this.cropRegion ? this.cropRegion.y + this.cropRegion.height / 2 : fullHeight / 2;
const spawnRadius = this.cropRegion ? Math.min(this.cropRegion.width, this.cropRegion.height) / 2 - 20 : Math.min(fullWidth, fullHeight) / 2 - 20;

// Players distributed around spawn center
for (let i = 0; i < numPlayers; i++) {
  const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;
  const baseX = Math.floor(spawnCenterX + spawnRadius * Math.cos(angle));
  const baseY = Math.floor(spawnCenterY + spawnRadius * Math.sin(angle));
  // ... search for valid land tile nearby ...
}
```

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/game_bridge/game_bridge_visual.ts` (lines 210-287)

---

## 3. MODEL LOADING & INFERENCE MODE

### Model Loading
Phase 4 loads trained **PPO models** from Phase 3:

```python
# visualize_realtime.py (line 46)
self.model = PPO.load(model_path)
```

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/src/visualize_realtime.py` (lines 44-46)

### Inference Mode Configuration
Model runs in **DETERMINISTIC MODE** (always selects greedy action):

```python
# visualize_realtime.py (lines 167-170)
action, action_details = self.model_extractor.predict_with_details(
    obs,
    deterministic=True  # ← Inference mode: no exploration
)
```

**Key Point**: `deterministic=True` means:
- No random exploration
- Always picks action with highest probability
- Consistent, repeatable behavior for visualization

### Exploration Disabled
- **Exploration Flag**: Not used in Phase 4
- **Action Selection**: Pure exploitation (argmax policy)
- **Randomness**: Only in initial agent spawning angle (`angleOffset`)

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/src/visualize_realtime.py` (lines 166-170)

---

## 4. GAME RULES & CONFIGURATION DIFFERENCES: PHASE 4 vs PHASE 3

### Phase 3 (Training)
**Configuration**: Battle Royale with extensive options

```python
# environment.py
class OpenFrontEnv(gym.Env):
    def __init__(self, game_interface=None, num_bots: int = 50, map_name: str = 'plains', frame_stack: int = 4):
```

**Typical Training Setup**:
- Maps: plains, asia, etc. (default)
- Bots: 10-50
- Frame stack: 4 frames
- Infinite exploration via epsilon-greedy

### Phase 4 (Visualization/Testing)
**Configuration**: Simplified for visualization

```typescript
// game_bridge_visual.ts (lines 180-192)
const gameConfig: GameConfig = {
  gameMap: GameMapType.Asia,                    // Placeholder (overridden by map_name)
  gameMode: GameMode.FFA,                       // Free For All
  gameType: GameType.Singleplayer,              // Single player with bots
  difficulty: Difficulty.Easy,                  // ← HARDCODED
  disableNPCs: false,                           // Allow NPC spawning
  donateGold: false,                            // No gold donations
  donateTroops: false,                          // No troop donations
  bots: 0,                                      // Game manages bots
  infiniteGold: false,                          // Standard gold mechanics
  infiniteTroops: false,                        // Standard troop mechanics
  instantBuild: false,                          // Standard build times
};
```

**File Location**: `/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/phase4-implementation/game_bridge/game_bridge_visual.ts` (lines 180-192)

### KEY DIFFERENCES

| Aspect | Phase 3 (Training) | Phase 4 (Visualization) |
|--------|-------------------|------------------------|
| **Mode** | Training with exploration | Inference/testing only |
| **Difficulty** | Variable (Easy/Medium/Hard) | **Hardcoded to Easy** |
| **Bots** | 10-50 configurable | Configurable (default 10) |
| **NPCs** | Typically enabled | **Enabled (may affect gameplay)** |
| **Gold System** | Standard | **Standard** |
| **Deterministic** | No (random actions) | **Yes (greedy policy)** |
| **Model Mode** | Learning/updating weights | **Inference only** |

### Critical Config: Game Rules
Both phases use **same core game mechanics**:
- Territory-based combat system
- Gold generation and unit building
- Fallout mechanics
- Alliance system (not used in basic battle royale)
- NPC spawning
- Troop movement and combat

---

## 5. HOW VISUALIZER RUNS THE GAME

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│ Python Process (Phase 4)                                    │
│  RealtimeVisualizer (main runner)                           │
│    ↓                                                        │
│  PPO Model (inference mode, deterministic=True)            │
│    ↓                                                        │
│  VisualGameWrapper                                          │
│    ↓                                                        │
│  game_bridge_visual.ts (Node.js subprocess)               │
│    ↓                                                        │
│  Game Engine (Phase 3's battle royale implementation)      │
│    ↓                                                        │
│  GameUpdateViewData (game state serialization)            │
│    ↓                                                        │
│  WebSocket Server (broadcasts to browser)                 │
│    ↓                                                        │
│  Browser Client                                            │
│    ↓                                                        │
│  RLWorkerClient (drop-in replacement for Web Worker)      │
│    ↓                                                        │
│  ClientGameRunner → GameView → GameRenderer → Full Game UI │
│    ↓                                                        │
│  RLOverlay (displays model decisions)                      │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Execution

#### 1. Initialization (visualize_realtime.py)

```python
# Lines 437-443
visualizer = RealtimeVisualizer(
    model_path=args.model,
    num_bots=args.num_bots,
    websocket_host=args.ws_host,
    websocket_port=args.ws_port,
    map_name=args.map,
    crop_region=crop_region  # Optional: center-800x600 or custom
)
```

#### 2. Model & Game Setup

```python
# visualize_realtime.py, lines 44-58
self.model = PPO.load(model_path)                    # Load trained model
self.model_extractor = ModelStateExtractor(...)      # Extract model internals
self.visual_game = VisualGameWrapper(...)            # Create game wrapper
```

**VisualGameWrapper** (visual_game_wrapper.py):
- Spawns `game_bridge_visual.ts` as Node.js subprocess
- Communicates via stdin/stdout JSON protocol
- Manages game commands (reset, tick, attack_direction)

#### 3. Game Reset

```python
# visualize_realtime.py, lines 107-108
visual_response = self.visual_game.reset()

# Sends to subprocess:
{
  'type': 'reset',
  'num_bots': 10,
  'map_name': 'australia_100x100'
  'crop': {'x': 600, 'y': 450, 'width': 800, 'height': 600}  # Optional
}
```

**In game_bridge_visual.ts**:
```typescript
// Lines 142-309
async initialize(numBots, mapName, crop?) {
  // 1. Load map binary files
  const mapBinBuffer = fs.readFileSync(mapBinPath);
  // 2. Create game with Phase 3's Game object
  this.game = createGame(players, [], gameMap, miniGameMap, config);
  // 3. Spawn players in circle
  // 4. Execute spawn phase
  // 5. Return initial visual state
}
```

#### 4. Game Loop (Lines 104-253 of visualize_realtime.py)

```python
while not done:
    # Step 1: Check pause/speed controls
    if not self.ws_server.should_step():
        await asyncio.sleep(0.1)
        continue

    # Step 2: Get model action (DETERMINISTIC MODE)
    action, action_details = self.model_extractor.predict_with_details(
        obs,
        deterministic=True  # ← Critical: no exploration
    )

    # Step 3: Execute action in game
    direction = action_details['direction']          # N, NE, E, SE, S, SW, W, NW, WAIT
    intensity = action_details['intensity']          # 0.15-0.75
    self.visual_game.attack_direction(direction, intensity)

    # Step 4: Tick game
    visual_response = self.visual_game.tick()

    # Step 5: Extract game state
    visual_state = visual_response.get('state')
    game_update = visual_response.get('gameUpdate')  # GameUpdateViewData

    # Step 6: Broadcast to browser
    await self.ws_server.broadcast_game_update(visual_state, game_update)

    # Step 7: Broadcast model decisions
    await self.ws_server.broadcast_model_state(
        tick=self.step_count,
        observation=action_details['raw_observation'],
        action_dict={...},
        value=action_details['value_estimate'],
        reward=reward,
        cumulative_reward=self.cumulative_reward
    )

    # Step 8: Wait for next tick
    await asyncio.sleep(0.05)  # 20 ticks/second
```

#### 5. Browser Rendering (RLMain.ts)

The browser client receives WebSocket messages:

```typescript
// RLWorkerClient.ts, lines 82-97
if (message.type === 'game_update' && message.gameUpdate) {
    const gameUpdate = message.gameUpdate;  // GameUpdateViewData
    if (this.gameUpdateCallback) {
        this.gameUpdateCallback(gameUpdate);
    }
}

// RLOverlay.ts displays model state
if (message.type === 'model_state') {
    window.dispatchEvent(new CustomEvent('rl-model-state', {
        detail: message
    }));
}
```

### WebSocket Message Format

#### Game Update (every tick)
```json
{
  "type": "game_update",
  "gameUpdate": {
    "tick": 123,
    "packedTileUpdates": [1234, 5678, ...],  // Tile ownership changes
    "updates": {
      "1": [/* PlayerUpdateViewData */],
      "2": [/* UnitUpdateViewData */],
      ...
    },
    "playerNameViewData": {
      "player_1": {"x": 100, "y": 200, "width": 50, "height": 20}
    }
  }
}
```

#### Model State (every tick, for overlay)
```json
{
  "type": "model_state",
  "tick": 123,
  "action": {
    "direction_probs": [0.1, 0.15, 0.2, ...],  // 9 directions
    "intensity_probs": [0.1, 0.2, 0.3, 0.25, 0.15],  // 5 intensities
    "build_prob": 0.02,
    "selected_action": 14,
    "direction": "NE",
    "intensity": 0.45,
    "build": false
  },
  "value_estimate": 42.5,
  "reward": 1.2,
  "cumulative_reward": 156.8
}
```

---

## 6. FILES & LOCATIONS SUMMARY

### Python Backend
| File | Purpose | Key Config |
|------|---------|-----------|
| `/phase4-implementation/src/visualize_realtime.py` | Main entry point | Default: 10 bots, australia map |
| `/phase4-implementation/src/visual_game_wrapper.py` | Game interface | Spawns game_bridge subprocess |
| `/phase4-implementation/src/websocket_server.py` | WebSocket server | Port 8765 |
| `/phase4-implementation/src/model_state_extractor.py` | Model introspection | Extracts probabilities, value |
| `/phase4-implementation/game_bridge/game_bridge_visual.ts` | Game engine | Uses Phase 3 Game object |

### TypeScript Frontend
| File | Purpose | Key Config |
|------|---------|-----------|
| `/base-game/src/client/RLMain.ts` | Entry point | Loads map from URL params |
| `/base-game/src/client/RLWorkerClient.ts` | WebSocket bridge | Connects to Python server |
| `/base-game/src/client/RLOverlay.ts` | Model overlay component | Displays action probabilities |
| `/base-game/src/client/rl-index.html` | HTML page | Full game UI |

### Key Configuration Files
| File | Config Parameter |
|------|-----------------|
| `visualize_realtime.py` | `--model`, `--num-bots`, `--map`, `--crop` |
| `game_bridge_visual.ts` | `numBots`, `mapName`, `crop` region |
| `RLMain.ts` | URL params: `ws`, `map`, `difficulty` |

---

## 7. START COMMAND & CONFIGURATION

### Command to Run Phase 4 Visualization
```bash
cd phase4-implementation

# Basic (10 bots, australia map)
python src/visualize_realtime.py --model ../phase3-implementation/runs/run_20250103_120000/openfront_final.zip

# With 100x100 map (recommended)
python src/visualize_realtime.py --model model.zip --map australia_100x100

# With custom bots and crop
python src/visualize_realtime.py \
  --model model.zip \
  --num-bots 25 \
  --map australia_100x100 \
  --crop center-800x600
```

### URL Parameters
```
http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia_100x100
```

---

## 8. QUICK REFERENCE: PHASE 3 vs PHASE 4

### Phase 3: TRAINING
- **Map**: Variable (plains, asia, etc.)
- **Bots**: 10-50
- **Mode**: Exploration enabled (epsilon-greedy)
- **Deterministic**: No
- **Model State**: Learning (weights updating)
- **Frame Stack**: 4 frames
- **Output**: Training metrics, model checkpoint
- **Game Rules**: Full configuration options

### Phase 4: VISUALIZATION/TESTING  
- **Map**: Configurable (default australia)
- **Bots**: Configurable (default 10)
- **Mode**: Deterministic=True (no exploration)
- **Deterministic**: Yes (always greedy)
- **Model State**: Inference only
- **Frame Stack**: 4 frames (matches training)
- **Output**: Real-time visualization in browser
- **Game Rules**: Simplified (Easy difficulty hardcoded)

---

## 9. KEY TECHNICAL INSIGHTS

### Why Deterministic Mode?
In Phase 4, `deterministic=True` in model prediction ensures:
- **Consistency**: Same input → same action (reproducible)
- **Clarity**: Can see model's true policy without noise
- **Visualization**: Model decisions are predictable and clear

### Spawn Region Cropping
The `--crop center-800x600` parameter:
- Focuses visualization on map center (800×600 region)
- Reduces rendering load for smooth visualization
- Helps zoom camera to action area
- Default behavior: full map spawning

### Frame Stacking (4 frames)
Both Phase 3 and 4 use 4-frame stacking:
- **Purpose**: Temporal context (motion detection)
- **Phase 3**: During training (learning movement patterns)
- **Phase 4**: During visualization (same architecture for inference)

### Game Bridge vs Direct Game
Phase 4 uses **subprocess-based game bridge** (game_bridge_visual.ts):
- Runs in separate Node.js process
- Communicates via stdin/stdout JSON
- Allows Python to interface with TypeScript game engine
- Provides GameUpdateViewData format for browser rendering

---

## 10. TROUBLESHOOTING DIFFERENCES

### If Phase 4 Shows Different Behavior Than Training
**Likely Causes**:
1. **Difficulty mismatch**: Phase 4 hardcoded to `Easy`
2. **Bot count**: Default 10 (training might use 50)
3. **Map size**: australia_100x100 vs full australia
4. **NPC spawning**: Enabled in Phase 4 (might affect early game)

**Solution**:
- Match Phase 4's `--num-bots` and `--map` to Phase 3's training configuration
- Check if training used custom difficulty settings

---

**Generated**: 2025-11-06  
**Phase 4 Status**: Production Ready  
**File Count**: 30+ files across TypeScript/Python  
**Architecture**: Modular WebSocket-based client/server
