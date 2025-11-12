"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Cluster = exports.TrainStationMapAdapter = exports.TrainStation = void 0;
exports.createTrainStopHandlers = createTrainStopHandlers;
const PseudoRandom_1 = require("../PseudoRandom");
const Game_1 = require("./Game");
const GameUpdates_1 = require("./GameUpdates");
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
function createTrainStopHandlers(random) {
    return {
        [Game_1.UnitType.City]: new CityStopHandler(),
        [Game_1.UnitType.Port]: new PortStopHandler(random),
        [Game_1.UnitType.Factory]: new FactoryStopHandler(),
    };
}
class TrainStation {
    constructor(mg, unit) {
        this.mg = mg;
        this.unit = unit;
        this.stopHandlers = {};
        this.railroads = new Set();
        this.stopHandlers = createTrainStopHandlers(new PseudoRandom_1.PseudoRandom(mg.ticks()));
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
                railType: GameUpdates_1.RailType.VERTICAL,
            }));
            this.mg.addUpdate({
                type: GameUpdates_1.GameUpdateType.RailroadEvent,
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
exports.TrainStation = TrainStation;
/**
 * Make the trainstation usable with A*
 */
class TrainStationMapAdapter {
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
exports.TrainStationMapAdapter = TrainStationMapAdapter;
/**
 * Cluster of connected stations
 */
class Cluster {
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
            if ((station.unit.type() === Game_1.UnitType.City ||
                station.unit.type() === Game_1.UnitType.Port) &&
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
exports.Cluster = Cluster;
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
