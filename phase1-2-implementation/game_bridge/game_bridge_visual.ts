/**
 * Visual Game Bridge - Extends game_bridge_cached with rendering capabilities
 *
 * This bridge exports full game state snapshots that can be rendered
 * using the OpenFront.io client renderer.
 */

import * as readline from 'readline';
import { setup, playerInfo } from '../../base-game/tests/util/Setup';
import { PlayerType, Player, Game, PlayerInfo } from '../../base-game/src/core/game/Game';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
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

interface VisualState extends GameState {
  map_width: number;
  map_height: number;
  tiles: TileState[];
  players: PlayerState[];
}

interface TileState {
  x: number;
  y: number;
  owner_id: number;  // 0 = neutral, 1+ = player
  troops: number;
  is_city: boolean;
  is_mountain: boolean;
}

interface PlayerState {
  id: number;
  is_alive: boolean;
  tiles_owned: number;
  total_troops: number;
  gold: number;
  color: string;  // Hex color for rendering
}

interface AttackableNeighbor {
  neighbor_idx: number;
  enemy_player_id: number;
  tile_x: number;
  tile_y: number;
  enemy_troops: number;
}

interface Command {
  type: 'reset' | 'tick' | 'get_state' | 'get_visual_state' | 'get_attackable_neighbors' | 'attack_tile' | 'shutdown';
  map_name?: string;
  difficulty?: string;
  tick_interval?: number;
  num_players?: number;
  tile_x?: number;
  tile_y?: number;
}

interface Response {
  type: 'state' | 'visual_state' | 'neighbors' | 'ack' | 'error';
  state?: GameState | VisualState;
  neighbors?: AttackableNeighbor[];
  message?: string;
}

class VisualGameBridge {
  private game: Game | null = null;
  private rlPlayer: Player | null = null;
  private aiPlayers: Player[] = [];
  private currentTick: number = 0;
  private mapName: string = '';
  private maxTicks: number = 10000;
  private maxTroops: number = 100000;  // Default max troops for RL agent

  private readonly PLAYER_COLORS = [
    '#FF0000',  // Red (RL agent)
    '#0000FF',  // Blue
    '#00FF00',  // Green
    '#FFFF00',  // Yellow
    '#FF00FF',  // Magenta
    '#00FFFF',  // Cyan
    '#FFA500',  // Orange
    '#800080',  // Purple
  ];

  private log(message: string) {
    console.error(`[VisualBridge] ${message}`);
  }

  async initialize(mapName: string, difficulty: string, tickIntervalMs: number, numPlayers: number): Promise<GameState> {
    this.log(`Initializing game: map=${mapName}, difficulty=${difficulty}, tickInterval=${tickIntervalMs}ms, players=${numPlayers}`);

    this.mapName = mapName;

    // Create player info array (same as cached bridge)
    const players: PlayerInfo[] = [new PlayerInfo('RL_Agent', PlayerType.Human, null, 'RL_Agent')];
    for (let i = 1; i < numPlayers; i++) {
      players.push(new PlayerInfo(`AI_Bot_${i}`, PlayerType.Bot, null, `AI_Bot_${i}`));
    }

    this.log(`Creating game with ${players.length} players`);

    // Setup game (async!)
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
      players,
      path.join(__dirname, '../../base-game/tests/util')
    );

    if (!this.game) {
      throw new Error('setup() returned null');
    }

    this.log(`Game created, adding spawn points...`);

    // Distribute players around the map with randomization
    const width = this.game.width();
    const height = this.game.height();
    const spawnExecutions: SpawnExecution[] = [];
    const angleOffset = Math.random() * 2 * Math.PI;

    for (let i = 0; i < numPlayers; i++) {
      const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;
      const baseX = Math.floor(width / 2 + (width / 2 - 15) * Math.cos(angle));
      const baseY = Math.floor(height / 2 + (height / 2 - 15) * Math.sin(angle));
      const x = Math.max(5, Math.min(width - 5, baseX + Math.floor((Math.random() - 0.5) * 10)));
      const y = Math.max(5, Math.min(height - 5, baseY + Math.floor((Math.random() - 0.5) * 10)));

      const spawnPos = this.game.ref(x, y);
      const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
      const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;

      spawnExecutions.push(
        new SpawnExecution(
          new PlayerInfo(playerName, playerType, null, playerName),
          spawnPos
        )
      );
    }

