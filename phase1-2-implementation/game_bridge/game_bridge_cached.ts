/**
 * Game Bridge - Cached Version
 *
 * Pre-loads the map once at startup, then reuses it for fast resets.
 * Run with: npx tsx game_bridge_cached.ts
 */

import * as readline from 'readline';
import { setup, playerInfo } from '../../base-game/tests/util/Setup';
import { PlayerType, Player, Game, PlayerInfo } from '../../base-game/src/core/game/Game';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
import { GameUpdateType } from '../../base-game/src/core/game/GameUpdates';
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
  enemy_troops: number;
  neighbor_enemy_troops: number;  // Total troops of neighboring enemy players
  border_tiles: number;
  cities: number;
  tick: number;
  has_won: boolean;
  has_lost: boolean;
  game_over: boolean;
  enemies_killed_this_tick: number;  // Number of enemies RL agent eliminated this tick

  // NEW: Strategic metrics
  troops_per_tile: number;           // Our troop density (troops / tiles)
  avg_enemy_troops_per_tile: number; // Average enemy troop density
  border_tile_ratio: number;         // Exposure: border_tiles / total_tiles
  rank_by_tiles: number;             // Our rank by territory (1.0 = 1st, 0.0 = last)
  rank_by_troops: number;            // Our rank by military strength

  // NEW: Per-player arrays (indexed by alive players)
  player_tiles: number[];            // Tiles owned by each alive player [RL, AI1, AI2, ...]
  player_troops: number[];           // Troops owned by each alive player
  player_is_neighbor: number[];      // Is this player adjacent to us? [1=yes, 0=no]
}

interface Neighbor {
  neighbor_idx: number;
  enemy_player_id: number;
  tile_x: number;
  tile_y: number;
  enemy_troops: number;
  enemy_tiles: number;  // NEW: Total tiles owned by this enemy player
}

class GameBridge {
  private game: Game | null = null;
  private rlPlayer: Player | null = null;
  private aiPlayers: Player[] = [];
  private currentTick: number = 0;
  private maxTicks: number = 50000;  // High limit - let Python env control episode length

  // Cache settings
  private mapName: string = 'plains';
  private numPlayers: number = 6;
  private isInitialized: boolean = false;

  constructor() {
    this.log('GameBridge (Cached) initialized');
  }

  /**
   * Initialize game once - this is slow but only happens once
   */
  async initialize(mapName: string = 'plains', numPlayers: number = 6): Promise<void> {
    if (this.isInitialized && this.mapName === mapName && this.numPlayers === numPlayers) {
      this.log('Already initialized, skipping');
      return;
    }

    this.log(`Initializing with map: ${mapName}, ${numPlayers} players (this may take 30-60 seconds)...`);
    const startTime = Date.now();

    this.mapName = mapName;
    this.numPlayers = numPlayers;

    try {
      // Create player list: 1 RL agent + (numPlayers-1) AI bots
      const players: PlayerInfo[] = [
        new PlayerInfo('RL_Agent', PlayerType.Human, null, 'RL_Agent')
      ];

      for (let i = 1; i < numPlayers; i++) {
        players.push(new PlayerInfo(`AI_Bot_${i}`, PlayerType.Bot, null, `AI_Bot_${i}`));
      }

      this.log(`Creating game with ${players.length} players: 1 RL agent + ${numPlayers - 1} AI bots`);

      // Load map once - this is the slow part
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

      this.log(`Game created with ${this.game.allPlayers().length} players, adding spawn points...`);

      // Distribute players around the map edges with randomization
      const width = this.game.width();
      const height = this.game.height();
      const spawnExecutions: SpawnExecution[] = [];

      // Add random offset to starting angle to vary spawn positions each episode
      const angleOffset = Math.random() * 2 * Math.PI;

      // Calculate spawn positions evenly distributed around the map perimeter
      for (let i = 0; i < numPlayers; i++) {
        const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;

        // Add small random offsets to x,y positions (±5 tiles)
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

        this.log(`  Player ${i} (${playerName}) spawning at (${x}, ${y})`);
      }

      this.game.addExecution(...spawnExecutions);

      this.log(`Executing spawn phase...`);

      // Execute spawn phase
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      this.log(`Spawn phase complete at tick ${this.game.ticks()}`);

      // Get players by ID
      const allPlayers = this.game.allPlayers();
      this.log(`Found ${allPlayers.length} total players`);

      if (allPlayers.length < numPlayers) {
        throw new Error(`Expected ${numPlayers} players, got ${allPlayers.length}`);
      }

      this.rlPlayer = this.game.player('RL_Agent');
      if (!this.rlPlayer) {
        throw new Error('Could not find RL_Agent');
      }

      // Get all AI players
      this.aiPlayers = [];
      for (let i = 1; i < numPlayers; i++) {
        const aiPlayer = this.game.player(`AI_Bot_${i}`);
        if (!aiPlayer) {
          throw new Error(`Could not find AI_Bot_${i}`);
        }
        this.aiPlayers.push(aiPlayer);
      }

      this.log(`RL Player: tiles=${this.rlPlayer.numTilesOwned()}, troops=${this.rlPlayer.troops()}, alive=${this.rlPlayer.isAlive()}`);
      for (let i = 0; i < this.aiPlayers.length; i++) {
        this.log(`AI Player ${i+1}: tiles=${this.aiPlayers[i].numTilesOwned()}, troops=${this.aiPlayers[i].troops()}, alive=${this.aiPlayers[i].isAlive()}`);
      }

      this.currentTick = Number(this.game.ticks());
      this.isInitialized = true;

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      this.log(`Initialization complete in ${elapsed}s - ready for fast resets!`);

    } catch (error: any) {
      this.log(`Initialization FAILED: ${error.message}`);
      if (error.stack) {
        console.error(error.stack);
      }
      throw error;
    }
  }

