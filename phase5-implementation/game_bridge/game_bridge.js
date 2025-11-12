/**
 * Game Bridge for Phase 5 - Clean Implementation with Working Attacks
 *
 * Features:
 * - Battle royale mode with configurable bots
 * - Working attack execution using AttackExecution
 * - Spatial map extraction (512×512 → 128×128)
 * - 16 global features
 * - GPU-optimized
 */
import * as readline from 'readline';
import { PlayerType } from '../../base-game/src/core/game/Game';
import { createGame } from '../../base-game/src/core/game/GameImpl';
import { genTerrainFromBin } from '../../base-game/src/core/game/TerrainMapLoader';
import { UserSettings } from '../../base-game/src/core/game/UserSettings';
import { TestConfig } from '../../base-game/tests/util/TestConfig';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
import * as path from 'path';
import * as fs from 'fs';
import { dirname } from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
class GameBridge {
    constructor() {
        this.game = null;
        this.rlPlayer = null;
        this.aiPlayers = [];
        this.currentTick = 0;
        this.maxTicks = 50000;
        // Map cache
        this.mapName = 'plains';
        this.numPlayers = 11; // 1 RL + 10 bots
        this.mapWidth = 512;
        this.mapHeight = 512;
        // History for computing rates
        this.previousTiles = 0;
        this.territoryHistory = [];
        this.log('GameBridge Phase 5 initialized (Clean with working attacks)');
    }
    /**
     * Initialize/reset game
     */
    async initialize(mapName = 'plains', numPlayers = 11) {
        this.mapName = mapName;
        this.numPlayers = numPlayers;
        try {
            // Create player list: 1 RL agent + (numPlayers-1) AI bots
            const players = [
                { name: 'RL_Agent', type: PlayerType.Human }
            ];
            // Add AI bots
            for (let i = 1; i < numPlayers; i++) {
                players.push({
                    name: `AI_Bot_${i}`,
                    type: PlayerType.Bot,
                    difficulty: 'Easy'
                });
            }
            // Load map
            const mapDir = path.join(__dirname, '../../base-game/resources/maps', mapName);
            const manifestPath = path.join(mapDir, 'map_manifest.json');
            if (!fs.existsSync(manifestPath)) {
                throw new Error(`Map not found: ${mapName}`);
            }
            const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
            this.mapWidth = manifest.width;
            this.mapHeight = manifest.height;
            const terrainData = genTerrainFromBin(mapDir);
            // Create game with test config
            const config = new TestConfig();
            const userSettings = new UserSettings({});
            this.game = createGame({
                config,
                width: this.mapWidth,
                height: this.mapHeight,
                terrainData,
                userSettings,
                players,
                mode: 'Battle Royale',
                serverConfig: undefined
            });
            // Spawn players
            const spawnExecutions = [];
            const angleStep = (2 * Math.PI) / players.length;
            for (let i = 0; i < players.length; i++) {
                const player = this.game.player(players[i].name);
                if (!player)
                    continue;
                const angle = i * angleStep;
                const spawnRadius = Math.min(this.mapWidth, this.mapHeight) * 0.4;
                const centerX = this.mapWidth / 2;
                const centerY = this.mapHeight / 2;
                const spawnX = Math.floor(centerX + Math.cos(angle) * spawnRadius);
                const spawnY = Math.floor(centerY + Math.sin(angle) * spawnRadius);
                spawnExecutions.push(new SpawnExecution(player, spawnX, spawnY));
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
            this.currentTick = 0;
            this.previousTiles = this.rlPlayer.numTilesOwned();
            this.territoryHistory = [];
            this.log(`Game initialized: map=${mapName}, size=${this.mapWidth}x${this.mapHeight}, players=${numPlayers}`);
            return this.getState();
        }
        catch (error) {
            this.log(`Initialization error: ${error}`);
            throw error;
        }
    }
    /**
     * Execute one game tick
     */
    tick() {
        if (!this.game)
            throw new Error('Game not initialized');
        this.game.executeNextTick();
        this.currentTick++;
        return this.getState();
    }
    /**
     * Get current game state with spatial maps and global features
     */
    getState() {
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
        const numCities = Array.from(this.rlPlayer.units()).filter(u => u.type() === 'City').length;
        // Rank
        const alivePlayers_copy = alivePlayers.slice().sort((a, b) => b.numTilesOwned() - a.numTilesOwned());
        const rank = alivePlayers_copy.findIndex(p => p.id() === this.rlPlayer.id()) + 1;
        // Spatial maps
        const territoryMap = this.extractTerritoryMap();
        const troopMap = Array(this.mapHeight).fill(0).map(() => Array(this.mapWidth).fill(0));
        // Global features
        const borderTiles = Array.from(this.rlPlayer.borderTiles()).length;
        const borderPressure = this.computeBorderPressure();
        const timeAlive = this.currentTick;
        const nearestThreat = this.computeNearestThreat();
        const territoryChange = this.computeTerritoryChange(territoryPct);
        // NEW: Detect territory clusters
        const clusters = this.detectTerritoryClusters();
        // Update history
        this.previousTiles = tilesOwned;
        // Check game over
        const has_won = territoryPct >= 0.80;
        const has_lost = !this.rlPlayer.isAlive();
        const game_over = has_won || has_lost || this.currentTick >= this.maxTicks;
        return {
            tick: this.currentTick,
            game_over,
            has_won,
            has_lost,
            tiles_owned: tilesOwned,
            total_tiles: totalTiles,
            territory_pct: territoryPct,
            neutral_tiles: neutralTiles,
            population,
            max_population: maxPopulation,
            population_growth_rate: populationGrowthRate,
            gold,
            num_cities: numCities,
            rank,
            total_players: this.numPlayers,
            alive_players: alivePlayers.length,
            territory_map: territoryMap,
            troop_map: troopMap,
            border_tiles: borderTiles,
            border_pressure: borderPressure,
            time_alive: timeAlive,
            nearest_threat_distance: nearestThreat,
            territory_change: territoryChange,
            clusters: clusters // NEW: Territory clusters
        };
    }
    /**
     * Execute attack from specific cluster in direction with intensity
     * NEW: Cluster-aware attack system
     */
    attackDirection(direction, intensity, clusterId = 0) {
        if (!this.game || !this.rlPlayer) {
            return false;
        }
        // Direction 8 = WAIT, don't attack
        if (direction === 8) {
            return true;
        }
        // Get clusters
        const clusters = this.detectTerritoryClusters();
        // Validate cluster ID
        if (clusterId < 0 || clusterId >= clusters.length) {
            // Invalid cluster - fallback to largest cluster
            clusterId = 0;
        }
        if (clusters.length === 0) {
            return false; // No territory!
        }
        const cluster = clusters[clusterId];
        const attackTroops = Math.floor(cluster.troop_count * intensity);
        if (attackTroops < 1) {
            return false;
        }
        // Direction vectors: N, NE, E, SE, S, SW, W, NW
        const directionVectors = [
            { dx: 0, dy: -1 }, // 0: N
            { dx: 1, dy: -1 }, // 1: NE
            { dx: 1, dy: 0 }, // 2: E
            { dx: 1, dy: 1 }, // 3: SE
            { dx: 0, dy: 1 }, // 4: S
            { dx: -1, dy: 1 }, // 5: SW
            { dx: -1, dy: 0 }, // 6: W
            { dx: -1, dy: -1 } // 7: NW
        ];
        const targetDir = directionVectors[direction];
        // Find border tiles from THIS cluster that can attack in the target direction
        for (const borderTile of cluster.border_tiles) {
            const x = this.game.x(borderTile);
            const y = this.game.y(borderTile);
            // Check the target direction
            const targetX = x + targetDir.dx;
            const targetY = y + targetDir.dy;
            if (targetX < 0 || targetX >= this.mapWidth ||
                targetY < 0 || targetY >= this.mapHeight) {
                continue;
            }
            const targetTile = this.game.ref(targetX, targetY);
            const owner = this.game.owner(targetTile);
            // Check if we can attack this tile
            if (!owner.isPlayer() || owner.id() !== this.rlPlayer.id()) {
                if (this.rlPlayer.canAttack(targetTile)) {
                    // Found valid target in the specified direction!
                    const targetId = owner.isPlayer()
                        ? owner.id()
                        : this.game.terraNullius().id();
                    // Create and add attack execution
                    const attack = new AttackExecution(attackTroops, this.rlPlayer, targetId);
                    this.game.addExecution(attack);
                    this.log(`Cluster ${clusterId} attacks ${['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][direction]}: ${attackTroops} troops (${(intensity * 100).toFixed(0)}%)`);
                    return true;
                }
            }
        }
        // No valid targets in that direction from this cluster
        return false;
    }
    /**
     * Extract territory map (player IDs per tile)
     */
    extractTerritoryMap() {
        if (!this.game || !this.rlPlayer) {
            return [];
        }
        const map = [];
        for (let y = 0; y < this.mapHeight; y++) {
            const row = [];
            for (let x = 0; x < this.mapWidth; x++) {
                const tile = this.game.ref(x, y);
                const owner = this.game.owner(tile);
                if (!owner.isPlayer()) {
                    row.push(0); // Neutral/Terra Nullius
                }
                else {
                    const ownerPlayer = owner;
                    if (ownerPlayer.id() === this.rlPlayer.id()) {
                        row.push(1); // RL player
                    }
                    else {
                        // Find AI player index
                        const aiIndex = this.aiPlayers.findIndex(ai => ai.id() === ownerPlayer.id());
                        row.push(aiIndex >= 0 ? aiIndex + 2 : 999); // AI players: 2, 3, 4, ...
                    }
                }
            }
            map.push(row);
        }
        return map;
    }
    /**
     * Compute border pressure (how many enemy troops near borders)
     */
    computeBorderPressure() {
        if (!this.game || !this.rlPlayer)
            return 0;
        const borderTiles = Array.from(this.rlPlayer.borderTiles());
        let pressure = 0;
        for (const borderTile of borderTiles) {
            const x = this.game.x(borderTile);
            const y = this.game.y(borderTile);
            // Check adjacent tiles for enemies
            const offsets = [
                { dx: -1, dy: 0 }, { dx: 1, dy: 0 },
                { dx: 0, dy: -1 }, { dx: 0, dy: 1 }
            ];
            for (const offset of offsets) {
                const nx = x + offset.dx;
                const ny = y + offset.dy;
                if (nx < 0 || nx >= this.mapWidth || ny < 0 || ny >= this.mapHeight)
                    continue;
                const tile = this.game.ref(nx, ny);
                const owner = this.game.owner(tile);
                if (owner.isPlayer() && owner.id() !== this.rlPlayer.id()) {
                    pressure += 1;
                }
            }
        }
        return pressure / Math.max(borderTiles.length, 1);
    }
    /**
     * Compute nearest threat distance
     */
    computeNearestThreat() {
        if (!this.game || !this.rlPlayer)
            return 999;
        // Find RL player center
        let centerX = 0, centerY = 0, count = 0;
        for (let y = 0; y < this.mapHeight; y++) {
            for (let x = 0; x < this.mapWidth; x++) {
                const tile = this.game.ref(x, y);
                const owner = this.game.owner(tile);
                if (owner.isPlayer() && owner.id() === this.rlPlayer.id()) {
                    centerX += x;
                    centerY += y;
                    count++;
                }
            }
        }
        if (count === 0)
            return 999;
        centerX = centerX / count;
        centerY = centerY / count;
        // Find nearest enemy center
        let minDistance = 999;
        const rlTiles = this.rlPlayer.numTilesOwned();
        for (const aiPlayer of this.aiPlayers) {
            if (!aiPlayer.isAlive())
                continue;
            if (aiPlayer.numTilesOwned() < rlTiles * 0.5)
                continue;
            let enemyCenterX = 0, enemyCenterY = 0, enemyCount = 0;
            for (let y = 0; y < this.mapHeight; y++) {
                for (let x = 0; x < this.mapWidth; x++) {
                    const tile = this.game.ref(x, y);
                    const owner = this.game.owner(tile);
                    if (owner.isPlayer() && owner.id() === aiPlayer.id()) {
                        enemyCenterX += x;
                        enemyCenterY += y;
                        enemyCount++;
                    }
                }
            }
            if (enemyCount === 0)
                continue;
            enemyCenterX /= enemyCount;
            enemyCenterY /= enemyCount;
            const distance = Math.sqrt(Math.pow(centerX - enemyCenterX, 2) +
                Math.pow(centerY - enemyCenterY, 2));
            minDistance = Math.min(minDistance, distance);
        }
        return minDistance;
    }
    /**
     * Compute territory change over last few ticks
     */
    computeTerritoryChange(currentPct) {
        this.territoryHistory.push(currentPct);
        if (this.territoryHistory.length > 10) {
            this.territoryHistory.shift();
        }
        if (this.territoryHistory.length < 2)
            return 0;
        const oldPct = this.territoryHistory[0];
        return currentPct - oldPct;
    }
    /**
     * Detect disconnected territory clusters using flood fill.
     * Returns up to 5 largest clusters sorted by size.
     */
    detectTerritoryClusters() {
        if (!this.game || !this.rlPlayer) {
            return [];
        }
        const allTiles = Array.from(this.rlPlayer.tiles());
        const visited = new Set();
        const clusters = [];
        // Find all connected components
        for (const startTile of allTiles) {
            if (visited.has(startTile))
                continue;
            const cluster = this.floodFillCluster(startTile, allTiles, visited);
            if (cluster.tiles.length > 0) {
                clusters.push(cluster);
            }
        }
        // Sort by size (largest first) and keep top 5
        clusters.sort((a, b) => b.tiles.length - a.tiles.length);
        const topClusters = clusters.slice(0, 5);
        // Assign IDs
        topClusters.forEach((cluster, idx) => {
            cluster.id = idx;
        });
        return topClusters;
    }
    /**
     * Flood fill to find a connected territory cluster.
     */
    floodFillCluster(startTile, allTiles, visited) {
        const allTilesSet = new Set(allTiles);
        const queue = [startTile];
        visited.add(startTile);
        const clusterTiles = [];
        const borderTilesSet = new Set();
        let sumX = 0;
        let sumY = 0;
        while (queue.length > 0) {
            const tile = queue.shift();
            clusterTiles.push(tile);
            const x = this.game.x(tile);
            const y = this.game.y(tile);
            sumX += x;
            sumY += y;
            // Check if this is a border tile
            if (this.isBorderTile(tile)) {
                borderTilesSet.add(tile);
            }
            // Add 4-connected neighbors
            const neighbors = [
                { dx: 0, dy: -1 },
                { dx: 1, dy: 0 },
                { dx: 0, dy: 1 },
                { dx: -1, dy: 0 }
            ];
            for (const { dx, dy } of neighbors) {
                const nx = x + dx;
                const ny = y + dy;
                if (nx >= 0 && nx < this.mapWidth && ny >= 0 && ny < this.mapHeight) {
                    const neighborTile = this.game.ref(nx, ny);
                    if (allTilesSet.has(neighborTile) && !visited.has(neighborTile)) {
                        visited.add(neighborTile);
                        queue.push(neighborTile);
                    }
                }
            }
        }
        // Compute center
        const centerX = clusterTiles.length > 0 ? sumX / clusterTiles.length : 0;
        const centerY = clusterTiles.length > 0 ? sumY / clusterTiles.length : 0;
        // Estimate troop count (proportional to cluster size)
        const totalTiles = allTiles.length;
        const totalTroops = this.rlPlayer.troops();
        const troopCount = totalTiles > 0 ? Math.floor((totalTroops * clusterTiles.length) / totalTiles) : 0;
        return {
            id: -1, // Will be assigned later
            tiles: clusterTiles,
            border_tiles: Array.from(borderTilesSet),
            center_x: centerX,
            center_y: centerY,
            troop_count: troopCount
        };
    }
    /**
     * Check if a tile is on the border of our territory.
     */
    isBorderTile(tile) {
        if (!this.game || !this.rlPlayer)
            return false;
        const x = this.game.x(tile);
        const y = this.game.y(tile);
        const neighbors = [
            { dx: 0, dy: -1 },
            { dx: 1, dy: 0 },
            { dx: 0, dy: 1 },
            { dx: -1, dy: 0 }
        ];
        for (const { dx, dy } of neighbors) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < this.mapWidth && ny >= 0 && ny < this.mapHeight) {
                const neighborTile = this.game.ref(nx, ny);
                const owner = this.game.owner(neighborTile);
                // If neighbor is not ours, we're on a border
                if (!owner.isPlayer() || owner.id() !== this.rlPlayer.id()) {
                    return true;
                }
            }
        }
        return false;
    }
    log(message) {
        console.error(`[GameBridge] ${message}`);
    }
    close() {
        this.game = null;
        this.rlPlayer = null;
        this.aiPlayers = [];
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
    rl.on('line', async (line) => {
        try {
            const command = JSON.parse(line);
            let response = { success: true };
            switch (command.type) {
                case 'reset':
                    response.state = await bridge.initialize(command.map_name || 'plains', command.num_players || 11);
                    break;
                case 'tick':
                    response.state = bridge.tick();
                    break;
                case 'get_state':
                    response.state = bridge.getState();
                    break;
                case 'attack_direction':
                    response.success = bridge.attackDirection(command.direction || 8, command.intensity || 0.5, command.cluster_id || 0);
                    break;
                case 'shutdown':
                    bridge.close();
                    console.log(JSON.stringify(response));
                    process.exit(0);
                    break;
                default:
                    response.success = false;
                    response.error = `Unknown command type: ${command.type}`;
            }
            console.log(JSON.stringify(response));
        }
        catch (error) {
            console.log(JSON.stringify({
                success: false,
                error: error.message || String(error)
            }));
        }
    });
    rl.on('close', () => {
        bridge.close();
        process.exit(0);
    });
}
main().catch(error => {
    console.error('[GameBridge FATAL]', error);
    process.exit(1);
});
