/**
 * Visual Game Bridge for Phase 4 - Real-time visualization
 *
 * Provides full visual state export for the game client
 */

import * as readline from 'readline';
import * as fs from 'fs';
import { PlayerType, Player, Game, PlayerInfo, GameMapType, GameMode, GameType, Difficulty, NameViewData, PlayerID } from '../../base-game/src/core/game/Game';
import { createGame } from '../../base-game/src/core/game/GameImpl';
import { genTerrainFromBin, MapManifest } from '../../base-game/src/core/game/TerrainMapLoader';
import { UserSettings } from '../../base-game/src/core/game/UserSettings';
import { GameConfig } from '../../base-game/src/core/Schemas';
import { TestConfig } from '../../base-game/tests/util/TestConfig';
import { TestServerConfig } from '../../base-game/tests/util/TestServerConfig';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
import { GameUpdateViewData, GameUpdateType } from '../../base-game/src/core/game/GameUpdates';
import { placeName } from '../../base-game/src/client/graphics/NameBoxCalculator';
import * as path from 'path';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface TileState {
  x: number;
  y: number;
  owner_id: number;  // 0 = neutral, 1 = RL agent, 2+ = AI bots
  troops: number;
  is_city: boolean;
  is_mountain: boolean;
  terrain_type: number;  // 0 = plains, 1 = water, 2 = mountains, etc.
}

interface PlayerState {
  id: number;
  name: string;
  is_alive: boolean;
  tiles_owned: number;
  total_troops: number;
  gold: number;
  color: string;  // Hex color for rendering
  rank: number;   // Current ranking (1 = first place)
}

interface VisualState {
  tick: number;
  map_width: number;
  map_height: number;
  tiles: TileState[];
  players: PlayerState[];
  rl_player: {
    id: number;
    tiles_owned: number;
    troops: number;
    territory_pct: number;
    rank: number;
    is_alive: boolean;
    gold: number;
    num_cities: number;
  };
  game_over: boolean;
  winner_id: number | null;
}

interface Command {
  type: 'reset' | 'tick' | 'get_visual_state' | 'attack_direction' | 'shutdown';
  num_bots?: number;
  map_name?: string;
  direction?: string;  // N, NE, E, SE, S, SW, W, NW
  intensity?: number;   // 0.0-1.0
  crop?: {             // Optional: crop a region from the map
    x: number;         // Top-left x
    y: number;         // Top-left y
    width: number;     // Crop width
    height: number;    // Crop height
  };
}

interface Response {
  type: 'visual_state' | 'game_update' | 'ack' | 'error';
  state?: VisualState;
  gameUpdate?: GameUpdateViewData;
  message?: string;
  success?: boolean;
}

// Helper function to convert BigInt to number recursively
function convertBigIntToNumber(obj: any): any {
  if (obj === null || obj === undefined) return obj;

  if (typeof obj === 'bigint') {
    return Number(obj);
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertBigIntToNumber(item));
  }

  if (typeof obj === 'object') {
    const result: any = {};
    for (const key in obj) {
      result[key] = convertBigIntToNumber(obj[key]);
    }
    return result;
  }

  return obj;
}

class VisualGameBridge {
  private game: Game | null = null;
  private rlPlayer: Player | null = null;
  private aiPlayers: Player[] = [];
  private currentTick: number = 0;
  private maxTicks: number = 10000;
  private cropRegion: { x: number; y: number; width: number; height: number } | null = null;
  private playerViewData: Record<PlayerID, NameViewData> = {};
  private needsFullUpdate: boolean = false;  // Track if we need to send all tiles

  // Color palette for players (40 colors)
  private readonly PLAYER_COLORS = [
    // RL Agent (bright red)
    '#FF0000',
    // AI Bots (diverse palette)
    '#0000FF', '#00FF00', '#FFFF00', '#FF00FF', '#00FFFF',
    '#FFA500', '#800080', '#FFD700', '#FF1493', '#00CED1',
    '#FF6347', '#4169E1', '#32CD32', '#FF4500', '#DA70D6',
    '#20B2AA', '#FF69B4', '#87CEEB', '#BA55D3', '#F08080',
    '#9370DB', '#3CB371', '#FF8C00', '#4682B4', '#D2691E',
    '#DC143C', '#00FA9A', '#FFB6C1', '#48D1CC', '#C71585',
    '#FF7F50', '#6495ED', '#ADFF2F', '#FF6347', '#DB7093',
    '#40E0D0', '#EE82EE', '#F5DEB3', '#98FB98', '#DDA0DD'
  ];

