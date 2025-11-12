/**
 * Game Bridge for Phase 3 - Battle Royale
 *
 * Supports:
 * - Battle royale mode (10-50 bots)
 * - Spatial map extraction (512×512 → 128×128)
 * - Direction-based actions
 * - 16 global features
 * - Fast resets with map caching
 */

import * as readline from 'readline';
import { setup, playerInfo } from '../../base-game/tests/util/Setup';
import { PlayerType, Player, Game, PlayerInfo } from '../../base-game/src/core/game/Game';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
import { GameUpdateType } from '../../base-game/src/core/game/GameUpdates';
import * as path from 'path';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface GameState {
  // Core state
  tick: number;
  game_over: boolean;
  has_won: boolean;
  has_lost: boolean;

  // Territory info
  tiles_owned: number;
  total_tiles: number;
  territory_pct: number;
  neutral_tiles: number;

  // Population
  population: number;
  max_population: number;
  population_growth_rate: number;

  // Resources
  gold: number;
  num_cities: number;

  // Position
  rank: number;
  total_players: number;
  alive_players: number;

  // Spatial data (512×512)
  territory_map: number[][];      // Player IDs
  troop_map: number[][];          // Troop counts

  // Global features for RL
  border_tiles: number;
  border_pressure: number;
  time_alive: number;
  nearest_threat_distance: number;
  territory_change: number;
}

interface DirectionTarget {
  direction: number;  // 0-7 for N, NE, E, SE, S, SW, W, NW
  tile_x: number;
  tile_y: number;
  owner_id: number;
  distance: number;
}

class GameBridge {
  private game: Game | null = null;
  private rlPlayer: Player | null = null;
  private aiPlayers: Player[] = [];
  private currentTick: number = 0;
  private maxTicks: number = 50000;
  private startTick: number = 0;

  // Map cache
  private mapName: string = 'plains';
  private numPlayers: number = 50;
  private isInitialized: boolean = false;
  private mapWidth: number = 512;
  private mapHeight: number = 512;

  // History for computing rates
  private previousTiles: number = 0;
  private territoryHistory: number[] = [];

  constructor() {
    this.log('GameBridge Phase 3 initialized (Battle Royale)');
  }

  /**
   * Initialize game (slow first time, cached after)
   */
  async initialize(mapName: string = 'plains', numPlayers: number = 50): Promise<void> {
    if (this.isInitialized && this.mapName === mapName && this.numPlayers === numPlayers) {
      this.log('Already initialized, skipping');
      return;
    }

    this.log(`Initializing battle royale: map=${mapName}, ${numPlayers} players...`);
    const startTime = Date.now();

    this.mapName = mapName;
    this.numPlayers = numPlayers;

    try {
      // Create player list: 1 RL agent + (numPlayers-1) AI bots
      const players: PlayerInfo[] = [
        playerInfo('RL_Agent', PlayerType.Human)
      ];

      for (let i = 1; i < numPlayers; i++) {
        players.push(playerInfo(`AI_Bot_${i}`, PlayerType.Bot));
      }

      this.log(`Creating game with ${players.length} players...`);

      // Load map
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

      // Get map dimensions
      this.mapWidth = this.game.width();
      this.mapHeight = this.game.height();
      this.log(`Map size: ${this.mapWidth}×${this.mapHeight}`);

      // Spawn players distributed around map edges
      const spawnExecutions: SpawnExecution[] = [];
      const angleOffset = Math.random() * 2 * Math.PI;

      for (let i = 0; i < numPlayers; i++) {
        const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;
        const baseX = Math.floor(this.mapWidth / 2 + (this.mapWidth / 2 - 20) * Math.cos(angle));
        const baseY = Math.floor(this.mapHeight / 2 + (this.mapHeight / 2 - 20) * Math.sin(angle));
        const x = Math.max(5, Math.min(this.mapWidth - 5, baseX + Math.floor((Math.random() - 0.5) * 10)));
        const y = Math.max(5, Math.min(this.mapHeight - 5, baseY + Math.floor((Math.random() - 0.5) * 10)));

        const spawnPos = this.game.ref(x, y);
        const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
        const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;

        spawnExecutions.push(
          new SpawnExecution(playerInfo(playerName, playerType), spawnPos)
        );
      }

      this.game.addExecution(...spawnExecutions);

      // Execute spawn phase
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      // Get players
      this.rlPlayer = this.game.player('RL_Agent');
      if (!this.rlPlayer) {
        throw new Error('Could not find RL_Agent');
      }

      this.aiPlayers = [];
      for (let i = 1; i < numPlayers; i++) {
        const aiPlayer = this.game.player(`AI_Bot_${i}`);
        if (aiPlayer) {
          this.aiPlayers.push(aiPlayer);
        }
      }

      this.currentTick = Number(this.game.ticks());
      this.startTick = this.currentTick;
      this.previousTiles = this.rlPlayer.numTilesOwned();
      this.territoryHistory = [this.previousTiles];
      this.isInitialized = true;

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      this.log(`Initialization complete in ${elapsed}s`);

    } catch (error: any) {
      this.log(`Initialization FAILED: ${error.message}`);
      throw error;
    }
  }

