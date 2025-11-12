"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RailNetworkImpl = exports.StationManagerImpl = void 0;
exports.createRailNetwork = createRailNetwork;
const RailroadExecution_1 = require("../execution/RailroadExecution");
const AStar_1 = require("../pathfinding/AStar");
const MiniAStar_1 = require("../pathfinding/MiniAStar");
const SerialAStar_1 = require("../pathfinding/SerialAStar");
const Game_1 = require("./Game");
const Railroad_1 = require("./Railroad");
const TrainStation_1 = require("./TrainStation");
class StationManagerImpl {
    constructor() {
        this.stations = new Set();
    }
    addStation(station) {
        this.stations.add(station);
    }
    removeStation(station) {
        this.stations.delete(station);
    }
    findStation(unit) {
        for (const station of this.stations) {
            if (station.unit === unit)
                return station;
        }
        return null;
    }
    getAll() {
        return this.stations;
    }
}
exports.StationManagerImpl = StationManagerImpl;
class RailPathFinderServiceImpl {
    constructor(game) {
        this.game = game;
    }
    findTilePath(from, to) {
        const astar = new MiniAStar_1.MiniAStar(this.game.map(), this.game.miniMap(), from, to, 5000, 20, false, 3);
        return astar.compute() === AStar_1.PathFindResultType.Completed
            ? astar.reconstructPath()
            : [];
    }
    findStationsPath(from, to) {
        const stationAStar = new SerialAStar_1.SerialAStar(from, to, 5000, 20, new TrainStation_1.TrainStationMapAdapter(this.game));
        return stationAStar.compute() === AStar_1.PathFindResultType.Completed
            ? stationAStar.reconstructPath()
            : [];
    }
}
function createRailNetwork(game) {
    const stationManager = new StationManagerImpl();
    const pathService = new RailPathFinderServiceImpl(game);
    return new RailNetworkImpl(game, stationManager, pathService);
}
class RailNetworkImpl {
    constructor(game, stationManager, pathService) {
        this.game = game;
        this.stationManager = stationManager;
        this.pathService = pathService;
        this.maxConnectionDistance = 4;
    }
    connectStation(station) {
        this.stationManager.addStation(station);
        this.connectToNearbyStations(station);
    }
    removeStation(unit) {
        const station = this.stationManager.findStation(unit);
        if (!station)
            return;
        const neighbors = station.neighbors();
        this.disconnectFromNetwork(station);
        this.stationManager.removeStation(station);
        const cluster = station.getCluster();
        if (!cluster)
            return;
        if (neighbors.length === 1) {
            cluster.removeStation(station);
        }
        else if (neighbors.length > 1) {
            for (const neighbor of neighbors) {
                const stations = this.computeCluster(neighbor);
                const newCluster = new TrainStation_1.Cluster();
                newCluster.addStations(stations);
            }
        }
        station.unit.setTrainStation(false);
    }
    /**
     * Return the intermediary stations connecting two stations
     */
    findStationsPath(from, to) {
        return this.pathService.findStationsPath(from, to);
    }
    connectToNearbyStations(station) {
        const neighbors = this.game.nearbyUnits(station.tile(), this.game.config().trainStationMaxRange(), [Game_1.UnitType.City, Game_1.UnitType.Factory, Game_1.UnitType.Port]);
        const editedClusters = new Set();
        neighbors.sort((a, b) => a.distSquared - b.distSquared);
        for (const neighbor of neighbors) {
            if (neighbor.unit === station.unit)
                continue;
            const neighborStation = this.stationManager.findStation(neighbor.unit);
            if (!neighborStation)
                continue;
            const distanceToStation = this.distanceFrom(neighborStation, station, this.maxConnectionDistance);
            const neighborCluster = neighborStation.getCluster();
            if (neighborCluster === null)
                continue;
            const connectionAvailable = distanceToStation > this.maxConnectionDistance ||
                distanceToStation === -1;
            if (connectionAvailable &&
                neighbor.distSquared > Math.pow(this.game.config().trainStationMinRange(), 2)) {
                if (this.connect(station, neighborStation)) {
                    neighborCluster.addStation(station);
                    editedClusters.add(neighborCluster);
                }
            }
        }
        // If multiple clusters own the new station, merge them into a single cluster
        if (editedClusters.size > 1) {
            this.mergeClusters(editedClusters);
        }
        else if (editedClusters.size === 0) {
            // If no cluster owns the station, creates a new one for it
            const newCluster = new TrainStation_1.Cluster();
            newCluster.addStation(station);
        }
    }
    disconnectFromNetwork(station) {
        for (const rail of station.getRailroads()) {
            rail.delete(this.game);
        }
        station.clearRailroads();
        const cluster = station.getCluster();
        if (cluster !== null && cluster.size() === 1) {
            this.deleteCluster(cluster);
        }
    }
    deleteCluster(cluster) {
        for (const station of cluster.stations) {
            station.setCluster(null);
        }
        cluster.clear();
    }
    connect(from, to) {
        const path = this.pathService.findTilePath(from.tile(), to.tile());
        if (path.length > 0 && path.length < this.game.config().railroadMaxSize()) {
            const railRoad = new Railroad_1.Railroad(from, to, path);
            this.game.addExecution(new RailroadExecution_1.RailroadExecution(railRoad));
            from.addRailroad(railRoad);
            to.addRailroad(railRoad);
            return true;
        }
        return false;
    }
    distanceFrom(start, dest, maxDistance) {
        if (start === dest)
            return 0;
        const visited = new Set();
        const queue = [
            { station: start, distance: 0 },
        ];
        while (queue.length > 0) {
            const { station, distance } = queue.shift();
            if (visited.has(station))
                continue;
            visited.add(station);
            if (distance >= maxDistance)
                continue;
            for (const neighbor of station.neighbors()) {
                if (neighbor === dest)
                    return distance + 1;
                if (!visited.has(neighbor)) {
                    queue.push({ station: neighbor, distance: distance + 1 });
                }
            }
        }
        // If destination not found within maxDistance
        return -1;
    }
    computeCluster(start) {
        const visited = new Set();
        const queue = [start];
        while (queue.length > 0) {
            const current = queue.shift();
            if (visited.has(current))
                continue;
            visited.add(current);
            for (const neighbor of current.neighbors()) {
                if (!visited.has(neighbor))
                    queue.push(neighbor);
            }
        }
        return visited;
    }
    mergeClusters(clustersToMerge) {
        const merged = new TrainStation_1.Cluster();
        for (const cluster of clustersToMerge) {
            merged.merge(cluster);
        }
    }
}
exports.RailNetworkImpl = RailNetworkImpl;
