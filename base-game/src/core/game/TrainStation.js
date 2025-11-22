import { PseudoRandom } from "../PseudoRandom";
import { UnitType } from "./Game";
import { GameUpdateType, RailType } from "./GameUpdates";
/**
 * All stop handlers share the same logic for the time being
 * Behavior to be defined
 */
class CityStopHandler {
    onStop(mg, station, trainExecution) {
        const stationOwner = station.unit.owner();
        const trainOwner = trainExecution.owner();
        const goldBonus = mg.config().trainGold(rel(trainOwner, stationOwner));
        // Share revenue with the station owner if it's not the current player
        if (trainOwner !== stationOwner) {
            stationOwner.addGold(goldBonus, station.tile());
        }
        trainOwner.addGold(goldBonus, station.tile());
    }
}
class PortStopHandler {
    constructor(random) {
        this.random = random;
    }
    onStop(mg, station, trainExecution) {
        const stationOwner = station.unit.owner();
        const trainOwner = trainExecution.owner();
        const goldBonus = mg.config().trainGold(rel(trainOwner, stationOwner));
        trainOwner.addGold(goldBonus, station.tile());
        // Share revenue with the station owner if it's not the current player
        if (trainOwner !== stationOwner) {
            stationOwner.addGold(goldBonus, station.tile());
        }
    }
}
class FactoryStopHandler {
    onStop(mg, station, trainExecution) { }
}
export function createTrainStopHandlers(random) {
    return {
        [UnitType.City]: new CityStopHandler(),
        [UnitType.Port]: new PortStopHandler(random),
        [UnitType.Factory]: new FactoryStopHandler(),
    };
}
export class TrainStation {
    constructor(mg, unit) {
        this.mg = mg;
        this.unit = unit;
        this.stopHandlers = {};
        this.railroads = new Set();
        this.stopHandlers = createTrainStopHandlers(new PseudoRandom(mg.ticks()));
    }
    tradeAvailable(otherPlayer) {
        const player = this.unit.owner();
        return otherPlayer === player || player.canTrade(otherPlayer);
    }
    clearRailroads() {
        this.railroads.clear();
    }
    addRailroad(railRoad) {
        this.railroads.add(railRoad);
    }
    removeNeighboringRails(station) {
        const toRemove = [...this.railroads].find((r) => r.from === station || r.to === station);
        if (toRemove) {
            const railTiles = toRemove.tiles.map((tile) => ({
                tile,
                railType: RailType.VERTICAL,
            }));
            this.mg.addUpdate({
                type: GameUpdateType.RailroadEvent,
                isActive: false,
                railTiles,
            });
            this.railroads.delete(toRemove);
        }
    }
    neighbors() {
        const neighbors = [];
        for (const r of this.railroads) {
            if (r.from !== this) {
                neighbors.push(r.from);
            }
            else {
                neighbors.push(r.to);
            }
        }
        return neighbors;
    }
    tile() {
        return this.unit.tile();
    }
    isActive() {
        return this.unit.isActive();
    }
    getRailroads() {
        return this.railroads;
    }
    setCluster(cluster) {
        this.cluster = cluster;
    }
    getCluster() {
        return this.cluster;
    }
    onTrainStop(trainExecution) {
        const type = this.unit.type();
        const handler = this.stopHandlers[type];
        if (handler) {
            handler.onStop(this.mg, this, trainExecution);
        }
    }
}
/**
 * Make the trainstation usable with A*
 */
export class TrainStationMapAdapter {
    constructor(game) {
        this.game = game;
    }
    neighbors(node) {
        return node.neighbors();
    }
    cost(node) {
        return 1;
    }
    position(node) {
        return { x: this.game.x(node.tile()), y: this.game.y(node.tile()) };
    }
    isTraversable(from, to) {
        return true;
    }
}
/**
 * Cluster of connected stations
 */
export class Cluster {
    constructor() {
        this.stations = new Set();
    }
    has(station) {
        return this.stations.has(station);
    }
    addStation(station) {
        this.stations.add(station);
        station.setCluster(this);
    }
    removeStation(station) {
        this.stations.delete(station);
    }
    addStations(stations) {
        for (const station of stations) {
            this.addStation(station);
        }
    }
    merge(other) {
        for (const s of other.stations) {
            this.addStation(s);
        }
    }
    availableForTrade(player) {
        const tradingStations = new Set();
        for (const station of this.stations) {
            if ((station.unit.type() === UnitType.City ||
                station.unit.type() === UnitType.Port) &&
                station.tradeAvailable(player)) {
                tradingStations.add(station);
            }
        }
        return tradingStations;
    }
    size() {
        return this.stations.size;
    }
    clear() {
        this.stations.clear();
    }
}
function rel(player, other) {
    if (player === other) {
        return "self";
    }
    if (player.isOnSameTeam(other)) {
        return "team";
    }
    if (player.isAlliedWith(other)) {
        return "ally";
    }
    return "other";
}
