"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GameMapImpl = void 0;
exports.euclDistFN = euclDistFN;
exports.manhattanDistFN = manhattanDistFN;
exports.rectDistFN = rectDistFN;
exports.isometricDistFN = isometricDistFN;
exports.hexDistFN = hexDistFN;
exports.andFN = andFN;
const Game_1 = require("./Game");
class GameMapImpl {
    // Bit 15 still reserved
    constructor(width, height, terrainData, numLandTiles_) {
        this.numLandTiles_ = numLandTiles_;
        this._numTilesWithFallout = 0;
        if (terrainData.length !== width * height) {
            throw new Error(`Terrain data length ${terrainData.length} doesn't match dimensions ${width}x${height}`);
        }
        this.width_ = width;
        this.height_ = height;
        this.terrain = terrainData;
        this.state = new Uint16Array(width * height);
        // Precompute the LUTs
        let ref = 0;
        this.refToX = new Array(width * height);
        this.refToY = new Array(width * height);
        this.yToRef = new Array(height);
        for (let y = 0; y < height; y++) {
            this.yToRef[y] = ref;
            for (let x = 0; x < width; x++) {
                this.refToX[ref] = x;
                this.refToY[ref] = y;
                ref++;
            }
        }
    }
    numTilesWithFallout() {
        return this._numTilesWithFallout;
    }
    ref(x, y) {
        if (!this.isValidCoord(x, y)) {
            throw new Error(`Invalid coordinates: ${x},${y}`);
        }
        return this.yToRef[y] + x;
    }
    isValidRef(ref) {
        return ref >= 0 && ref < this.refToX.length;
    }
    x(ref) {
        return this.refToX[ref];
    }
    y(ref) {
        return this.refToY[ref];
    }
    cell(ref) {
        return new Game_1.Cell(this.x(ref), this.y(ref));
    }
    width() {
        return this.width_;
    }
    height() {
        return this.height_;
    }
    numLandTiles() {
        return this.numLandTiles_;
    }
    isValidCoord(x, y) {
        return x >= 0 && x < this.width_ && y >= 0 && y < this.height_;
    }
    // Terrain getters (immutable)
    isLand(ref) {
        return Boolean(this.terrain[ref] & (1 << GameMapImpl.IS_LAND_BIT));
    }
    isOceanShore(ref) {
        return (this.isLand(ref) && this.neighbors(ref).some((tr) => this.isOcean(tr)));
    }
    isOcean(ref) {
        return Boolean(this.terrain[ref] & (1 << GameMapImpl.OCEAN_BIT));
    }
    isShoreline(ref) {
        return Boolean(this.terrain[ref] & (1 << GameMapImpl.SHORELINE_BIT));
    }
    magnitude(ref) {
        return this.terrain[ref] & GameMapImpl.MAGNITUDE_MASK;
    }
    // State getters and setters (mutable)
    ownerID(ref) {
        return this.state[ref] & GameMapImpl.PLAYER_ID_MASK;
    }
    hasOwner(ref) {
        return this.ownerID(ref) !== 0;
    }
    setOwnerID(ref, playerId) {
        if (playerId > GameMapImpl.PLAYER_ID_MASK) {
            throw new Error(`Player ID ${playerId} exceeds maximum value ${GameMapImpl.PLAYER_ID_MASK}`);
        }
        this.state[ref] =
            (this.state[ref] & ~GameMapImpl.PLAYER_ID_MASK) | playerId;
    }
    hasFallout(ref) {
        return Boolean(this.state[ref] & (1 << GameMapImpl.FALLOUT_BIT));
    }
    setFallout(ref, value) {
        const existingFallout = this.hasFallout(ref);
        if (value) {
            if (!existingFallout) {
                this._numTilesWithFallout++;
                this.state[ref] |= 1 << GameMapImpl.FALLOUT_BIT;
            }
        }
        else {
            if (existingFallout) {
                this._numTilesWithFallout--;
                this.state[ref] &= ~(1 << GameMapImpl.FALLOUT_BIT);
            }
        }
    }
    isOnEdgeOfMap(ref) {
        const x = this.x(ref);
        const y = this.y(ref);
        return (x === 0 || x === this.width() - 1 || y === 0 || y === this.height() - 1);
    }
    isBorder(ref) {
        return this.neighbors(ref).some((tr) => this.ownerID(tr) !== this.ownerID(ref));
    }
    hasDefenseBonus(ref) {
        return Boolean(this.state[ref] & (1 << GameMapImpl.DEFENSE_BONUS_BIT));
    }
    setDefenseBonus(ref, value) {
        if (value) {
            this.state[ref] |= 1 << GameMapImpl.DEFENSE_BONUS_BIT;
        }
        else {
            this.state[ref] &= ~(1 << GameMapImpl.DEFENSE_BONUS_BIT);
        }
    }
    // Helper methods
    isWater(ref) {
        return !this.isLand(ref);
    }
    isLake(ref) {
        return !this.isLand(ref) && !this.isOcean(ref);
    }
    isShore(ref) {
        return this.isLand(ref) && this.isShoreline(ref);
    }
    cost(ref) {
        return this.magnitude(ref) < 10 ? 2 : 1;
    }
    terrainType(ref) {
        if (this.isLand(ref)) {
            const magnitude = this.magnitude(ref);
            if (magnitude < 10)
                return Game_1.TerrainType.Plains;
            if (magnitude < 20)
                return Game_1.TerrainType.Highland;
            return Game_1.TerrainType.Mountain;
        }
        return this.isOcean(ref) ? Game_1.TerrainType.Ocean : Game_1.TerrainType.Lake;
    }
    neighbors(ref) {
        const neighbors = [];
        const w = this.width_;
        const x = this.refToX[ref];
        if (ref >= w)
            neighbors.push(ref - w);
        if (ref < (this.height_ - 1) * w)
            neighbors.push(ref + w);
        if (x !== 0)
            neighbors.push(ref - 1);
        if (x !== w - 1)
            neighbors.push(ref + 1);
        return neighbors;
    }
    forEachTile(fn) {
        for (let ref = 0; ref < this.width_ * this.height_; ref++) {
            fn(ref);
        }
    }
    manhattanDist(c1, c2) {
        return (Math.abs(this.x(c1) - this.x(c2)) + Math.abs(this.y(c1) - this.y(c2)));
    }
    euclideanDistSquared(c1, c2) {
        const x = this.x(c1) - this.x(c2);
        const y = this.y(c1) - this.y(c2);
        return x * x + y * y;
    }
    bfs(tile, filter) {
        const seen = new Set();
        const q = [];
        if (filter(this, tile)) {
            seen.add(tile);
            q.push(tile);
        }
        while (q.length > 0) {
            const curr = q.pop();
            if (curr === undefined)
                continue;
            for (const n of this.neighbors(curr)) {
                if (!seen.has(n) && filter(this, n)) {
                    seen.add(n);
                    q.push(n);
                }
            }
        }
        return seen;
    }
    toTileUpdate(tile) {
        // Pack the tile reference and state into a bigint
        // Format: [32 bits for tile reference][16 bits for state]
        return (BigInt(tile) << 16n) | BigInt(this.state[tile]);
    }
    updateTile(tu) {
        // Extract tile reference and state from the TileUpdate
        // Last 16 bits are state, rest is tile reference
        const tileRef = Number(tu >> 16n);
        const state = Number(tu & 0xffffn);
        const existingFallout = this.hasFallout(tileRef);
        this.state[tileRef] = state;
        const newFallout = this.hasFallout(tileRef);
        if (existingFallout && !newFallout) {
            this._numTilesWithFallout--;
        }
        if (!existingFallout && newFallout) {
            this._numTilesWithFallout++;
        }
        return tileRef;
    }
}
exports.GameMapImpl = GameMapImpl;
// Terrain bits (Uint8Array)
GameMapImpl.IS_LAND_BIT = 7;
GameMapImpl.SHORELINE_BIT = 6;
GameMapImpl.OCEAN_BIT = 5;
GameMapImpl.MAGNITUDE_MASK = 0x1f; // 11111 in binary
// State bits (Uint16Array)
GameMapImpl.PLAYER_ID_MASK = 0xfff;
GameMapImpl.FALLOUT_BIT = 13;
GameMapImpl.DEFENSE_BONUS_BIT = 14;
function euclDistFN(root, dist, center = false) {
    const dist2 = dist * dist;
    if (!center) {
        return (gm, n) => gm.euclideanDistSquared(root, n) <= dist2;
    }
    else {
        return (gm, n) => {
            // shifts the root tile’s coordinates by -0.5 so that its “center”
            // center becomes the corner of four pixels rather than the middle of one pixel.
            // just makes things based off even pixels instead of odd. Used to use 9x9 icons now 10x10 icons etc...
            const rootX = gm.x(root) - 0.5;
            const rootY = gm.y(root) - 0.5;
            const dx = gm.x(n) - rootX;
            const dy = gm.y(n) - rootY;
            return dx * dx + dy * dy <= dist2;
        };
    }
}
function manhattanDistFN(root, dist, center = false) {
    if (!center) {
        return (gm, n) => gm.manhattanDist(root, n) <= dist;
    }
    else {
        return (gm, n) => {
            const rootX = gm.x(root) - 0.5;
            const rootY = gm.y(root) - 0.5;
            const dx = Math.abs(gm.x(n) - rootX);
            const dy = Math.abs(gm.y(n) - rootY);
            return dx + dy <= dist;
        };
    }
}
function rectDistFN(root, dist, center = false) {
    if (!center) {
        return (gm, n) => {
            const dx = Math.abs(gm.x(n) - gm.x(root));
            const dy = Math.abs(gm.y(n) - gm.y(root));
            return dx <= dist && dy <= dist;
        };
    }
    else {
        return (gm, n) => {
            const rootX = gm.x(root) - 0.5;
            const rootY = gm.y(root) - 0.5;
            const dx = Math.abs(gm.x(n) - rootX);
            const dy = Math.abs(gm.y(n) - rootY);
            return dx <= dist && dy <= dist;
        };
    }
}
function isInIsometricTile(center, tile, yOffset, distance) {
    const dx = Math.abs(tile.x - center.x);
    const dy = Math.abs(tile.y - (center.y + yOffset));
    return dx + dy * 2 <= distance + 1;
}
function isometricDistFN(root, dist, center = false) {
    if (!center) {
        return (gm, n) => gm.manhattanDist(root, n) <= dist;
    }
    else {
        return (gm, n) => {
            const rootX = gm.x(root) - 0.5;
            const rootY = gm.y(root) - 0.5;
            return isInIsometricTile({ x: rootX, y: rootY }, { x: gm.x(n), y: gm.y(n) }, 0, dist);
        };
    }
}
function hexDistFN(root, dist, center = false) {
    if (!center) {
        return (gm, n) => {
            const dx = Math.abs(gm.x(n) - gm.x(root));
            const dy = Math.abs(gm.y(n) - gm.y(root));
            return dx <= dist && dy <= dist && dx + dy <= dist * 1.5;
        };
    }
    else {
        return (gm, n) => {
            const rootX = gm.x(root) - 0.5;
            const rootY = gm.y(root) - 0.5;
            const dx = Math.abs(gm.x(n) - rootX);
            const dy = Math.abs(gm.y(n) - rootY);
            return dx <= dist && dy <= dist && dx + dy <= dist * 1.5;
        };
    }
}
function andFN(x, y) {
    return (gm, tile) => x(gm, tile) && y(gm, tile);
}