  /**
   * Fast reset - reuses existing game, just resets state
   */
  async reset(mapName: string = 'plains', difficulty: string = 'easy', tickInterval?: number, numPlayers?: number): Promise<GameState> {
    const players = numPlayers || this.numPlayers;

    // Initialize if needed (slow first time only)
    if (!this.isInitialized || mapName !== this.mapName || players !== this.numPlayers) {
      await this.initialize(mapName, players);
    } else {
      // Fast reset - just reset game state
      this.log('Fast reset (reusing loaded map)');

      // Create player list
      const playerInfos: PlayerInfo[] = [
        playerInfo('RL_Agent', PlayerType.Human)
      ];

      for (let i = 1; i < this.numPlayers; i++) {
        playerInfos.push(playerInfo(`AI_Bot_${i}`, PlayerType.Bot));
      }

      // Create new game with same map (still uses cached binary data)
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

      // Distribute players around the map with randomization
      const width = this.game.width();
      const height = this.game.height();
      const spawnExecutions: SpawnExecution[] = [];

      // Add random offset to starting angle to vary spawn positions each episode
      const angleOffset = Math.random() * 2 * Math.PI;

      for (let i = 0; i < this.numPlayers; i++) {
        const angle = (i / this.numPlayers) * 2 * Math.PI + angleOffset;

        // Add small random offsets to x,y positions (±5 tiles)
        const baseX = Math.floor(width / 2 + (width / 2 - 15) * Math.cos(angle));
        const baseY = Math.floor(height / 2 + (height / 2 - 15) * Math.sin(angle));
        const x = Math.max(5, Math.min(width - 5, baseX + Math.floor((Math.random() - 0.5) * 10)));
        const y = Math.max(5, Math.min(height - 5, baseY + Math.floor((Math.random() - 0.5) * 10)));

        const spawnPos = this.game.ref(x, y);

        const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
        const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;

        spawnExecutions.push(
          new SpawnExecution(
            playerInfo(playerName, playerType),
            spawnPos
          )
        );
      }

      this.game.addExecution(...spawnExecutions);

      // Execute spawn phase
      while (this.game.inSpawnPhase()) {
        this.game.executeNextTick();
      }

      // Get players by ID (same as initialize path)
      this.rlPlayer = this.game.player('RL_Agent');
      if (!this.rlPlayer) {
        throw new Error('Could not find RL_Agent');
      }

      this.aiPlayers = [];
      for (let i = 1; i < this.numPlayers; i++) {
        const aiPlayer = this.game.player(`AI_Bot_${i}`);
        if (!aiPlayer) {
          throw new Error(`Could not find AI_Bot_${i}`);
        }
        this.aiPlayers.push(aiPlayer);
      }

      this.currentTick = Number(this.game.ticks());
    }

    return this.getState();
  }

  tick(): GameState {
    if (!this.game) throw new Error('Game not initialized');

    // Execute tick and capture game updates (includes conquest events)
    const updates = this.game.executeNextTick();
    this.currentTick++;

    // Check for conquest events where RL agent is the conqueror
    let enemiesKilledThisTick = 0;
    const conquestEvents = updates[GameUpdateType.ConquestEvent] || [];

    if (this.rlPlayer) {
      for (const event of conquestEvents) {
        if (event.conquerorId === this.rlPlayer.id()) {
          enemiesKilledThisTick++;
          this.log(`RL Agent eliminated player ${event.conqueredId}! Gold bonus: ${event.gold}`);
        }
      }
    }

    // Get state and add kill count
    const state = this.getState();
    state.enemies_killed_this_tick = enemiesKilledThisTick;

    return state;
  }

