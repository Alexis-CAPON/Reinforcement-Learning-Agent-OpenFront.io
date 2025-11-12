# Map Selection and Cropping Guide

## Overview

Phase 4 supports **realistic game maps** with terrain features (mountains, coastlines, relief) and **flexible cropping** to focus visualization on specific regions.

**Important**: Your RL model is playing the **REAL GAME** on these maps! The terrain is not just visual - mountains affect movement, coastlines require boats, and all game mechanics work exactly as in the full OpenFront.io game. Cropping only affects what you SEE, not what the game simulates - the full game still runs with all terrain and mechanics.

## Why Use Maps and Cropping?

### Benefits of Real Maps
- ✅ **Realistic terrain**: Mountains, water, coastlines
- ✅ **Strategic gameplay**: Terrain affects movement and defense
- ✅ **Visual appeal**: Professional look with geographic features
- ✅ **Better training**: More realistic scenarios for RL agents

### Benefits of Cropping
- ✅ **Performance**: Smaller render region = faster updates
- ✅ **Focus**: Zoom into action-heavy areas
- ✅ **Clarity**: Better visualization of model behavior
- ✅ **Flexibility**: Adjust view without changing game logic

## Available Maps

| Map | Dimensions | Description |
|-----|-----------|-------------|
| **australia** | 2000×1500 | Realistic Australia map with coastlines, mountains, and varied terrain (default) |
| **world** | 2000×1000 | World map with continents and oceans |
| **europe** | 1500×1200 | European region with detailed terrain |
| **plains** | Varies | Simple flat map without terrain features |

## Cropping Options

### 1. Centered Crop (Recommended)

**Format:** `center-WIDTHxHEIGHT`

Automatically centers the crop region on the map.

```bash
# Default: 512×384 centered crop
--crop center-512x384

# Larger view: 800×600
--crop center-800x600

# Smaller focused view: 400×300
--crop center-400x300
```

**How it works:**
```python
# For Australia (2000×1500) with center-512x384:
x = (2000 - 512) // 2  # = 744
y = (1500 - 384) // 2  # = 558
crop_region = {'x': 744, 'y': 558, 'width': 512, 'height': 384}
```

### 2. Custom Crop

**Format:** `x,y,width,height`

Specify exact coordinates for the crop region.

```bash
# Top-left corner focused
--crop 100,100,512,384

# Bottom-right region
--crop 1200,900,512,384

# Specific coordinates
--crop 744,558,512,384
```

**Coordinate system:**
- Origin (0,0) is top-left
- X increases rightward
- Y increases downward

### 3. No Cropping

**Format:** `none`

Use the full map without cropping.

```bash
--crop none
```

⚠️ **Warning**: Full maps are large and may impact performance!

## Usage Examples

### Basic Usage with Australia Map

```bash
python src/visualize_realtime.py \
  --model path/to/model.zip \
  --map australia \
  --crop center-512x384
```

### Larger Crop for Better Overview

```bash
python src/visualize_realtime.py \
  --model path/to/model.zip \
  --map australia \
  --crop center-800x600
```

### Focus on Specific Region

```bash
# Coastal region of Australia
python src/visualize_realtime.py \
  --model path/to/model.zip \
  --map australia \
  --crop 200,400,640,480
```

### Different Map with Custom Crop

```bash
python src/visualize_realtime.py \
  --model path/to/model.zip \
  --map world \
  --crop center-1000x500
```

### Full Map (No Cropping)

```bash
python src/visualize_realtime.py \
  --model path/to/model.zip \
  --map plains \
  --crop none
```

## How Cropping Works

### 1. Map Loading
The full map is loaded with all terrain features:
```typescript
// In game_bridge_visual.ts
const game = await setup(mapName, config, players, ...);
```

### 2. Crop Region Definition
Crop region is specified in game coordinates:
```typescript
interface CropRegion {
  x: number;        // Top-left x coordinate
  y: number;        // Top-left y coordinate
  width: number;    // Crop width in tiles
  height: number;   // Crop height in tiles
}
```