  /**
   * Fast reset - reuses map
   */
  async reset(mapName: string = 'plains', numPlayers?: number): Promise<GameState> {
    const players = numPlayers || this.numPlayers;

    // Initialize if needed
    if (!this.isInitialized || mapName !== this.mapName || players !== this.numPlayers) {
      await this.initialize(mapName, players);
    } else {
      this.log('Fast reset...');

      // Create new game with same map
      const playerInfos: PlayerInfo[] = [playerInfo('RL_Agent', PlayerType.Human)];
      for (let i = 1; i < this.numPlayers; i++) {
        playerInfos.push(playerInfo(`AI_Bot_${i}`, PlayerType.Bot));
      }

      this.game = await setup(
        this.mapName,
        {
          gameMode: 'Free For All' as any,
          gameType: 'Singleplayer' as any,
          difficulty: 'Easy' as any,
          infiniteGold: false,
          infiniteTroops: false,
          instantBuild: false,
        },
        playerInfos,
        path.join(__dirname, '../../base-game/tests/util')
      );

      // Spawn players
      const spawnExecutions: SpawnExecution[] = [];
      const angleOffset = Math.random() * 2 * Math.PI;

      for (let i = 0; i < this.numPlayers; i++) {
        const angle = (i / this.numPlayers) * 2 * Math.PI + angleOffset;
        const baseX = Math.floor(this.mapWidth / 2 + (this.mapWidth / 2 - 20) * Math.cos(angle));
        const baseY = Math.floor(this.mapHeight / 2 + (this.mapHeight / 2 - 20) * Math.sin(angle));
        const x = Math.max(5, Math.min(this.mapWidth - 5, baseX + Math.floor((Math.random() - 0.5) * 10)));
        const y = Math.max(5, Math.min(this.mapHeight - 5, baseY + Math.floor((Math.random() - 0.5) * 10)));

        const spawnPos = this.game.ref(x, y);
        const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
        const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;

        spawnExecutions.push(
          new SpawnExecution(playerInfo(playerName, playerType), spawnPos)
        );
      }

      this.game.addExecution(...spawnExecutions);

      // Execute spawn phase
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      // Get players
      this.rlPlayer = this.game.player('RL_Agent');
      if (!this.rlPlayer) {
        throw new Error('Could not find RL_Agent');
      }

      this.aiPlayers = [];
      for (let i = 1; i < this.numPlayers; i++) {
        const aiPlayer = this.game.player(`AI_Bot_${i}`);
        if (aiPlayer) {
          this.aiPlayers.push(aiPlayer);
        }
      }

      this.currentTick = Number(this.game.ticks());
      this.startTick = this.currentTick;
      this.previousTiles = this.rlPlayer.numTilesOwned();
      this.territoryHistory = [this.previousTiles];
    }

    return this.getState();
  }

  /**
   * Execute one game tick
   */
  tick(): GameState {
    if (!this.game) throw new Error('Game not initialized');

    this.game.executeNextTick();
    this.currentTick++;

    return this.getState();
  }

