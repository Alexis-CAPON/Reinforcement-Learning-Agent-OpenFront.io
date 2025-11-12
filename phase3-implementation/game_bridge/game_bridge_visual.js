/**
 * Visual Game Bridge for Phase 3 - Battle Royale
 *
 * Extends the regular game bridge with full visual state export
 * for HTML Canvas rendering.
 */
import * as readline from 'readline';
import { setup } from '../../base-game/tests/util/Setup';
import { PlayerType, PlayerInfo } from '../../base-game/src/core/game/Game';
import { AttackExecution } from '../../base-game/src/core/execution/AttackExecution';
import { SpawnExecution } from '../../base-game/src/core/execution/SpawnExecution';
import * as path from 'path';
import { dirname } from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
class VisualGameBridge {
    game = null;
    rlPlayer = null;
    aiPlayers = [];
    currentTick = 0;
    maxTicks = 10000;
    // Color palette for players (40 colors)
    PLAYER_COLORS = [
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
    log(message) {
        console.error(`[VisualBridge] ${message}`);
    }
    async initialize(numBots, mapName = 'plains') {
        this.log(`Initializing battle royale: map=${mapName}, bots=${numBots}`);
        const numPlayers = numBots + 1; // RL agent + bots
        // Create players
        const players = [new PlayerInfo('RL_Agent', PlayerType.Human, null, 'RL_Agent')];
        for (let i = 1; i <= numBots; i++) {
            players.push(new PlayerInfo(`AI_Bot_${i}`, PlayerType.Bot, null, `AI_Bot_${i}`));
        }
        this.log(`Creating game with ${numPlayers} players...`);
        // Setup game
        this.game = await setup(mapName, {
            gameMode: 'Free For All',
            gameType: 'Singleplayer',
            difficulty: 'Easy',
            infiniteGold: false,
            infiniteTroops: false,
            instantBuild: false,
        }, players, path.join(__dirname, '../../base-game/tests/util'));
        if (!this.game) {
            throw new Error('setup() returned null');
        }
        this.log(`Game created, spawning ${numPlayers} players...`);
        // Spawn players distributed around the map
        const width = this.game.width();
        const height = this.game.height();
        const spawnExecutions = [];
        const angleOffset = Math.random() * 2 * Math.PI;
        for (let i = 0; i < numPlayers; i++) {
            const angle = (i / numPlayers) * 2 * Math.PI + angleOffset;
            const baseX = Math.floor(width / 2 + (width / 2 - 20) * Math.cos(angle));
            const baseY = Math.floor(height / 2 + (height / 2 - 20) * Math.sin(angle));
            const x = Math.max(10, Math.min(width - 10, baseX + Math.floor((Math.random() - 0.5) * 15)));
            const y = Math.max(10, Math.min(height - 10, baseY + Math.floor((Math.random() - 0.5) * 15)));
            const spawnPos = this.game.ref(x, y);
            const playerName = i === 0 ? 'RL_Agent' : `AI_Bot_${i}`;
            const playerType = i === 0 ? PlayerType.Human : PlayerType.Bot;
            spawnExecutions.push(new SpawnExecution(new PlayerInfo(playerName, playerType, null, playerName), spawnPos));
        }
        this.game.addExecution(...spawnExecutions);
        // Execute spawn phase
        this.log(`Executing spawn phase...`);
        while (this.game.inSpawnPhase()) {
            this.game.executeNextTick();
        }
        this.log(`Spawn phase complete`);
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
    tick() {
        if (!this.game)
            throw new Error('Game not initialized');
        this.game.executeNextTick();
        this.currentTick++;
        return this.getVisualState();
    }
    getVisualState() {
        if (!this.game || !this.rlPlayer) {
            throw new Error('Game not initialized');
        }
        const width = this.game.width();
        const height = this.game.height();
        const allPlayers = [this.rlPlayer, ...this.aiPlayers];
        // Calculate ranks (by tiles owned)
        const playersByTiles = [...allPlayers]
            .filter(p => p.isAlive())
            .sort((a, b) => b.numTilesOwned() - a.numTilesOwned());
        const playerRanks = new Map();
        playersByTiles.forEach((player, index) => {
            playerRanks.set(player.id(), index + 1);
        });
        // Dead players get worst rank
        allPlayers.filter(p => !p.isAlive()).forEach(player => {
            playerRanks.set(player.id(), allPlayers.length + 1);
        });
        // Build city positions map
        const cityPositions = new Set();
        allPlayers.forEach(player => {
            player.units().filter(u => u.type() === 'City').forEach(city => {
                const cityX = this.game.x(city.tile());
                const cityY = this.game.y(city.tile());
                cityPositions.add(`${cityX},${cityY}`);
            });
        });
        // Build player ID mapping (RL = 1, AI bots = 2+)
        const playerIdMap = new Map();
        playerIdMap.set(this.rlPlayer.id(), 1);
        this.aiPlayers.forEach((ai, index) => {
            playerIdMap.set(ai.id(), index + 2);
        });
        // Extract ALL tiles
        const tiles = [];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const tileRef = this.game.ref(x, y);
                const owner = this.game.owner(tileRef);
                // Determine owner_id
                let owner_id = 0;
                if (owner.isPlayer()) {
                    const ownerPlayer = owner;
                    owner_id = playerIdMap.get(ownerPlayer.id()) || 0;
                }
                const terrainType = this.game.terrainType(tileRef);
                const is_mountain = terrainType === 2;
                const is_city = cityPositions.has(`${x},${y}`);
                tiles.push({
                    x,
                    y,
                    owner_id,
                    troops: 0, // Troops are per-player, not per-tile
                    is_city,
                    is_mountain
                });
            }
        }
        // Extract player states
        const players = allPlayers.map((player, idx) => ({
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
        let winner_id = null;
        let game_over = false;
        if (alivePlayers.length === 1) {
            winner_id = playerIdMap.get(alivePlayers[0].id()) || null;
            game_over = true;
        }
        else if (!this.rlPlayer.isAlive()) {
            game_over = true;
        }
        else if (this.currentTick >= this.maxTicks) {
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
    attackDirection(direction, intensity, build) {
        if (!this.game || !this.rlPlayer) {
            throw new Error('Game not initialized');
        }
        // Find attackable target (use ANY valid target, direction is just a hint)
        if (direction !== 'WAIT') {
            const currentTroops = this.rlPlayer.troops();
            const attackTroops = Math.floor(currentTroops * intensity);
            if (attackTroops >= 1) {
                // Get all attackable neighbors (game API provides this)
                const borderTiles = Array.from(this.rlPlayer.borderTiles());
                // Find ANY valid attack target
                for (const borderTile of borderTiles) {
                    const x = this.game.x(borderTile);
                    const y = this.game.y(borderTile);
                    // Check all 4 directions for attackable tiles
                    const offsets = [
                        { dx: 0, dy: -1 }, // N
                        { dx: 1, dy: 0 }, // E
                        { dx: 0, dy: 1 }, // S
                        { dx: -1, dy: 0 } // W
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
                        if (!owner.isPlayer() || owner.id() !== this.rlPlayer.id()) {
                            if (this.rlPlayer.canAttack(targetTile)) {
                                // Found a valid target! Attack it!
                                const targetId = owner.isPlayer()
                                    ? owner.id()
                                    : this.game.terraNullius().id();
                                // FIXED: Use correct AttackExecution constructor (matching phase1-2)
                                // Constructor: (startTroops, _owner, _targetID, sourceTile?, removeTroops?)
                                const attack = new AttackExecution(attackTroops, // startTroops
                                this.rlPlayer, // _owner (Player object, not ID!)
                                targetId // _targetID
                                );
                                this.game.addExecution(attack);
                                this.log(`Attack added: ${attackTroops} troops (${(intensity * 100).toFixed(0)}% of ${currentTroops}) to (${targetX},${targetY})`);
                                return; // Attack added, done!
                            }
                        }
                    }
                }
                this.log(`No valid attack targets found (border tiles: ${borderTiles.length})`);
            }
            else {
                this.log(`Attack too small: ${attackTroops} troops (${(intensity * 100).toFixed(0)}% of ${currentTroops})`);
            }
        }
        // Build city (if requested and possible)
        if (build) {
            // Build on a random interior tile
            const ownedTiles = Array.from(this.rlPlayer.tiles());
            const borderTiles = new Set(this.rlPlayer.borderTiles());
            const interiorTiles = ownedTiles.filter(t => !borderTiles.has(t));
            if (interiorTiles.length > 0 && this.rlPlayer.gold() >= 1000) {
                const buildTile = interiorTiles[Math.floor(Math.random() * interiorTiles.length)];
                // City building would be handled by game logic automatically
                // (This is a simplified version - actual implementation may vary)
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
    rl.on('line', async (line) => {
        try {
            const command = JSON.parse(line);
            let response;
            switch (command.type) {
                case 'reset': {
                    const numBots = command.num_bots || 10;
                    const mapName = command.map_name || 'plains';
                    const state = await bridge.initialize(numBots, mapName);
                    response = { type: 'visual_state', state, success: true };
                    break;
                }
                case 'tick': {
                    const state = bridge.tick();
                    response = { type: 'visual_state', state, success: true };
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
                    const build = command.build || false;
                    bridge.attackDirection(direction, intensity, build);
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
        }
        catch (error) {
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