  getState(): GameState {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) {
      throw new Error('Game not initialized');
    }

    // Get alive players only
    const aliveAIPlayers = this.aiPlayers.filter(ai => ai.isAlive());

    // Count total enemy tiles and troops (all alive AI players combined)
    const enemyTiles = aliveAIPlayers.reduce((sum, ai) => sum + ai.numTilesOwned(), 0);
    const enemyTroops = aliveAIPlayers.reduce((sum, ai) => sum + ai.troops(), 0);

    // Get neighboring enemy players and sum their troops
    const borderTiles = Array.from(this.rlPlayer.borderTiles());
    const neighboringPlayerIds = new Set<number>();

    for (const borderTile of borderTiles) {
      const x = this.game.x(borderTile);
      const y = this.game.y(borderTile);
      const offsets = [{ dx: 0, dy: -1 }, { dx: 0, dy: 1 }, { dx: -1, dy: 0 }, { dx: 1, dy: 0 }];

      for (const offset of offsets) {
        const adjX = x + offset.dx;
        const adjY = y + offset.dy;
        if (adjX >= 0 && adjX < this.game.width() && adjY >= 0 && adjY < this.game.height()) {
          const adjTile = this.game.ref(adjX, adjY);
          const owner = this.game.owner(adjTile);
          if (owner.isPlayer() && (owner as Player).id() !== this.rlPlayer.id()) {
            neighboringPlayerIds.add((owner as Player).id());
          }
        }
      }
    }

    const neighborEnemyTroops = aliveAIPlayers
      .filter(ai => neighboringPlayerIds.has(ai.id()))
      .reduce((sum, ai) => sum + ai.troops(), 0);

    // Get current state values
    const tilesOwned = this.rlPlayer.numTilesOwned();
    const troopsOwned = this.rlPlayer.troops();
    const borderTilesCount = this.rlPlayer.borderTiles().size;
    const isAlive = this.rlPlayer.isAlive();

    // === NEW: Strategic metrics ===

    // 1. Troop density
    const troopsPerTile = tilesOwned > 0 ? troopsOwned / tilesOwned : 0;
    const avgEnemyTroopsPerTile = enemyTiles > 0 ? enemyTroops / enemyTiles : 0;

    // 2. Border exposure
    const borderTileRatio = tilesOwned > 0 ? borderTilesCount / tilesOwned : 0;

    // 3. Rankings (1.0 = 1st place, 0.0 = last place)
    // Collect all players (RL + alive AI)
    const allPlayersInfo = [
      { tiles: tilesOwned, troops: troopsOwned, isRL: true },
      ...aliveAIPlayers.map(ai => ({ tiles: ai.numTilesOwned(), troops: ai.troops(), isRL: false }))
    ];

    // Sort by tiles (descending) and find RL agent's rank
    const sortedByTiles = [...allPlayersInfo].sort((a, b) => b.tiles - a.tiles);
    const tileRank = sortedByTiles.findIndex(p => p.isRL);
    const rankByTiles = allPlayersInfo.length > 1
      ? 1.0 - (tileRank / (allPlayersInfo.length - 1))
      : 1.0;

    // Sort by troops (descending) and find RL agent's rank
    const sortedByTroops = [...allPlayersInfo].sort((a, b) => b.troops - a.troops);
    const troopRank = sortedByTroops.findIndex(p => p.isRL);
    const rankByTroops = allPlayersInfo.length > 1
      ? 1.0 - (troopRank / (allPlayersInfo.length - 1))
      : 1.0;

    // 4. Per-player arrays (RL agent first, then alive AI players)
    const playerTiles = [tilesOwned, ...aliveAIPlayers.map(ai => ai.numTilesOwned())];
    const playerTroops = [troopsOwned, ...aliveAIPlayers.map(ai => ai.troops())];
    const playerIsNeighbor = [
      0, // RL agent (ourselves) - not a neighbor
      ...aliveAIPlayers.map(ai => neighboringPlayerIds.has(ai.id()) ? 1 : 0)
    ];

    // === Terminal conditions ===
    const allAIDead = aliveAIPlayers.length === 0;
    const hasLost = !isAlive || tilesOwned === 0;

