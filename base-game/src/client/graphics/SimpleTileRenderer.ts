/**
 * Simple Tile Renderer for RL Visualization
 * Renders tiles with terrain colors
 */

import * as PIXI from 'pixi.js';

interface TileData {
  x: number;
  y: number;
  owner_id: number;
  terrain_type: number;
  is_city: boolean;
  is_mountain: boolean;
}

interface PlayerData {
  id: number;
  color: string;
}

export class SimpleTileRenderer {
  private container: PIXI.Container;
  private tileSize: number = 4;
  private tileGraphics: Map<string, PIXI.Graphics> = new Map();

  // Terrain colors
  private readonly TERRAIN_COLORS: { [key: number]: number } = {
    0: 0x88cc88,  // Plains (light green)
    1: 0x4488cc,  // Water (blue)
    2: 0x8b7355,  // Mountains (brown)
    3: 0xcccc88,  // Desert (tan)
    4: 0x88aa88,  // Forest (darker green)
  };

  constructor(container: PIXI.Container) {
    this.container = container;
  }

  render(tiles: TileData[], players: PlayerData[], mapWidth: number, mapHeight: number) {
    // Clear existing tiles
    this.container.removeChildren();
    this.tileGraphics.clear();

    // Create player color map
    const playerColors = new Map<number, number>();
    players.forEach(player => {
      playerColors.set(player.id, parseInt(player.color.replace('#', ''), 16));
    });

    // Render each tile
    tiles.forEach(tile => {
      const graphics = new PIXI.Graphics();
      const key = `${tile.x},${tile.y}`;

      // Determine color
      let color: number;
      let alpha = 1.0;

      if (tile.owner_id > 0) {
        // Tile is owned by a player
        color = playerColors.get(tile.owner_id) || 0xcccccc;
      } else {
        // Neutral tile - show terrain color
        color = this.TERRAIN_COLORS[tile.terrain_type] || 0x888888;
      }

      // Draw tile
      graphics.beginFill(color, alpha);
      graphics.drawRect(
        tile.x * this.tileSize,
        tile.y * this.tileSize,
        this.tileSize,
        this.tileSize
      );
      graphics.endFill();

      // Draw border for mountains
      if (tile.is_mountain) {
        graphics.lineStyle(1, 0x000000, 0.3);
        graphics.drawRect(
          tile.x * this.tileSize,
          tile.y * this.tileSize,
          this.tileSize,
          this.tileSize
        );
      }

      // Draw city marker
      if (tile.is_city) {
        graphics.beginFill(0xffff00, 0.8);
        graphics.drawCircle(
          tile.x * this.tileSize + this.tileSize / 2,
          tile.y * this.tileSize + this.tileSize / 2,
          this.tileSize / 2
        );
        graphics.endFill();
      }

      this.container.addChild(graphics);
      this.tileGraphics.set(key, graphics);
    });
  }

  setTileSize(size: number) {
    this.tileSize = size;
  }

  clear() {
    this.container.removeChildren();
    this.tileGraphics.clear();
  }
}