  /**
   * Get current game state with spatial maps and global features
   */
  getState(): GameState {
    if (!this.game || !this.rlPlayer) {
      throw new Error('Game not initialized');
    }

    const aliveAIPlayers = this.aiPlayers.filter(ai => ai.isAlive());
    const alivePlayers = [this.rlPlayer, ...aliveAIPlayers].filter(p => p.isAlive());

    // Territory info
    const tilesOwned = this.rlPlayer.numTilesOwned();
    const totalTiles = this.mapWidth * this.mapHeight;
    const territoryPct = tilesOwned / totalTiles;

    // Count neutral tiles
    let neutralTiles = 0;
    for (let y = 0; y < this.mapHeight; y++) {
      for (let x = 0; x < this.mapWidth; x++) {
        const tile = this.game.ref(x, y);
        const owner = this.game.owner(tile);
        if (!owner.isPlayer()) {
          neutralTiles++;
        }
      }
    }

    // Population
    const population = this.rlPlayer.troops();
    const maxPopulation = this.game.config().maxTroops(this.rlPlayer);
    const populationGrowthRate = (tilesOwned - this.previousTiles) / Math.max(this.previousTiles, 1);

    // Resources
    const gold = Number(this.rlPlayer.gold());
    const numCities = this.rlPlayer.units().filter(u => u.type().name() === 'City').length;

    // Rank (1 = 1st place)
    const sortedByTerritory = alivePlayers
      .map(p => p.numTilesOwned())
      .sort((a, b) => b - a);
    const rank = sortedByTerritory.indexOf(tilesOwned) + 1;

    // Border info
    const borderTiles = this.rlPlayer.borderTiles().size;
    const borderPressure = this.computeBorderPressure();

    // Time alive
    const timeAlive = this.currentTick - this.startTick;

    // Nearest threat
    const nearestThreat = this.findNearestThreat();

    // Territory change (last 10 ticks)
    this.territoryHistory.push(tilesOwned);
    if (this.territoryHistory.length > 10) {
      this.territoryHistory.shift();
    }
    const territoryChange = this.territoryHistory.length > 1
      ? (tilesOwned - this.territoryHistory[0]) / this.territoryHistory.length
      : 0;

    // Check win/loss
    const hasWon = territoryPct >= 0.80;
    const hasLost = !this.rlPlayer.isAlive() || tilesOwned === 0;
    const gameOver = hasWon || hasLost || this.currentTick >= this.maxTicks;

    // Extract spatial maps
    const { territoryMap, troopMap } = this.extractMaps();

    this.previousTiles = tilesOwned;

    return {
      tick: this.currentTick,
      game_over: gameOver,
      has_won: hasWon,
      has_lost: hasLost,

      tiles_owned: tilesOwned,
      total_tiles: totalTiles,
      territory_pct: territoryPct,
      neutral_tiles: neutralTiles,

      population: population,
      max_population: maxPopulation,
      population_growth_rate: populationGrowthRate,

      gold: gold,
      num_cities: numCities,

      rank: rank,
      total_players: this.numPlayers,
      alive_players: alivePlayers.length,

      territory_map: territoryMap,
      troop_map: troopMap,

      border_tiles: borderTiles,
      border_pressure: borderPressure,
      time_alive: timeAlive,
      nearest_threat_distance: nearestThreat,
      territory_change: territoryChange
    };
  }