  private log(message: string) {
    console.error(`[VisualBridge] ${message}`);
  }

  async initialize(numBots: number, mapName: string = 'plains', crop?: { x: number; y: number; width: number; height: number }): Promise<VisualState> {
    console.error(`[BRIDGE] initialize() called: bots=${numBots}, map=${mapName}, crop=${JSON.stringify(crop)}`);
    this.log(`Initializing battle royale: map=${mapName}, bots=${numBots}`);

    if (crop) {
      this.cropRegion = crop;
      console.error(`[BRIDGE] ✓ Crop region SET: center will be (${crop.x + crop.width/2}, ${crop.y + crop.height/2})`);
      this.log(`Cropping map to region: x=${crop.x}, y=${crop.y}, width=${crop.width}, height=${crop.height}`);
    } else {
      console.error(`[BRIDGE] ✗ NO CROP - will spawn across full map`);
    }

    const numPlayers = numBots + 1;  // RL agent + bots

    // Create players
    const players: PlayerInfo[] = [new PlayerInfo('RL_Agent', PlayerType.Human, null, 'RL_Agent')];
    for (let i = 1; i <= numBots; i++) {
      players.push(new PlayerInfo(`AI_Bot_${i}`, PlayerType.Bot, null, `AI_Bot_${i}`));
    }

    this.log(`Creating game with ${numPlayers} players...`);

    // Load map from map-generator/generated/maps
    const mapsDir = path.join(__dirname, '../../base-game/map-generator/generated/maps');
    const mapBinPath = path.join(mapsDir, mapName, 'map.bin');
    const miniMapBinPath = path.join(mapsDir, mapName, 'mini_map.bin');
    const manifestPath = path.join(mapsDir, mapName, 'manifest.json');

    this.log(`Loading map from: ${mapBinPath}`);

    const mapBinBuffer = fs.readFileSync(mapBinPath);
    const miniMapBinBuffer = fs.readFileSync(miniMapBinPath);
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as MapManifest;

    const gameMap = await genTerrainFromBin(manifest.map, mapBinBuffer);
    const miniGameMap = await genTerrainFromBin(manifest.mini_map, miniMapBinBuffer);

    // Configure the game
    const gameConfig: GameConfig = {
      gameMap: GameMapType.Asia,
      gameMode: GameMode.FFA,
      gameType: GameType.Singleplayer,
      difficulty: Difficulty.Easy,
      disableNPCs: false,
      donateGold: false,
      donateTroops: false,
      bots: 0,
      infiniteGold: false,
      infiniteTroops: false,
      instantBuild: false,
    };

    // Suppress console.debug
    console.debug = () => {};

    // Create config using TestConfig
    const serverConfig = new TestServerConfig();
    const config = new TestConfig(serverConfig, gameConfig, new UserSettings(), false);

    // Create game
    this.game = createGame(players, [], gameMap, miniGameMap, config);

    if (!this.game) {
      throw new Error('createGame() returned null');
    }

    this.log(`Game created, spawning ${numPlayers} players...`);

    // Spawn players distributed around the map (or cropped region)
    const fullWidth = this.game.width();
    const fullHeight = this.game.height();

    // If cropping, use crop region dimensions for spawning
    const spawnCenterX = this.cropRegion ? this.cropRegion.x + this.cropRegion.width / 2 : fullWidth / 2;
    const spawnCenterY = this.cropRegion ? this.cropRegion.y + this.cropRegion.height / 2 : fullHeight / 2;
    const spawnRadius = this.cropRegion ? Math.min(this.cropRegion.width, this.cropRegion.height) / 2 - 20 : Math.min(fullWidth, fullHeight) / 2 - 20;

    const spawnExecutions: SpawnExecution[] = [];
    const angleOffset = Math.random() * 2 * Math.PI;

    console.error(`[BRIDGE] Map dimensions: ${fullWidth}x${fullHeight}`);
    if (this.cropRegion) {
      console.error(`[BRIDGE] Crop region: x=${this.cropRegion.x}, y=${this.cropRegion.y}, w=${this.cropRegion.width}, h=${this.cropRegion.height}`);
    }
    console.error(`[BRIDGE] Spawn calculation: center=(${spawnCenterX}, ${spawnCenterY}), radius=${spawnRadius}`);
    this.log(`Spawning players: center=(${spawnCenterX}, ${spawnCenterY}), radius=${spawnRadius}`);

    for (let i = 0; i < numPlayers; i++) {
      const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;
      const baseX = Math.floor(spawnCenterX + spawnRadius * Math.cos(angle));
      const baseY = Math.floor(spawnCenterY + spawnRadius * Math.sin(angle));

      // Find a valid land tile near the target position
      let x = baseX;
      let y = baseY;
      let foundLand = false;

      // Search in expanding circles for land
      for (let searchRadius = 0; searchRadius < 200 && !foundLand; searchRadius += 10) {
        for (let attempt = 0; attempt < 20; attempt++) {
          const searchAngle = (attempt / 20) * 2 * Math.PI;
          const testX = Math.floor(baseX + searchRadius * Math.cos(searchAngle));
          const testY = Math.floor(baseY + searchRadius * Math.sin(searchAngle));

          // Check bounds
          if (testX < 10 || testX >= fullWidth - 10 || testY < 10 || testY >= fullHeight - 10) {
            continue;
          }

          // Check if it's land
          const testTile = this.game.ref(testX, testY);
          if (testTile >= 0 && !this.game.map().isWater(testTile)) {
            x = testX;
            y = testY;
            foundLand = true;
            break;
          }
        }
      }

      if (!foundLand) {
        console.error(`[BRIDGE] WARNING: Could not find land for player ${i}, spawning at (${x}, ${y}) anyway`);
      }

      const spawnPos = this.game.ref(x, y);
      const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
      const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;

      console.error(`[BRIDGE] Player ${i} (${playerName}) spawning at (${x}, ${y}) - tile=${spawnPos}, foundLand=${foundLand}`);

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

    // Mark that we need to send full map state on next tick
    this.needsFullUpdate = true;

    // Get players
    this.rlPlayer = this.game.player('RL_Agent');
    if (!this.rlPlayer) {
      throw new Error('RL Player not found');
    }

    this.aiPlayers = [];
    for (let i = 1; i <= numBots; i++) {
      const aiPlayer = this.game.player(`AI_Bot_${i}`);
      if (aiPlayer) {
        this.aiPlayers.push(aiPlayer);
      }
    }

    this.currentTick = Number(this.game.ticks());
    this.log(`Game initialized at tick ${this.currentTick}`);

    return this.getVisualState();
  }

  tick(): Response {
    if (!this.game) throw new Error('Game not initialized');

    // Execute game tick and get updates
    const updates = this.game.executeNextTick();
    this.currentTick = Number(this.game.ticks());

    // Update player view data periodically (like GameRunner does)
    if (this.currentTick < 3 || this.currentTick % 30 === 0) {
      this.game.players().forEach((p) => {
        this.playerViewData[p.id()] = placeName(this.game!, p);
      });
    }

    // Pack tile updates
    let packedTileUpdates = updates[GameUpdateType.Tile].map((u: any) => u.update);
    updates[GameUpdateType.Tile] = [];

    // On first tick after reset, send ALL owned tiles (not just changes)
    if (this.needsFullUpdate) {
      this.log(`Sending full map state with owned tiles`);
      const allTileUpdates: bigint[] = [];

      // Iterate through all PLAYERS and get their owned tiles
      this.game.players().forEach((player: Player) => {
        player.tiles().forEach((tileRef: number) => {
          const tileUpdate = this.game.toTileUpdate(tileRef);
          allTileUpdates.push(tileUpdate);
        });
      });

      packedTileUpdates = allTileUpdates;
      this.needsFullUpdate = false;  // Clear flag
      this.log(`Packed ${allTileUpdates.length} owned tiles from ${this.game.players().length} players`);
    }

    // Convert BigUint64Array to regular array for JSON serialization
    const packedTileUpdatesArray = new BigUint64Array(packedTileUpdates);
    const packedTileUpdatesNumbers = Array.from(packedTileUpdatesArray, n => Number(n));

    // Convert all BigInt values in updates to numbers
    const updatesWithNumbers = convertBigIntToNumber(updates);
    const playerNameViewDataWithNumbers = convertBigIntToNumber(this.playerViewData);

    // Create serializable GameUpdateViewData (with number array instead of BigUint64Array)
    const gameUpdateViewData: any = {
      tick: this.currentTick,
      packedTileUpdates: packedTileUpdatesNumbers,  // Use number array for JSON
      updates: updatesWithNumbers,
      playerNameViewData: playerNameViewDataWithNumbers,
    };

    // Also include simple visual state for backward compatibility
    const visualState = this.getVisualState();

    return {
      type: 'game_update',
      gameUpdate: gameUpdateViewData,
      state: visualState,
      success: true
    };
  }

  getVisualState(): VisualState {
    if (!this.game || !this.rlPlayer) {
      throw new Error('Game not initialized');
    }

    const fullWidth = this.game.width();
    const fullHeight = this.game.height();

    // Use crop region if specified, otherwise use full map
    const viewX = this.cropRegion ? this.cropRegion.x : 0;
    const viewY = this.cropRegion ? this.cropRegion.y : 0;
    const width = this.cropRegion ? this.cropRegion.width : fullWidth;
    const height = this.cropRegion ? this.cropRegion.height : fullHeight;
    const allPlayers = [this.rlPlayer, ...this.aiPlayers];

    // Calculate ranks (by tiles owned)
    const playersByTiles = [...allPlayers]
      .filter(p => p.isAlive())
      .sort((a, b) => b.numTilesOwned() - a.numTilesOwned());

    const playerRanks = new Map<number, number>();
    playersByTiles.forEach((player, index) => {
      playerRanks.set(player.id(), index + 1);
    });

    // Dead players get worst rank
    allPlayers.filter(p => !p.isAlive()).forEach(player => {
      playerRanks.set(player.id(), allPlayers.length + 1);
    });

    // Build city positions map
    const cityPositions = new Set<string>();
    allPlayers.forEach(player => {
      player.units().filter(u => u.type() === 'City').forEach(city => {
        const cityX = this.game!.x(city.tile());
        const cityY = this.game!.y(city.tile());
        cityPositions.add(`${cityX},${cityY}`);
      });
    });

    // Build player ID mapping (RL = 1, AI bots = 2+)
    const playerIdMap = new Map<number, number>();
    playerIdMap.set(this.rlPlayer.id(), 1);
    this.aiPlayers.forEach((ai, index) => {
      playerIdMap.set(ai.id(), index + 2);
    });

    // Extract tiles (from crop region if specified)
    const tiles: TileState[] = [];
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // Actual game coordinates
        const gameX = viewX + x;
        const gameY = viewY + y;

        const tileRef = this.game.ref(gameX, gameY);
        const owner = this.game.owner(tileRef);

        // Determine owner_id
        let owner_id = 0;
        if (owner.isPlayer()) {
          const ownerPlayer = owner as Player;
          owner_id = playerIdMap.get(ownerPlayer.id()) || 0;
        }

        const terrainType = this.game.terrainType(tileRef);
        const is_mountain = terrainType === 2;
        const is_city = cityPositions.has(`${gameX},${gameY}`);

        tiles.push({
          x,  // Relative to view (0-based)
          y,
          owner_id,
          troops: 0,  // Troops are per-player, not per-tile
          is_city,
          is_mountain,
          terrain_type: terrainType  // Send full terrain type for proper rendering
        });
      }
    }