    this.game.addExecution(...spawnExecutions);

    // Execute spawn phase
    this.log(`Executing spawn phase...`);
    while (this.game.inSpawnPhase()) {
      this.game.executeNextTick();
    }
    this.log(`Spawn phase complete`);

    // Get players by name
    this.rlPlayer = this.game.player('RL_Agent');
    if (!this.rlPlayer) {
      throw new Error('RL Player not found');
    }

    this.aiPlayers = [];
    for (let i = 1; i < numPlayers; i++) {
      const aiPlayer = this.game.player(`AI_Bot_${i}`);
      if (!aiPlayer) {
        throw new Error(`AI_Bot_${i} not found`);
      }
      this.aiPlayers.push(aiPlayer);
    }

    this.currentTick = Number(this.game.ticks());
    this.log(`Game initialized with ${numPlayers} players at tick ${this.currentTick}`);

    return this.getState();
  }

  async reset(mapName: string, difficulty: string, tickIntervalMs: number, numPlayers: number): Promise<GameState> {
    // For simplicity, just reinitialize (fast enough with setup utility)
    return await this.initialize(mapName, difficulty, tickIntervalMs, numPlayers);
  }

  tick(): GameState {
    if (!this.game) throw new Error('Game not initialized');
    this.game.executeNextTick();
    this.currentTick++;
    return this.getState();
  }

  getState(): GameState {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) {
      throw new Error('Game not initialized');
    }

    const enemyTiles = this.aiPlayers.reduce((sum, ai) => sum + ai.numTilesOwned(), 0);
    const allAIDead = this.aiPlayers.every(ai => !ai.isAlive());
    const tilesOwned = this.rlPlayer.numTilesOwned();
    const isAlive = this.rlPlayer.isAlive();
    const hasLost = !isAlive || tilesOwned === 0;

    return {
      tiles_owned: tilesOwned,
      troops: this.rlPlayer.troops(),
      gold: Number(this.rlPlayer.gold()),
      max_troops: 100000,
      enemy_tiles: enemyTiles,
      border_tiles: this.rlPlayer.borderTiles().size,
      cities: this.rlPlayer.units().filter(u => u.type() === 'City').length,
      tick: this.currentTick,
      has_won: allAIDead,
      has_lost: hasLost,
      game_over: hasLost || allAIDead || this.currentTick >= this.maxTicks
    };
  }

  getVisualState(): VisualState {
    if (!this.game || !this.rlPlayer) throw new Error('Game not initialized');

    const baseState = this.getState();
    const width = this.game.width();
    const height = this.game.height();

    // Collect ALL tiles on the map (not just player-owned)
    const tiles: TileState[] = [];
    const allPlayers = [this.rlPlayer, ...this.aiPlayers];

    // Create a set of city positions for fast lookup
    const cityPositions = new Set<string>();
    allPlayers.forEach(player => {
      player.units().filter(u => u.type() === 'City').forEach(city => {
        const cityX = this.game.x(city.tile());
        const cityY = this.game.y(city.tile());
        cityPositions.add(`${cityX},${cityY}`);
      });
    });

    // Iterate through every coordinate on the map
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const tileRef = this.game.ref(x, y);
        const owner = this.game.owner(tileRef);

        // Determine owner_id
        let owner_id = 0;  // Default to neutral
        if (owner.isPlayer()) {
          const ownerPlayer = owner as Player;
          if (ownerPlayer.id() === this.rlPlayer.id()) {
            owner_id = 1;
          } else {
            const aiIndex = this.aiPlayers.findIndex(ai => ai.id() === ownerPlayer.id());
            owner_id = aiIndex >= 0 ? aiIndex + 2 : 0;
          }
        }

        // Get terrain type (Mountain is a terrain type, not unit)
        const terrainType = this.game.terrainType(tileRef);
        const is_mountain = terrainType === 2;  // TerrainType.Mountain = 2

        // Check if this tile has a city (cities are units, not terrain)
        const is_city = cityPositions.has(`${x},${y}`);

        // Troops are per-player, not per-tile - we'll use 0 for display
        const troops = 0;

        tiles.push({
          x,
          y,
          owner_id,
          troops,
          is_city,
          is_mountain
        });
      }
    }

    // Extract player states
    const players: PlayerState[] = allPlayers.map((player, idx) => ({
      id: idx + 1,
      is_alive: player.isAlive(),
      tiles_owned: player.numTilesOwned(),
      total_troops: player.troops(),
      gold: Number(player.gold()),
      color: this.PLAYER_COLORS[idx] || '#FFFFFF'
    }));

    return {
      ...baseState,
      map_width: width,
      map_height: height,
      tiles,
      players
    };
  }

  private getPlayerId(player: Player): number {
    if (player === this.rlPlayer) return 1;
    const aiIndex = this.aiPlayers.indexOf(player);
    return aiIndex >= 0 ? aiIndex + 2 : 0;
  }

  getAttackableNeighbors(): AttackableNeighbor[] {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) return [];

    const neighbors: AttackableNeighbor[] = [];
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

        // Include neutral territory and any enemy player tiles
        const isNeutral = !owner.isPlayer();
        const isEnemyPlayer = owner.isPlayer() && (owner as Player).id() !== this.rlPlayer.id();

        if (isEnemyPlayer || isNeutral) {
          let enemyPlayerId = 0;
          if (isEnemyPlayer) {
            const ownerPlayer = owner as Player;
            const aiIndex = this.aiPlayers.findIndex(ai => ai.id() === ownerPlayer.id());
            enemyPlayerId = aiIndex >= 0 ? aiIndex + 2 : 2;
          }

          neighbors.push({
            neighbor_idx: neighbors.length,
            enemy_player_id: enemyPlayerId,
            tile_x: adjX,
            tile_y: adjY,
            enemy_troops: isNeutral ? 0 : (owner as Player).troops()
          });

          if (neighbors.length >= 8) return neighbors;
        }
      }
    }

    return neighbors;
  }

  attackTile(tileX: number, tileY: number, attack_percentage: number = 0.5) {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) {
      throw new Error('Game not initialized');
    }

    const targetTile = this.game.ref(tileX, tileY);
    if (!this.rlPlayer.canAttack(targetTile)) {
      this.log(`Cannot attack (${tileX}, ${tileY})`);
      return;
    }

    // Get current troops and calculate attack size using learned percentage
    const currentTroops = this.rlPlayer.troops();
    const attackTroops = Math.floor(currentTroops * attack_percentage);

    // Minimum attack size validation
    if (attackTroops < 1) {
      this.log(`Attack too small: ${attackTroops} troops (${attack_percentage * 100}% of ${currentTroops})`);
      return;
    }

    // Determine the target
    const owner = this.game.owner(targetTile);
    const targetId = owner.isPlayer()
      ? (owner as Player).id()
      : this.game.terraNullius().id();

    // Validate attackTroops is a valid number
    if (isNaN(attackTroops) || !isFinite(attackTroops)) {
      this.log(`Invalid attack troops: ${attackTroops}, skipping attack`);
      return;
    }

    this.log(`Attacking (${tileX}, ${tileY}) with ${attackTroops} troops (${attack_percentage * 100}% of ${currentTroops})`);

    this.game.addExecution(
      new AttackExecution(attackTroops, this.rlPlayer, targetId)
    );
  }
}