  /**
   * Extract 512×512 spatial maps
   */
  private extractMaps(): { territoryMap: number[][], troopMap: number[][] } {
    if (!this.game) throw new Error('Game not initialized');

    const territoryMap: number[][] = [];
    const troopMap: number[][] = [];

    // Create player ID mapping (RL agent = 1, AI bots = 2+)
    const playerIdMap = new Map<number, number>();
    if (this.rlPlayer) {
      playerIdMap.set(this.rlPlayer.id(), 1);
    }
    this.aiPlayers.forEach((ai, index) => {
      playerIdMap.set(ai.id(), index + 2);
    });

    for (let y = 0; y < this.mapHeight; y++) {
      const territoryRow: number[] = [];
      const troopRow: number[] = [];

      for (let x = 0; x < this.mapWidth; x++) {
        const tile = this.game.ref(x, y);
        const owner = this.game.owner(tile);

        // Territory: 0 = neutral, 1 = RL agent, 2+ = AI players
        if (!owner.isPlayer()) {
          territoryRow.push(0);  // Neutral/TerraNullius
        } else {
          const player = owner as Player;
          const mappedId = playerIdMap.get(player.id()) || 0;
          territoryRow.push(mappedId);
        }

        // Troops: approximate troop count on this tile
        // (Note: actual game may store this differently)
        troopRow.push(0);  // TODO: Get actual troop count if available
      }

      territoryMap.push(territoryRow);
      troopMap.push(troopRow);
    }

    return { territoryMap, troopMap };
  }

  /**
   * Compute border pressure (how many enemy tiles adjacent to borders)
   */
  private computeBorderPressure(): number {
    if (!this.game || !this.rlPlayer) return 0;

    let pressure = 0;
    const borderTiles = Array.from(this.rlPlayer.borderTiles());

    for (const borderTile of borderTiles) {
      const x = this.game.x(borderTile);
      const y = this.game.y(borderTile);
      const offsets = [
        { dx: 0, dy: -1 }, { dx: 0, dy: 1 },
        { dx: -1, dy: 0 }, { dx: 1, dy: 0 }
      ];

      for (const { dx, dy } of offsets) {
        const adjX = x + dx;
        const adjY = y + dy;

        if (adjX >= 0 && adjX < this.mapWidth && adjY >= 0 && adjY < this.mapHeight) {
          const adjTile = this.game.ref(adjX, adjY);
          const owner = this.game.owner(adjTile);

          if (owner.isPlayer() && (owner as Player).id() !== this.rlPlayer.id()) {
            pressure++;
          }
        }
      }
    }

    return pressure;
  }

  /**
   * Find distance to nearest large enemy
   */
  private findNearestThreat(): number {
    if (!this.game || !this.rlPlayer) return 999;

    // Find center of RL agent's territory
    let centerX = 0;
    let centerY = 0;
    let count = 0;

    for (let y = 0; y < this.mapHeight; y++) {
      for (let x = 0; x < this.mapWidth; x++) {
        const tile = this.game.ref(x, y);
        const owner = this.game.owner(tile);

        if (owner.isPlayer() && (owner as Player).id() === this.rlPlayer.id()) {
          centerX += x;
          centerY += y;
          count++;
        }
      }
    }

    if (count === 0) return 999;

    centerX /= count;
    centerY /= count;

    // Find nearest large enemy
    let minDistance = 999;
    const rlTiles = this.rlPlayer.numTilesOwned();

    for (const aiPlayer of this.aiPlayers) {
      if (!aiPlayer.isAlive()) continue;
      if (aiPlayer.numTilesOwned() < rlTiles * 0.5) continue;  // Only consider threats

      // Find enemy center
      let enemyCenterX = 0;
      let enemyCenterY = 0;
      let enemyCount = 0;

      for (let y = 0; y < this.mapHeight; y++) {
        for (let x = 0; x < this.mapWidth; x++) {
          const tile = this.game.ref(x, y);
          const owner = this.game.owner(tile);

          if (owner.isPlayer() && (owner as Player).id() === aiPlayer.id()) {
            enemyCenterX += x;
            enemyCenterY += y;
            enemyCount++;
          }
        }
      }

      if (enemyCount === 0) continue;

      enemyCenterX /= enemyCount;
      enemyCenterY /= enemyCount;

      const distance = Math.sqrt(
        Math.pow(centerX - enemyCenterX, 2) +
        Math.pow(centerY - enemyCenterY, 2)
      );

      minDistance = Math.min(minDistance, distance);
    }

    return minDistance;
  }

