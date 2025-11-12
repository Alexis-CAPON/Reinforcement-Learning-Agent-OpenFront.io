/**
 * Game Bridge: TypeScript/Node.js interface for RL training
 *
 * This file wraps the OpenFront.io game engine and exposes it via JSON IPC
 * to the Python RL environment.
 */

import * as readline from 'readline';
import { Game } from '../../base-game/src/core/game/Game';
import { GameImpl } from '../../base-game/src/core/game/GameImpl';
import { GameMapLoader } from '../../base-game/src/core/game/GameMapLoader';
import { BinaryLoaderGameMapLoader } from '../../base-game/src/core/game/BinaryLoaderGameMapLoader';
import { DefaultConfig } from '../../base-game/src/core/configuration/DefaultConfig';
import { PlayerType } from '../../base-game/src/core/game/Game';
import { RLConfig } from './RLConfig';

interface GameState {
  player_id: number;
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

interface AttackableNeighbor {
  neighbor_idx: number;
  enemy_player_id: number;
  tile_x: number;
  tile_y: number;
  enemy_troops: number;
}

class GameBridge {
  private game: Game | null = null;
  private config: RLConfig;
  private mapLoader: GameMapLoader;
  private currentTick = 0;
  private maxTicks = 1000;
  private playerIdRL = 1;  // RL agent is player 1
  private playerIdAI = 2;  // AI opponent is player 2
  private tickIntervalMs = 100;  // Default tick interval

  constructor() {
    this.mapLoader = new BinaryLoaderGameMapLoader();
    this.config = new RLConfig(this.tickIntervalMs);
    this.log('GameBridge initialized');
  }

  /**
   * Initialize a new game
   */
  async reset(mapName: string, opponentDifficulty: string, tickInterval?: number): Promise<GameState> {
    try {
      // Update tick interval if provided
      if (tickInterval !== undefined && tickInterval !== this.tickIntervalMs) {
        this.tickIntervalMs = tickInterval;
        this.config = new RLConfig(tickInterval);
        this.log(`Updated tick interval to ${tickInterval}ms`);
      }

      this.log(`Resetting game: map=${mapName}, difficulty=${opponentDifficulty}, tickInterval=${this.tickIntervalMs}ms`);

      // Load map
      const mapData = await this.mapLoader.load(mapName);

      // Create new game with RL config
      this.game = new GameImpl(
        mapData.gameMap,
        mapData.nations,
        this.config,
        0, // gameId
        false // isMultiplayer
      );

      // Add RL player (human type)
      this.game.addPlayer(
        this.playerIdRL,
        'RL_Agent',
        PlayerType.Human,
        mapData.nations[0] // First spawn point
      );

      // Add AI opponent
      const aiType = this.getAIType(opponentDifficulty);
      this.game.addPlayer(
        this.playerIdAI,
        'AI_Opponent',
        aiType,
        mapData.nations[1] // Second spawn point
      );

      // Initialize game
      this.game.start();
      this.currentTick = 0;

      this.log('Game reset complete');
      return this.getGameState(this.playerIdRL);
    } catch (error) {
      this.logError('Reset failed', error);
      throw error;
    }
  }

  /**
   * Execute one game tick
   */
  tick(): void {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    this.game.executeNextTick();
    this.currentTick++;
  }

  /**
   * Get current game state for a player
   */
  getGameState(playerId: number): GameState {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    const player = this.game.getPlayer(playerId);
    const opponent = this.game.getPlayer(playerId === 1 ? 2 : 1);

    return {
      player_id: playerId,
      tiles_owned: player.numTilesOwned,
      troops: player.troops,
      gold: Number(player.gold),
      max_troops: player.maxTroops,
      enemy_tiles: opponent.numTilesOwned,
      border_tiles: player.borderTiles.size,
      cities: player.units.filter(u => u.type.name === 'City').length,
      tick: this.currentTick,
      has_won: this.checkWin(playerId),
      has_lost: this.checkLoss(playerId),
      game_over: this.game.hasWinner() || this.currentTick >= this.maxTicks
    };
  }

