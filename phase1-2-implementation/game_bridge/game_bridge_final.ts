/**
 * Game Bridge - Final Version
 *
 * Simple TypeScript bridge using the same patterns as the working tests.
 * Run with: npx tsx game_bridge_final.ts
 */

import * as readline from 'readline';
import { setup, playerInfo } from '../../base-game/tests/util/Setup';
import { PlayerType, Player, Game } from '../../base-game/src/core/game/Game';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import * as path from 'path';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

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
    this.log('GameBridge initialized');
  }

  async reset(mapName: string = 'plains', difficulty: string = 'easy', tickInterval?: number): Promise<GameState> {
    try {
      this.log(`Resetting: map=${mapName}, difficulty=${difficulty}`);

      // Use setup utility from tests
      this.game = await setup(
        mapName,
        {
          gameMode: 'Free For All' as any,
          gameType: 'Singleplayer' as any,
          difficulty: 'Easy' as any,
          infiniteGold: false,
          infiniteTroops: false,
          instantBuild: false,
        },
        [
          playerInfo('RL_Agent', PlayerType.Human),
          playerInfo('AI_Bot', PlayerType.FakeHuman)
        ],
        path.join(__dirname, '../../base-game/tests/util')
      );

      // Execute spawn phase
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      const players = this.game.players();
      this.rlPlayer = players[0];
      this.aiPlayer = players[1];

      this.currentTick = Number(this.game.ticks());
      this.log(`Game ready at tick ${this.currentTick}`);

      return this.getState();

    } catch (error: any) {
      this.logError('Reset failed', error);
      throw error;
    }
  }

  tick(): GameState {
    if (!this.game) throw new Error('Game not initialized');
    this.game.executeNextTick();
    this.currentTick++;
    return this.getState();
  }

  getState(): GameState {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) {
      throw new Error('Game not initialized');
    }

    return {
      tiles_owned: this.rlPlayer.numTilesOwned(),
      troops: this.rlPlayer.troops(),
      gold: Number(this.rlPlayer.gold()),
      max_troops: 100000,
      enemy_tiles: this.aiPlayer.numTilesOwned(),
      border_tiles: this.rlPlayer.borderTiles().size,
      cities: this.rlPlayer.units().filter(u => u.type() === 'City').length,
      tick: this.currentTick,
      has_won: !this.aiPlayer.isAlive(),
      has_lost: !this.rlPlayer.isAlive(),
      game_over: !this.rlPlayer.isAlive() || !this.aiPlayer.isAlive() || this.currentTick >= this.maxTicks
    };
  }

  getAttackableNeighbors(): Neighbor[] {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) return [];

    const neighbors: Neighbor[] = [];
    const borderTiles = Array.from(this.rlPlayer.borderTiles());

    for (const borderTile of borderTiles) {
      const x = this.game.x(borderTile);
      const y = this.game.y(borderTile);

      const offsets = [
        { dx: 0, dy: -1 }, { dx: 0, dy: 1 },
        { dx: -1, dy: 0 }, { dx: 1, dy: 0 }
      ];

      for (const offset of offsets) {
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

          if (neighbors.length >= 8) return neighbors;
        }
      }
    }

    return neighbors;
  }

  attackTile(tile_x: number, tile_y: number): void {
    if (!this.game || !this.rlPlayer || !this.aiPlayer) {
      throw new Error('Game not initialized');
    }

    const targetTile = this.game.ref(tile_x, tile_y);
    if (!this.rlPlayer.canAttack(targetTile)) {
      this.log(`Cannot attack (${tile_x}, ${tile_y})`);
      return;
    }

    const attackTroops = Math.min(1000, Math.floor(this.rlPlayer.troops() * 0.5));
    this.game.addExecution(
      new AttackExecution(attackTroops, this.rlPlayer, this.aiPlayer.id())
    );
  }

  private log(msg: string): void {
    console.error(`[GameBridge] ${msg}`);
  }

  private logError(msg: string, error: any): void {
    console.error(`[GameBridge ERROR] ${msg}:`, error);
  }
}

// ============================================================================
// IPC Interface
// ============================================================================

const bridge = new GameBridge();
console.error('[GameBridge] Starting...');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', async (line) => {
  try {
    const command = JSON.parse(line);
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
        response.message = 'Goodbye!';
        console.log(JSON.stringify(response));
        process.exit(0);
      default:
        response = { type: 'error', message: `Unknown: ${command.type}` };
    }

    console.log(JSON.stringify(response));

  } catch (error: any) {
    console.error(`[GameBridge ERROR] ${error.message}`);
    console.log(JSON.stringify({ type: 'error', message: error.message }));
  }
});

rl.on('close', () => process.exit(0));

console.error('[GameBridge] Ready');
