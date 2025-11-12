/**
 * Game Bridge V3 - Simplified version using test utilities
 *
 * Directly imports and uses the test setup patterns from base-game.
 */

import * as readline from 'readline';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Import the setup utility from tests
import { setup, playerInfo } from '../../base-game/tests/util/Setup.js';
import { PlayerType, Player, Game } from '../../base-game/src/core/game/Game.js';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution.js';
import { GameMode, GameType, Difficulty } from '../../base-game/src/core/Schemas.js';

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
  private currentTick: number = 0;
  private maxTicks: number = 1000;

  constructor() {
    this.log('GameBridge V3 initialized (using test utilities)');
  }

  /**
   * Initialize game using test setup utility
   */
  async reset(mapName: string = 'plains', difficulty: string = 'easy', tickInterval?: number): Promise<GameState> {
    try {
      this.log(`Resetting game: map=${mapName}, difficulty=${difficulty}, tick=${tickInterval || 100}ms`);

      // Use the test setup utility
      this.game = await setup(
        mapName,
        {
          gameMode: GameMode.FFA,
          gameType: GameType.Singleplayer,
          difficulty: difficulty as Difficulty,
          infiniteGold: false,
          infiniteTroops: false,
          instantBuild: false,
        },
        [
          playerInfo('RL_Agent', PlayerType.Human),
          playerInfo('AI_Opponent', PlayerType.FakeHuman)
        ],
        path.join(__dirname, '../../base-game/tests/util')
      );

      this.log('Game created successfully');

      // Execute spawn phase
      this.log('Executing spawn phase...');
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      // Get player references
      const players = this.game.players();
      if (players.length < 2) {
        throw new Error(`Expected 2 players, got ${players.length}`);
      }

      this.rlPlayer = players[0];
      this.aiPlayer = players[1];

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
      gold: Number(this.rlPlayer.gold()),
      max_troops: 100000,
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
    const borderTiles = Array.from(this.rlPlayer.borderTiles());

    for (const borderTile of borderTiles) {
      const x = this.game.x(borderTile);
      const y = this.game.y(borderTile);

      const adjacentOffsets = [
        { dx: 0, dy: -1 }, { dx: 0, dy: 1 },
        { dx: -1, dy: 0 }, { dx: 1, dy: 0 }
      ];

      for (const offset of adjacentOffsets) {
        const adjX = x + offset.dx;
        const adjY = y + offset.dy;

        if (adjX < 0 || adjX >= this.game.width() || adjY < 0 || adjY >= this.game.height()) {
          continue;
        }

        const adjTile = this.game.ref(adjX, adjY);
        const owner = this.game.owner(adjTile);

        if (owner.isPlayer() && (owner as Player).id() === this.aiPlayer.id()) {
          neighbors.push({
            neighbor_idx: neighbors.length,
            enemy_player_id: 2,
            tile_x: adjX,
            tile_y: adjY,
            enemy_troops: (owner as Player).troops()
          });

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

    if (!this.rlPlayer.canAttack(targetTile)) {
      this.log(`Cannot attack tile (${tile_x}, ${tile_y})`);
      return;
    }

    const attackTroops = Math.min(1000, Math.floor(this.rlPlayer.troops() * 0.5));
    this.log(`Creating attack at (${tile_x}, ${tile_y}) with ${attackTroops} troops`);

    this.game.addExecution(
      new AttackExecution(attackTroops, this.rlPlayer, this.aiPlayer.id())
    );
  }

  private log(message: string): void {
    console.error(`[GameBridge V3] ${message}`);
  }

  private logError(message: string, error: any): void {
    console.error(`[GameBridge V3 ERROR] ${message}:`, error);
    if (error.stack) {
      console.error(error.stack);
    }
  }
}

// ============================================================================
// IPC Interface
// ============================================================================

const bridge = new GameBridge();

console.error('[GameBridge V3] Starting...');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

console.error('[GameBridge V3] Readline interface created');

rl.on('line', async (line) => {
  try {
    const command = JSON.parse(line);
    console.error(`[GameBridge V3] Received command: ${command.type}`);

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
        console.error('[GameBridge V3] Shutdown requested');
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
    console.error(`[GameBridge V3 ERROR] ${error.message}`);
    if (error.stack) {
      console.error(error.stack);
    }
    const errorResponse = {
      type: 'error',
      message: error.message
    };
    console.log(JSON.stringify(errorResponse));
  }
});

rl.on('close', () => {
  console.error('[GameBridge V3] Input stream closed');
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  console.error(`[GameBridge V3 FATAL] Uncaught exception: ${error.message}`);
  if (error.stack) {
    console.error(error.stack);
  }
  process.exit(1);
});

console.error('[GameBridge V3] Ready to receive commands');