  /**
   * Get list of attackable neighbors for a player
   */
  getAttackableNeighbors(playerId: number): AttackableNeighbor[] {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    const player = this.game.getPlayer(playerId);
    const gameMap = this.game.getMap();
    const neighbors: AttackableNeighbor[] = [];

    // Iterate through player's border tiles
    const borderTiles = Array.from(player.borderTiles);
    const seenTiles = new Set<number>();

    for (const borderTile of borderTiles) {
      // Get neighbors of this border tile
      const neighborTiles = gameMap.neighbors(borderTile);

      for (const neighborTile of neighborTiles) {
        const ownerId = gameMap.ownerID(neighborTile);

        // If neighbor is owned by enemy and not already added
        if (ownerId !== 0 && ownerId !== playerId && !seenTiles.has(neighborTile)) {
          seenTiles.add(neighborTile);

          const enemy = this.game.getPlayer(ownerId);

          neighbors.push({
            neighbor_idx: neighbors.length,
            enemy_player_id: ownerId,
            tile_x: gameMap.x(neighborTile),
            tile_y: gameMap.y(neighborTile),
            enemy_troops: enemy.troops
          });

          // Limit to 8 neighbors max
          if (neighbors.length >= 8) {
            return neighbors;
          }
        }
      }
    }

    return neighbors;
  }

  /**
   * Execute attack action on specific tile
   */
  attackTile(playerId: number, tileX: number, tileY: number): void {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    const gameMap = this.game.getMap();
    const player = this.game.getPlayer(playerId);

    // Convert coordinates to tile reference
    const targetTile = gameMap.ref(tileX, tileY);

    // Create attack intent
    // Note: You'll need to implement the actual intent creation
    // based on your game's action system
    // This is a placeholder for the actual implementation

    this.log(`Player ${playerId} attacking tile (${tileX}, ${tileY})`);

    // TODO: Implement actual attack intent creation
    // player.submitIntent(new AttackIntent(targetTile));
  }

  /**
   * Let AI player take its turn
   */
  aiStep(playerId: number): void {
    if (!this.game) {
      throw new Error('Game not initialized');
    }

    // AI players automatically act during tick
    // This is handled by the game engine
  }

  private checkWin(playerId: number): boolean {
    if (!this.game) return false;
    const winner = this.game.getWinner();
    return winner !== null && winner.id === playerId;
  }

  private checkLoss(playerId: number): boolean {
    if (!this.game) return false;
    const winner = this.game.getWinner();
    return winner !== null && winner.id !== playerId;
  }

  private getAIType(difficulty: string): PlayerType {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return PlayerType.FakeHumanEasy;
      case 'medium':
        return PlayerType.FakeHumanMedium;
      case 'hard':
        return PlayerType.FakeHumanHard;
      case 'impossible':
        return PlayerType.FakeHumanImpossible;
      default:
        return PlayerType.FakeHumanEasy;
    }
  }

  private log(message: string): void {
    console.error(`[GameBridge] ${message}`);
  }

  private logError(message: string, error: any): void {
    console.error(`[GameBridge ERROR] ${message}:`, error);
  }
}

// Main IPC loop
async function main() {
  const bridge = new GameBridge();
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  console.error('[GameBridge] Ready for commands');

  rl.on('line', async (line: string) => {
    try {
      const command = JSON.parse(line);
      let response: any = { success: true };

      switch (command.type) {
        case 'reset':
          response.state = await bridge.reset(
            command.map_name || 'Halkidiki',
            command.difficulty || 'Easy',
            command.tick_interval  // Pass tick_interval from Python
          );
          break;

        case 'tick':
          bridge.tick();
          response.state = bridge.getGameState(command.player_id || 1);
          break;

        case 'get_state':
          response.state = bridge.getGameState(command.player_id || 1);
          break;

        case 'get_neighbors':
          response.neighbors = bridge.getAttackableNeighbors(command.player_id || 1);
          break;

        case 'attack_tile':
          bridge.attackTile(command.player_id, command.tile_x, command.tile_y);
          response.action_executed = true;
          break;

        case 'ai_step':
          bridge.aiStep(command.player_id);
          response.action_executed = true;
          break;

        case 'shutdown':
          console.error('[GameBridge] Shutting down');
          process.exit(0);
          break;

        default:
          response.success = false;
          response.error = `Unknown command type: ${command.type}`;
      }

      // Send response
      console.log(JSON.stringify(response));
    } catch (error: any) {
      console.log(JSON.stringify({
        success: false,
        error: error.message || String(error)
      }));
    }
  });

  rl.on('close', () => {
    console.error('[GameBridge] Input closed, shutting down');
    process.exit(0);
  });
}

// Run main
main().catch(error => {
  console.error('[GameBridge FATAL]', error);
  process.exit(1);
});