    // Extract player states
    const players: PlayerState[] = allPlayers.map((player, idx) => ({
      id: idx + 1,
      name: idx === 0 ? 'RL Agent' : `AI Bot ${idx}`,
      is_alive: player.isAlive(),
      tiles_owned: player.numTilesOwned(),
      total_troops: player.troops(),
      gold: Number(player.gold()),
      color: this.PLAYER_COLORS[idx] || '#FFFFFF',
      rank: playerRanks.get(player.id()) || allPlayers.length + 1
    }));

    // Total tiles (excluding mountains)
    const totalTiles = tiles.filter(t => !t.is_mountain).length;
    const rlTiles = this.rlPlayer.numTilesOwned();
    const territoryPct = totalTiles > 0 ? rlTiles / totalTiles : 0;

    // Check for winner
    const alivePlayers = allPlayers.filter(p => p.isAlive());
    let winner_id: number | null = null;
    let game_over = false;

    if (alivePlayers.length === 1) {
      winner_id = playerIdMap.get(alivePlayers[0].id()) || null;
      game_over = true;
    } else if (!this.rlPlayer.isAlive()) {
      game_over = true;
    } else if (this.currentTick >= this.maxTicks) {
      game_over = true;
      // Winner is the one with most tiles
      if (playersByTiles.length > 0) {
        winner_id = playerIdMap.get(playersByTiles[0].id()) || null;
      }
    }