    // Debug logging
    if (hasLost) {
      this.log(`LOSS DETECTED: isAlive=${isAlive}, tiles=${tilesOwned}, tick=${this.currentTick}`);
    }
    if (tilesOwned <= 10 && tilesOwned > 0) {
      this.log(`WARNING: Low tiles - isAlive=${isAlive}, tiles=${tilesOwned}, tick=${this.currentTick}`);
    }

    return {
      tiles_owned: tilesOwned,
      troops: troopsOwned,
      gold: Number(this.rlPlayer.gold()),
      max_troops: 100000,
      enemy_tiles: enemyTiles,
      enemy_troops: enemyTroops,
      neighbor_enemy_troops: neighborEnemyTroops,
      border_tiles: borderTilesCount,
      cities: this.rlPlayer.units().filter(u => u.type() === 'City').length,
      tick: this.currentTick,
      has_won: allAIDead,
      has_lost: hasLost,
      game_over: hasLost || allAIDead || this.currentTick >= this.maxTicks,
      enemies_killed_this_tick: 0,  // Will be set by tick() if there are conquest events

      // NEW strategic metrics
      troops_per_tile: troopsPerTile,
      avg_enemy_troops_per_tile: avgEnemyTroopsPerTile,
      border_tile_ratio: borderTileRatio,
      rank_by_tiles: rankByTiles,
      rank_by_troops: rankByTroops,

      // NEW per-player arrays
      player_tiles: playerTiles,
      player_troops: playerTroops,
      player_is_neighbor: playerIsNeighbor
    };
  }

  getAttackableNeighbors(): Neighbor[] {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) return [];

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

        // Include neutral territory and any enemy player tiles (not owned by RL agent)
        const isNeutral = !owner.isPlayer();
        const isEnemyPlayer = owner.isPlayer() && (owner as Player).id() !== this.rlPlayer.id();

        if (isEnemyPlayer || isNeutral) {
          // Determine which player owns this tile (for enemy_player_id)
          let enemyPlayerId = 0; // 0 for neutral
          let enemyTroops = 0;
          let enemyTiles = 0;

          if (isEnemyPlayer) {
            const ownerPlayer = owner as Player;
            // Find the AI player index
            const aiIndex = this.aiPlayers.findIndex(ai => ai.id() === ownerPlayer.id());
            enemyPlayerId = aiIndex >= 0 ? aiIndex + 2 : 2; // Start from 2 for AI players
            enemyTroops = ownerPlayer.troops();
            enemyTiles = ownerPlayer.numTilesOwned();
          }

          neighbors.push({
            neighbor_idx: neighbors.length,
            enemy_player_id: enemyPlayerId,
            tile_x: adjX,
            tile_y: adjY,
            enemy_troops: enemyTroops,
            enemy_tiles: enemyTiles
          });

          if (neighbors.length >= 8) return neighbors;
        }
      }
    }

    return neighbors;
  }

  attackTile(tile_x: number, tile_y: number, attack_percentage: number = 0.5): void {
    if (!this.game || !this.rlPlayer || this.aiPlayers.length === 0) {
      throw new Error('Game not initialized');
    }

    const targetTile = this.game.ref(tile_x, tile_y);
    if (!this.rlPlayer.canAttack(targetTile)) {
      this.log(`Cannot attack (${tile_x}, ${tile_y})`);
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

    // Determine the target: owner of the tile or terra nullius
    const owner = this.game.owner(targetTile);
    const targetId = owner.isPlayer()
      ? (owner as Player).id()  // Attack the player who owns it
      : this.game.terraNullius().id();  // Attack neutral territory

    // Validate attackTroops is a valid number
    if (isNaN(attackTroops) || !isFinite(attackTroops)) {
      this.log(`Invalid attack troops: ${attackTroops}, skipping attack`);
      return;
    }

    this.log(`Attacking (${tile_x}, ${tile_y}) with ${attackTroops} troops (${attack_percentage * 100}% of ${currentTroops})`);

    this.game.addExecution(
      new AttackExecution(attackTroops, this.rlPlayer, targetId)
    );
  }

  private log(msg: string): void {
    console.error(`[GameBridge] ${msg}`);
  }
}

// ============================================================================
// IPC Interface with Pre-loading
// ============================================================================

const bridge = new GameBridge();
console.error('[GameBridge] Starting with pre-load strategy...');
console.error('[GameBridge] First reset will be slow (~30-60s), subsequent resets will be fast!');

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
          command.tick_interval,
          command.num_players || 6
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
        bridge.attackTile(command.tile_x, command.tile_y, command.attack_percentage || 0.5);
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

console.error('[GameBridge] Ready - waiting for commands');