### 3. Player Spawning
Players spawn within the cropped region:
```typescript
const spawnCenterX = cropRegion.x + cropRegion.width / 2;
const spawnCenterY = cropRegion.y + cropRegion.height / 2;
const spawnRadius = Math.min(cropRegion.width, cropRegion.height) / 2 - 20;
```

### 4. Tile Extraction
Only tiles within the crop region are exported:
```typescript
for (let y = 0; y < height; y++) {
  for (let x = 0; x < width; x++) {
    const gameX = viewX + x;  // Actual game coordinate
    const gameY = viewY + y;
    const tile = game.ref(gameX, gameY);
    // Export with relative coordinates (0-based)
    tiles.push({ x, y, ...tileData });
  }
}
```

### 5. Client Rendering
Client receives cropped state and renders:
```typescript
// Tiles are in relative coordinates (0 to width-1, 0 to height-1)
visualState.tiles.forEach(tile => {
  renderTile(tile.x, tile.y, tile.owner_id, tile.is_mountain);
});
```

## Choosing Crop Size

### Recommended Sizes

| Use Case | Recommended Size | Description |
|----------|-----------------|-------------|
| **Default** | 512×384 | Good balance of detail and performance |
| **Detailed view** | 640×480 | More context, slightly slower |
| **Wide view** | 800×600 | See more of the map, may impact performance |
| **Focused** | 400×300 | Fast updates, less context |
| **Ultra-wide** | 1024×768 | Maximum context, slower updates |

### Performance Considerations

**Tile count = width × height**

- 512×384 = 196,608 tiles/frame ⚡ Fast
- 640×480 = 307,200 tiles/frame ⚡ Good
- 800×600 = 480,000 tiles/frame ⚠️ Moderate
- 1024×768 = 786,432 tiles/frame ⚠️ Slower

**Rule of thumb:** Keep below 500,000 tiles for smooth 60 FPS rendering.

## Advanced Usage

### Dynamic Cropping (Future Feature)

Currently, crop is set at initialization. Future versions may support:
- Dynamic crop following the agent
- Multiple simultaneous views
- Zoom controls

### Map Creation

To add custom maps:

1. Create map file in `base-game/resources/maps/YOUR_MAP/`
2. Include terrain data (mountains, water, etc.)
3. Use in Phase 4:
```bash
python src/visualize_realtime.py --model model.zip --map YOUR_MAP
```

## Troubleshooting

### "Players spawn outside visible region"

Check your crop coordinates don't exclude spawn points:
```bash
# Bad: Crop too small or offset
--crop 0,0,100,100

# Good: Centered crop with reasonable size
--crop center-512x384
```

### "Map looks stretched or distorted"

Maintain reasonable aspect ratios:
- ✅ 4:3 (640×480, 800×600)
- ✅ 16:9 (854×480, 1280×720)
- ✅ 3:2 (720×480)
- ❌ Avoid extreme ratios (e.g., 1000×100)

### "Terrain doesn't show"

Make sure you're using a map with terrain features:
```bash
# Has terrain
--map australia  ✅
--map world      ✅
--map europe     ✅

# No terrain
--map plains     ❌
```

## Summary

**Quick Reference:**

```bash
# Best for most cases
python src/visualize_realtime.py --model MODEL.zip --map australia --crop center-512x384

# Need more context
python src/visualize_realtime.py --model MODEL.zip --map australia --crop center-800x600

# Focus on specific area
python src/visualize_realtime.py --model MODEL.zip --map australia --crop 500,400,640,480

# Full map view
python src/visualize_realtime.py --model MODEL.zip --map australia --crop none
```

**Key Points:**
- 🗺️ Use `australia` for realistic terrain (default)
- ✂️ Use `center-WxH` for automatic centering
- 🎯 Default `center-512x384` works great for most cases
- ⚡ Smaller crops = better performance
- 🔍 Larger crops = more context