    return {
      tick: this.currentTick,
      map_width: width,
      map_height: height,
      tiles,
      players,
      rl_player: {
        id: 1,
        tiles_owned: rlTiles,
        troops: this.rlPlayer.troops(),
        territory_pct: territoryPct,
        rank: playerRanks.get(this.rlPlayer.id()) || allPlayers.length + 1,
        is_alive: this.rlPlayer.isAlive(),
        gold: Number(this.rlPlayer.gold()),
        num_cities: this.rlPlayer.units().filter(u => u.type() === 'City').length
      },
      game_over,
      winner_id
    };
  }

  attackDirection(direction: string, intensity: number) {
    if (!this.game || !this.rlPlayer) {
      throw new Error('Game not initialized');
    }

    // Find attackable target
    if (direction !== 'WAIT') {
      const currentTroops = this.rlPlayer.troops();
      const attackTroops = Math.floor(currentTroops * intensity);

      if (attackTroops >= 1) {
        const borderTiles = Array.from(this.rlPlayer.borderTiles());

        // Find ANY valid attack target
        for (const borderTile of borderTiles) {
          const x = this.game.x(borderTile);
          const y = this.game.y(borderTile);

          // Check all 4 directions for attackable tiles
          const offsets = [
            { dx: 0, dy: -1 }, // N
            { dx: 1, dy: 0 },  // E
            { dx: 0, dy: 1 },  // S
            { dx: -1, dy: 0 }  // W
          ];

          for (const offset of offsets) {
            const targetX = x + offset.dx;
            const targetY = y + offset.dy;

            if (targetX < 0 || targetX >= this.game.width() ||
                targetY < 0 || targetY >= this.game.height()) {
              continue;
            }

            const targetTile = this.game.ref(targetX, targetY);
            const owner = this.game.owner(targetTile);

            // Check if we can attack this tile
            if (!owner.isPlayer() || (owner as Player).id() !== this.rlPlayer.id()) {
              if (this.rlPlayer.canAttack(targetTile)) {
                const targetId = owner.isPlayer()
                  ? (owner as Player).id()
                  : this.game.terraNullius().id();

                const attack = new AttackExecution(
                  attackTroops,
                  this.rlPlayer,
                  targetId
                );
                this.game.addExecution(attack);
                // this.log(`Attack added: ${attackTroops} troops to (${targetX},${targetY})`);
                return;
              }
            }
          }
        }
      }
    }
  }

  close() {
    this.game = null;
    this.rlPlayer = null;
    this.aiPlayers = [];
  }
}

