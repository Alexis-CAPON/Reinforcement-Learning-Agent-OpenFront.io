"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RailroadExecution = void 0;
const GameUpdates_1 = require("../game/GameUpdates");
class RailroadExecution {
    constructor(railRoad) {
        this.railRoad = railRoad;
        this.active = true;
        this.headIndex = 0;
        this.tailIndex = 0;
        this.increment = 3;
        this.railTiles = [];
        this.tailIndex = railRoad.tiles.length;
    }
    isActive() {
        return this.active;
    }
    init(mg, ticks) {
        this.mg = mg;
        const tiles = this.railRoad.tiles;
        // Inverse direction computation for the first tile
        this.railTiles.push({
            tile: tiles[0],
            railType: tiles.length > 0
                ? this.computeExtremityDirection(tiles[0], tiles[1])
                : GameUpdates_1.RailType.VERTICAL,
        });
        for (let i = 1; i < tiles.length - 1; i++) {
            const direction = this.computeDirection(tiles[i - 1], tiles[i], tiles[i + 1]);
            this.railTiles.push({ tile: tiles[i], railType: direction });
        }
        this.railTiles.push({
            tile: tiles[tiles.length - 1],
            railType: tiles.length > 0
                ? this.computeExtremityDirection(tiles[tiles.length - 1], tiles[tiles.length - 2])
                : GameUpdates_1.RailType.VERTICAL,
        });
    }
    computeExtremityDirection(tile, next) {
        const x = this.mg.x(tile);
        const y = this.mg.y(tile);
        const nextX = this.mg.x(next);
        const nextY = this.mg.y(next);
        const dx = nextX - x;
        const dy = nextY - y;
        if (dx === 0 && dy === 0)
            return GameUpdates_1.RailType.VERTICAL; // No movement
        if (dx === 0) {
            return GameUpdates_1.RailType.VERTICAL;
        }
        else if (dy === 0) {
            return GameUpdates_1.RailType.HORIZONTAL;
        }
        return GameUpdates_1.RailType.VERTICAL;
    }
    computeDirection(prev, current, next) {
        if (this.mg === null) {
            throw new Error("Not initialized");
        }
        const x1 = this.mg.x(prev);
        const y1 = this.mg.y(prev);
        const x2 = this.mg.x(current);
        const y2 = this.mg.y(current);
        const x3 = this.mg.x(next);
        const y3 = this.mg.y(next);
        const dx1 = x2 - x1;
        const dy1 = y2 - y1;
        const dx2 = x3 - x2;
        const dy2 = y3 - y2;
        // Straight line
        if (dx1 === dx2 && dy1 === dy2) {
            if (dx1 !== 0)
                return GameUpdates_1.RailType.HORIZONTAL;
            if (dy1 !== 0)
                return GameUpdates_1.RailType.VERTICAL;
        }
        // Turn (corner) cases
        if ((dx1 === 0 && dx2 !== 0) || (dx1 !== 0 && dx2 === 0)) {
            // Now figure out which type of corner
            if (dx1 === 0 && dx2 === 1 && dy1 === -1)
                return GameUpdates_1.RailType.BOTTOM_RIGHT;
            if (dx1 === 0 && dx2 === -1 && dy1 === -1)
                return GameUpdates_1.RailType.BOTTOM_LEFT;
            if (dx1 === 0 && dx2 === 1 && dy1 === 1)
                return GameUpdates_1.RailType.TOP_RIGHT;
            if (dx1 === 0 && dx2 === -1 && dy1 === 1)
                return GameUpdates_1.RailType.TOP_LEFT;
            if (dx1 === 1 && dx2 === 0 && dy2 === -1)
                return GameUpdates_1.RailType.TOP_LEFT;
            if (dx1 === -1 && dx2 === 0 && dy2 === -1)
                return GameUpdates_1.RailType.TOP_RIGHT;
            if (dx1 === 1 && dx2 === 0 && dy2 === 1)
                return GameUpdates_1.RailType.BOTTOM_LEFT;
            if (dx1 === -1 && dx2 === 0 && dy2 === 1)
                return GameUpdates_1.RailType.BOTTOM_RIGHT;
        }
        console.warn(`Invalid rail segment: ${dx1}:${dy1}, ${dx2}:${dy2}`);
        return GameUpdates_1.RailType.VERTICAL;
    }
    tick(ticks) {
        if (this.mg === null) {
            throw new Error("Not initialized");
        }
        if (!this.activeSourceOrDestination()) {
            this.active = false;
            return;
        }
        if (this.headIndex > this.tailIndex) {
            // Construction complete
            this.constructionComplete();
            return;
        }
        let updatedRailTiles;
        // Check if remaining tiles can be done all at once
        if (this.tailIndex - this.headIndex <= 2 * this.increment) {
            updatedRailTiles = this.railTiles.slice(this.headIndex, this.tailIndex);
            this.constructionComplete();
        }
        else {
            updatedRailTiles = this.railTiles.slice(this.headIndex, this.headIndex + this.increment);
            updatedRailTiles = updatedRailTiles.concat(this.railTiles.slice(this.tailIndex - this.increment, this.tailIndex));
            this.headIndex += this.increment;
            this.tailIndex -= this.increment;
        }
        if (updatedRailTiles) {
            this.mg.addUpdate({
                type: GameUpdates_1.GameUpdateType.RailroadEvent,
                isActive: true,
                railTiles: updatedRailTiles,
            });
        }
    }
    activeDuringSpawnPhase() {
        return false;
    }
    activeSourceOrDestination() {
        return this.railRoad.from.isActive() && this.railRoad.to.isActive();
    }
    constructionComplete() {
        this.redrawBuildings();
        this.active = false;
    }
    redrawBuildings() {
        this.railRoad.from.unit.isActive() && this.railRoad.from.unit.touch();
        this.railRoad.to.unit.isActive() && this.railRoad.to.unit.touch();
    }
}
exports.RailroadExecution = RailroadExecution;
