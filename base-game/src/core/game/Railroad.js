import { GameUpdateType, RailType } from "./GameUpdates";
export class Railroad {
    constructor(from, to, tiles) {
        this.from = from;
        this.to = to;
        this.tiles = tiles;
    }
    delete(game) {
        const railTiles = this.tiles.map((tile) => ({
            tile,
            railType: RailType.VERTICAL,
        }));
        game.addUpdate({
            type: GameUpdateType.RailroadEvent,
            isActive: false,
            railTiles,
        });
        this.from.getRailroads().delete(this);
        this.to.getRailroads().delete(this);
    }
}
export function getOrientedRailroad(from, to) {
    for (const railroad of from.getRailroads()) {
        if (railroad.from === to) {
            return new OrientedRailroad(railroad, false);
        }
        else if (railroad.to === to) {
            return new OrientedRailroad(railroad, true);
        }
    }
    return null;
}
/**
 * Wrap a railroad with a direction so it always starts at tiles[0]
 */
export class OrientedRailroad {
    constructor(railroad, forward) {
        this.railroad = railroad;
        this.forward = forward;
        this.tiles = [];
        this.tiles = this.forward
            ? this.railroad.tiles
            : [...this.railroad.tiles].reverse();
    }
    getTiles() {
        return this.tiles;
    }
    getStart() {
        return this.forward ? this.railroad.from : this.railroad.to;
    }
    getEnd() {
        return this.forward ? this.railroad.to : this.railroad.from;
    }
}