// Main IPC loop
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
        case 'reset': {
          const numBots = command.num_bots || 10;
          const mapName = command.map_name || 'plains';
          const crop = command.crop || undefined;
          console.error(`[BRIDGE] Reset command: bots=${numBots}, map=${mapName}, crop=${JSON.stringify(crop)}`);
          const state = await bridge.initialize(numBots, mapName, crop);
          response = { type: 'visual_state', state, success: true };
          break;
        }

        case 'tick': {
          response = bridge.tick();  // bridge.tick() already returns a complete Response
          break;
        }

        case 'get_visual_state': {
          const state = bridge.getVisualState();
          response = { type: 'visual_state', state, success: true };
          break;
        }

        case 'attack_direction': {
          const direction = command.direction || 'WAIT';
          const intensity = command.intensity || 0.5;
          bridge.attackDirection(direction, intensity);
          response = { type: 'ack', success: true };
          break;
        }

        case 'shutdown': {
          bridge.close();
          response = { type: 'ack', success: true };
          console.log(JSON.stringify(response));
          process.exit(0);
        }

        default:
          response = { type: 'error', message: `Unknown command: ${command.type}` };
      }

      console.log(JSON.stringify(response));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.log(JSON.stringify({ type: 'error', message: errorMsg }));
    }
  });

  rl.on('close', () => {
    bridge.close();
    process.exit(0);
  });
}

main().catch(error => {
  console.error('[VisualBridge] Fatal error:', error);
  process.exit(1);
});