// Main bridge loop
async function main() {
  const bridge = new VisualGameBridge();
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  console.error('[VisualBridge] Ready for commands');

  rl.on('line', async (line: string) => {
    try {
      const command: Command = JSON.parse(line);
      let response: Response;

      switch (command.type) {
        case 'reset':
          const state = await bridge.reset(
            command.map_name || 'plains',
            command.difficulty || 'Easy',
            command.tick_interval || 100,
            command.num_players || 6
          );
          response = { type: 'state', state };
          break;

        case 'tick':
          response = { type: 'state', state: bridge.tick() };
          break;

        case 'get_state':
          response = { type: 'state', state: bridge.getState() };
          break;

        case 'get_visual_state':
          response = { type: 'visual_state', state: bridge.getVisualState() };
          break;

        case 'get_attackable_neighbors':
          response = { type: 'neighbors', neighbors: bridge.getAttackableNeighbors() };
          break;

        case 'attack_tile':
          bridge.attackTile(command.tile_x!, command.tile_y!, command.attack_percentage || 0.5);
          response = { type: 'ack' };
          break;

        case 'shutdown':
          console.error('[VisualBridge] Shutting down');
          process.exit(0);

        default:
          response = { type: 'error', message: `Unknown command: ${command.type}` };
      }

      console.log(JSON.stringify(response));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.log(JSON.stringify({ type: 'error', message: errorMessage }));
    }
  });
}

main();
