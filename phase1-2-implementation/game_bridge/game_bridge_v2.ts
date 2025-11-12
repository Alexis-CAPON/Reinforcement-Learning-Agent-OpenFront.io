/**
 * Game Bridge V2 - TypeScript/Node.js interface for RL training
 *
 * Based on patterns from base-game test suite.
 * Uses the actual working API from tests/util/Setup.ts
 */

import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Import game types and functions
import { createGame, Game } from '../../base-game/src/core/game/GameImpl.js';
import { PlayerInfo, PlayerType, Player, TerraNullius } from '../../base-game/src/core/game/Game.js';
import { genTerrainFromBin } from '../../base-game/src/core/game/TerrainMapLoader.js';
import { GameMode, GameType, Difficulty } from '../../base-game/src/core/Schemas.js';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution.js';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution.js';
import { RLConfig } from './RLConfig.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface GameState {
  tiles_owned: number;
  troops: number;
  gold: number;
  max_troops: number;
  enemy_tiles: number;
  border_tiles: number;
  cities: number;
  tick: number;
  has_won: boolean;
  has_lost: boolean;
  game_over: boolean;
}

interface Neighbor {
  neighbor_idx: number;
  enemy_player_id: number;
  tile_x: number;
  tile_y: number;
  enemy_troops: number;
}

class GameBridge {
  private game: Game | null = null;
  private rlPlayer: Player | null = null;
  private aiPlayer: Player | null = null;
  private config: RLConfig;
  private tickIntervalMs: number = 100;
  private currentTick: number = 0;
  private maxTicks: number = 1000;

  constructor() {
    this.config = new RLConfig(this.tickIntervalMs);
    this.log('GameBridge V2 initialized');
  }

  /**
   * Load map from binary files (like in tests/util/Setup.ts)
   */
  private async loadMap(mapName: string): Promise<{
    gameMap: any;
    miniGameMap: any;
    manifest: any;
  }> {
    // Use test maps from base-game
    const mapsDir = path.join(__dirname, '../../base-game/tests/testdata/maps');
    const mapDir = path.join(mapsDir, mapName);

    this.log(`Loading map from: ${mapDir}`);

    // Read binary files
    const mapBinPath = path.join(mapDir, 'map.bin');
    const miniMapBinPath = path.join(mapDir, 'mini_map.bin');
    const manifestPath = path.join(mapDir, 'manifest.json');

    if (!fs.existsSync(mapBinPath)) {
      throw new Error(`Map not found: ${mapName} at ${mapBinPath}`);
    }

    const mapBinBuffer = fs.readFileSync(mapBinPath);
    const miniMapBinBuffer = fs.readFileSync(miniMapBinPath);
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

    // Generate terrain maps
    const gameMap = await genTerrainFromBin(manifest.map, new Uint8Array(mapBinBuffer));
    const miniGameMap = await genTerrainFromBin(manifest.mini_map, new Uint8Array(miniMapBinBuffer));

    return { gameMap, miniGameMap, manifest };
  }

  /**
   * Initialize a new game (based on tests/util/Setup.ts pattern)
   */
  async reset(mapName: string = 'plains', difficulty: string = 'easy', tickInterval?: number): Promise<GameState> {
    try {
      // Update tick interval if provided
      if (tickInterval !== undefined && tickInterval !== this.tickIntervalMs) {
        this.tickIntervalMs = tickInterval;
        this.config = new RLConfig(tickInterval);
        this.log(`Updated tick interval to ${tickInterval}ms`);
      }

      this.log(`Resetting game: map=${mapName}, difficulty=${difficulty}`);

      // Load map
      const { gameMap, miniGameMap, manifest } = await this.loadMap(mapName);
      this.log(`Map loaded: ${manifest.map.width}x${manifest.map.height}`);

      // Create player infos
      const rlPlayerInfo = new PlayerInfo(
        'RL_Agent',
        PlayerType.Human,
        null,
        'rl_player_id'
      );

      const aiPlayerType = this.getAIType(difficulty);
      const aiPlayerInfo = new PlayerInfo(
        'AI_Opponent',
        aiPlayerType,
        null,
        'ai_player_id'
      );

      // Create game (like in Setup.ts)
      this.game = createGame(
        [rlPlayerInfo, aiPlayerInfo],
        [],  // No nations (they're in manifest)
        gameMap,
        miniGameMap,
        this.config
      );

      this.log('Game created successfully');

      // Get player references
      this.rlPlayer = this.game.player('rl_player_id');
      this.aiPlayer = this.game.player('ai_player_id');

      // Add spawn executions (use first two spawn points from manifest)
      const spawnPoints = manifest.nations || [];
      if (spawnPoints.length < 2) {
        throw new Error('Map needs at least 2 spawn points');
      }

      const rlSpawn = this.game.ref(spawnPoints[0].x, spawnPoints[0].y);
      const aiSpawn = this.game.ref(spawnPoints[1].x, spawnPoints[1].y);

      this.game.addExecution(
        new SpawnExecution(rlPlayerInfo, rlSpawn),
        new SpawnExecution(aiPlayerInfo, aiSpawn)
      );

      // Execute spawn phase (like in tests)
      this.log('Executing spawn phase...');
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      this.currentTick = Number(this.game.ticks());
      this.log(`Spawn phase complete, starting at tick ${this.currentTick}`);

      return this.getState();

    } catch (error: any) {
      this.logError('Reset failed', error);
      throw error;
    }
  }

  /**
   * Execute one game tick
   */
  tick(): GameState {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    this.game.executeNextTick();
    this.currentTick++;

    return this.getState();
  }

  /**
   * Get current game state
   */
  getState(): GameState {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) {
      throw new Error('Game not initialized');
    }