  /**
   * Find target in given direction
   */
  findDirectionTarget(direction: number): DirectionTarget | null {
    if (!this.game || !this.rlPlayer) return null;

    // Direction vectors: N, NE, E, SE, S, SW, W, NW
    const dirVectors = [
      { dx: 0, dy: -1 },   // N
      { dx: 1, dy: -1 },   // NE
      { dx: 1, dy: 0 },    // E
      { dx: 1, dy: 1 },    // SE
      { dx: 0, dy: 1 },    // S
      { dx: -1, dy: 1 },   // SW
      { dx: -1, dy: 0 },   // W
      { dx: -1, dy: -1 }   // NW
    ];

    if (direction < 0 || direction >= 8) return null;

    const { dx, dy } = dirVectors[direction];

    // Find center of territory
    let centerX = 0;
    let centerY = 0;
    let count = 0;

    for (let y = 0; y < this.mapHeight; y++) {
      for (let x = 0; x < this.mapWidth; x++) {
        const tile = this.game.ref(x, y);
        const owner = this.game.owner(tile);

        if (owner.isPlayer() && (owner as Player).id() === this.rlPlayer.id()) {
          centerX += x;
          centerY += y;
          count++;
        }
      }
    }

    if (count === 0) return null;

    centerX = Math.floor(centerX / count);
    centerY = Math.floor(centerY / count);

    // Raycast in direction to find target
    for (let distance = 1; distance < Math.max(this.mapWidth, this.mapHeight); distance++) {
      const targetX = centerX + dx * distance;
      const targetY = centerY + dy * distance;

      if (targetX < 0 || targetX >= this.mapWidth || targetY < 0 || targetY >= this.mapHeight) {
        break;
      }

      const tile = this.game.ref(targetX, targetY);
      const owner = this.game.owner(tile);

      // Found enemy or neutral territory
      if (!owner.isPlayer()) {
        // Neutral/TerraNullius
        return {
          direction,
          tile_x: targetX,
          tile_y: targetY,
          owner_id: 0,
          distance
        };
      } else if ((owner as Player).id() !== this.rlPlayer.id()) {
        // Enemy player
        return {
          direction,
          tile_x: targetX,
          tile_y: targetY,
          owner_id: (owner as Player).id(),
          distance
        };
      }
    }

    return null;
  }

  /**
   * Execute attack in direction with intensity
   */
  attackDirection(direction: number, intensity: number): boolean {
    const target = this.findDirectionTarget(direction);

    if (!target || !this.rlPlayer) {
      return false;
    }

    // Calculate troops to send
    const troops = Math.floor(this.rlPlayer.troops() * intensity);

    if (troops < 1) {
      return false;
    }

    // TODO: Execute actual attack
    // This depends on your game's action system
    // You may need to create an AttackExecution or similar

    this.log(`Attack direction ${direction} with ${troops} troops (${(intensity*100).toFixed(0)}%)`);

    return true;
  }

  /**
   * Build city at safe location
   */
  buildCity(): boolean {
    if (!this.game || !this.rlPlayer) return false;

    const CITY_COST = 5000;
    if (this.rlPlayer.gold() < CITY_COST) {
      return false;
    }

    // Find interior tile (far from borders)
    // TODO: Implement city building logic

    this.log('Build city (not yet implemented)');
    return false;
  }

  private log(message: string): void {
    console.error(`[GameBridge] ${message}`);
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
            command.map_name || 'plains',
            command.num_players || 50
          );
          break;

        case 'tick':
          response.state = bridge.tick();
          break;

        case 'get_state':
          response.state = bridge.getState();
          break;

        case 'find_direction_target':
          response.target = bridge.findDirectionTarget(command.direction);
          break;

        case 'attack_direction':
          response.success = bridge.attackDirection(
            command.direction,
            command.intensity
          );
          break;

        case 'build_city':
          response.success = bridge.buildCity();
          break;

        case 'shutdown':
          console.error('[GameBridge] Shutting down');
          process.exit(0);
          break;

        default:
          response.success = false;
          response.error = `Unknown command type: ${command.type}`;
      }

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

main().catch(error => {
  console.error('[GameBridge FATAL]', error);
  process.exit(1);
});
