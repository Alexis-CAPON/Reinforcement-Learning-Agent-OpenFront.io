import { UnitType } from "../game/Game";
import { calculateBoundingBox, getMode, inscribed, simpleHash } from "../Util";
export class PlayerExecution {
    constructor(player) {
        this.player = player;
        this.ticksPerClusterCalc = 20;
        this.lastCalc = 0;
        this.active = true;
    }
    activeDuringSpawnPhase() {
        return false;
    }
    init(mg, ticks) {
        this.mg = mg;
        this.config = mg.config();
        this.lastCalc =
            ticks + (simpleHash(this.player.name()) % this.ticksPerClusterCalc);
    }
    tick(ticks) {
        this.player.decayRelations();
        this.player.units().forEach((u) => {
            const tileOwner = this.mg.owner(u.tile());
            if (u.info().territoryBound) {
                if (tileOwner.isPlayer()) {
                    if (tileOwner !== this.player) {
                        this.mg.player(tileOwner.id()).captureUnit(u);
                    }
                }
                else {
                    u.delete();
                }
            }
        });
        if (!this.player.isAlive()) {
            // Player has no tiles, delete any remaining units and gold
            const gold = this.player.gold();
            this.player.removeGold(gold);
            this.player.units().forEach((u) => {
                if (u.type() !== UnitType.AtomBomb &&
                    u.type() !== UnitType.HydrogenBomb &&
                    u.type() !== UnitType.MIRVWarhead &&
                    u.type() !== UnitType.MIRV) {
                    u.delete();
                }
            });
            this.active = false;
            return;
        }
        const troopInc = this.config.troopIncreaseRate(this.player);
        this.player.addTroops(troopInc);
        const goldFromWorkers = this.config.goldAdditionRate(this.player);
        this.player.addGold(goldFromWorkers);
        // Record stats
        this.mg.stats().goldWork(this.player, goldFromWorkers);
        const alliances = Array.from(this.player.alliances());
        for (const alliance of alliances) {
            if (alliance.expiresAt() <= this.mg.ticks()) {
                alliance.expire();
            }
        }
        const embargoes = this.player.getEmbargoes();
        for (const embargo of embargoes) {
            if (embargo.isTemporary &&
                this.mg.ticks() - embargo.createdAt >
                    this.mg.config().temporaryEmbargoDuration()) {
                this.player.stopEmbargo(embargo.target);
            }
        }
        if (ticks - this.lastCalc > this.ticksPerClusterCalc) {
            if (this.player.lastTileChange() > this.lastCalc) {
                this.lastCalc = ticks;
                const start = performance.now();
                this.removeClusters();
                const end = performance.now();
                if (end - start > 1000) {
                    console.log(`player ${this.player.name()}, took ${end - start}ms`);
                }
            }
        }
    }
    removeClusters() {
        const clusters = this.calculateClusters();
        clusters.sort((a, b) => b.size - a.size);
        const main = clusters.shift();
        if (main === undefined)
            throw new Error("No clusters");
        this.player.largestClusterBoundingBox = calculateBoundingBox(this.mg, main);
        const surroundedBy = this.surroundedBySamePlayer(main);
        if (surroundedBy && !this.player.isFriendly(surroundedBy)) {
            this.removeCluster(main);
        }
        for (const cluster of clusters) {
            if (this.isSurrounded(cluster)) {
                this.removeCluster(cluster);
            }
        }
    }
    surroundedBySamePlayer(cluster) {
        const enemies = new Set();
        for (const tile of cluster) {
            const isOceanShore = this.mg.isOceanShore(tile);
            if (this.mg.isOceanShore(tile) && !isOceanShore) {
                continue;
            }
            if (isOceanShore ||
                this.mg.isOnEdgeOfMap(tile) ||
                this.mg.neighbors(tile).some((n) => !this.mg?.hasOwner(n))) {
                return false;
            }
            this.mg
                .neighbors(tile)
                .filter((n) => this.mg?.ownerID(n) !== this.player?.smallID())
                .forEach((p) => this.mg && enemies.add(this.mg.ownerID(p)));
            if (enemies.size !== 1) {
                return false;
            }
        }
        if (enemies.size !== 1) {
            return false;
        }
        const enemy = this.mg.playerBySmallID(Array.from(enemies)[0]);
        const enemyBox = calculateBoundingBox(this.mg, enemy.borderTiles());
        const clusterBox = calculateBoundingBox(this.mg, cluster);
        if (inscribed(enemyBox, clusterBox)) {
            return enemy;
        }
        return false;
    }
    isSurrounded(cluster) {
        const enemyTiles = new Set();
        for (const tr of cluster) {
            if (this.mg.isShore(tr) || this.mg.isOnEdgeOfMap(tr)) {
                return false;
            }
            this.mg
                .neighbors(tr)
                .filter((n) => this.mg?.owner(n).isPlayer() &&
                this.mg?.ownerID(n) !== this.player?.smallID())
                .forEach((n) => enemyTiles.add(n));
        }
        if (enemyTiles.size === 0) {
            return false;
        }
        const enemyBox = calculateBoundingBox(this.mg, enemyTiles);
        const clusterBox = calculateBoundingBox(this.mg, cluster);
        return inscribed(enemyBox, clusterBox);
    }
    removeCluster(cluster) {
        if (Array.from(cluster).some((t) => this.mg?.ownerID(t) !== this.player?.smallID())) {
            // Other removeCluster operations could change tile owners,
            // so double check.
            return;
        }
        const capturing = this.getCapturingPlayer(cluster);
        if (capturing === null) {
            return;
        }
        const firstTile = cluster.values().next().value;
        if (!firstTile) {
            return;
        }
        const filter = (_, t) => this.mg?.ownerID(t) === this.player?.smallID();
        const tiles = this.mg.bfs(firstTile, filter);
        if (this.player.numTilesOwned() === tiles.size) {
            this.mg.conquerPlayer(capturing, this.player);
        }
        for (const tile of tiles) {
            capturing.conquer(tile);
        }
    }
    getCapturingPlayer(cluster) {
        const neighborsIDs = new Set();
        for (const t of cluster) {
            for (const neighbor of this.mg.neighbors(t)) {
                if (this.mg.ownerID(neighbor) !== this.player.smallID()) {
                    neighborsIDs.add(this.mg.ownerID(neighbor));
                }
            }
        }
        let largestNeighborAttack = null;
        let largestTroopCount = 0;
        for (const id of neighborsIDs) {
            const neighbor = this.mg.playerBySmallID(id);
            if (!neighbor.isPlayer() || this.player.isFriendly(neighbor)) {
                continue;
            }
            for (const attack of neighbor.outgoingAttacks()) {
                if (attack.target() === this.player) {
                    if (attack.troops() > largestTroopCount) {
                        largestTroopCount = attack.troops();
                        largestNeighborAttack = neighbor;
                    }
                }
            }
        }
        if (largestNeighborAttack !== null) {
            return largestNeighborAttack;
        }
        // fall back to getting mode if no attacks
        const mode = getMode(neighborsIDs);
        if (!this.mg.playerBySmallID(mode).isPlayer()) {
            return null;
        }
        const capturing = this.mg.playerBySmallID(mode);
        if (!capturing.isPlayer()) {
            return null;
        }
        return capturing;
    }
    calculateClusters() {
        const seen = new Set();
        const border = this.player.borderTiles();
        const clusters = [];
        for (const tile of border) {
            if (seen.has(tile)) {
                continue;
            }
            const cluster = new Set();
            const queue = [tile];
            seen.add(tile);
            while (queue.length > 0) {
                const curr = queue.shift();
                if (curr === undefined)
                    throw new Error("curr is undefined");
                cluster.add(curr);
                const neighbors = this.mg.neighborsWithDiag(curr);
                for (const neighbor of neighbors) {
                    if (border.has(neighbor) && !seen.has(neighbor)) {
                        queue.push(neighbor);
                        seen.add(neighbor);
                    }
                }
            }
            clusters.push(cluster);
        }
        return clusters;
    }
    owner() {
        if (this.player === null) {
            throw new Error("Not initialized");
        }
        return this.player;
    }
    isActive() {
        return this.active;
    }
}