    const rlTiles = this.rlPlayer.numTilesOwned();
    const aiTiles = this.aiPlayer.numTilesOwned();

    return {
      tiles_owned: rlTiles,
      troops: this.rlPlayer.troops(),
      gold: Number(this.rlPlayer.gold()),  // BigInt to number
      max_troops: 100000,  // Placeholder
      enemy_tiles: aiTiles,
      border_tiles: this.rlPlayer.borderTiles().size,
      cities: this.rlPlayer.units().filter(u => u.type() === 'City').length,
      tick: this.currentTick,
      has_won: !this.aiPlayer.isAlive(),
      has_lost: !this.rlPlayer.isAlive(),
      game_over: !this.rlPlayer.isAlive() || !this.aiPlayer.isAlive() || this.currentTick >= this.maxTicks
    };
  }

  /**
   * Get attackable neighbors
   */
  getAttackableNeighbors(): Neighbor[] {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) {
      return [];
    }

    const neighbors: Neighbor[] = [];

    // Get all border tiles
    const borderTiles = Array.from(this.rlPlayer.borderTiles());

    // For each border tile, check adjacent tiles owned by enemy
    for (const borderTile of borderTiles) {
      const x = this.game.x(borderTile);
      const y = this.game.y(borderTile);

      // Check 4 adjacent tiles (up, down, left, right)
      const adjacentOffsets = [
        { dx: 0, dy: -1 },  // up
        { dx: 0, dy: 1 },   // down
        { dx: -1, dy: 0 },  // left
        { dx: 1, dy: 0 }    // right
      ];

      for (const offset of adjacentOffsets) {
        const adjX = x + offset.dx;
        const adjY = y + offset.dy;

        // Check bounds
        if (adjX < 0 || adjX >= this.game.width() || adjY < 0 || adjY >= this.game.height()) {
          continue;
        }

        const adjTile = this.game.ref(adjX, adjY);
        const owner = this.game.owner(adjTile);

        // Check if owned by AI opponent
        if (owner.isPlayer() && (owner as Player).id() === this.aiPlayer.id()) {
          neighbors.push({
            neighbor_idx: neighbors.length,
            enemy_player_id: 2,  // AI is player 2
            tile_x: adjX,
            tile_y: adjY,
            enemy_troops: (owner as Player).troops()
          });

          // Limit to 8 neighbors max (as per action space)
          if (neighbors.length >= 8) {
            return neighbors;
          }
        }
      }
    }

    return neighbors;
  }

  /**
   * Attack a tile
   */
  attackTile(tile_x: number, tile_y: number): void {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) {
      throw new Error('Game not initialized');
    }

    const targetTile = this.game.ref(tile_x, tile_y);
    const owner = this.game.owner(targetTile);

    // Check if we can attack
    if (!this.rlPlayer.canAttack(targetTile)) {
      this.log(`Cannot attack tile (${tile_x}, ${tile_y})`);
      return;
    }

    // Create attack execution (with minimal troops to start)
    const attackTroops = Math.min(1000, Math.floor(this.rlPlayer.troops() * 0.5));

    this.log(`Creating attack at (${tile_x}, ${tile_y}) with ${attackTroops} troops`);

    this.game.addExecution(
      new AttackExecution(
        attackTroops,
        this.rlPlayer,
        owner.isPlayer() ? (owner as Player).id() : 'terra_nullius'
      )
    );
  }

  /**
   * Get AI player type from difficulty string
   */
  private getAIType(difficulty: string): PlayerType {
    // Base game only has Bot, Human, and FakeHuman
    // FakeHuman is the AI that acts like a human
    return PlayerType.FakeHuman;
  }

  private log(message: string): void {
    console.error(`[GameBridge V2] ${message}`);
  }

  private logError(message: string, error: any): void {
    console.error(`[GameBridge V2 ERROR] ${message}:`, error);
  }
}

// ============================================================================
// IPC Interface (same pattern as test_hello.js)
// ============================================================================

const bridge = new GameBridge();

console.error('[GameBridge V2] Starting...');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

console.error('[GameBridge V2] Readline interface created');

rl.on('line', async (line) => {
  try {
    const command = JSON.parse(line);
    console.error(`[GameBridge V2] Received command: ${command.type}`);

    let response: any = { type: 'response' };

    switch (command.type) {
      case 'reset':
        response.state = await bridge.reset(
          command.map_name || 'plains',
          command.difficulty || 'easy',
          command.tick_interval
        );
        break;

      case 'tick':
        response.state = bridge.tick();
        break;

      case 'get_state':
        response.state = bridge.getState();
        break;

      case 'get_attackable_neighbors':
        response.neighbors = bridge.getAttackableNeighbors();
        break;

      case 'attack_tile':
        bridge.attackTile(command.tile_x, command.tile_y);
        response.success = true;
        break;

      case 'shutdown':
        console.error('[GameBridge V2] Shutdown requested');
        response.message = 'Goodbye!';
        console.log(JSON.stringify(response));
        process.exit(0);

      default:
        response = {
          type: 'error',
          message: `Unknown command type: ${command.type}`
        };
    }

    console.log(JSON.stringify(response));

  } catch (error: any) {
    console.error(`[GameBridge V2 ERROR] ${error.message}`);
    console.error(error.stack);
    const errorResponse = {
      type: 'error',
      message: error.message
    };
    console.log(JSON.stringify(errorResponse));
  }
});

rl.on('close', () => {
  console.error('[GameBridge V2] Input stream closed');
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  console.error(`[GameBridge V2 FATAL] Uncaught exception: ${error.message}`);
  console.error(error.stack);
  process.exit(1);
});

console.error('[GameBridge V2] Ready to receive commands');
