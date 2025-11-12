"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrainExecution = void 0;
const Game_1 = require("../game/Game");
const Railroad_1 = require("../game/Railroad");
class TrainExecution {
    constructor(railNetwork, player, source, destination, numCars) {
        this.railNetwork = railNetwork;
        this.player = player;
        this.source = source;
        this.destination = destination;
        this.numCars = numCars;
        this.active = true;
        this.mg = null;
        this.train = null;
        this.cars = [];
        this.hasCargo = false;
        this.currentTile = 0;
        this.spacing = 2;
        this.usedTiles = []; // used for cars behind
        this.stations = [];
        this.currentRailroad = null;
        this.speed = 2;
    }
    owner() {
        return this.player;
    }
    init(mg, ticks) {
        this.mg = mg;
        const stations = this.railNetwork.findStationsPath(this.source, this.destination);
        if (!stations || stations.length <= 1) {
            this.active = false;
            return;
        }
        this.stations = stations;
        const railroad = (0, Railroad_1.getOrientedRailroad)(this.stations[0], this.stations[1]);
        if (railroad) {
            this.currentRailroad = railroad;
        }
        else {
            this.active = false;
            return;
        }
        const spawn = this.player.canBuild(Game_1.UnitType.Train, this.stations[0].tile());
        if (spawn === false) {
            console.warn(`cannot build train`);
            this.active = false;
            return;
        }
        this.train = this.createTrainUnits(spawn);
    }
    tick(ticks) {
        if (this.train === null) {
            throw new Error("Not initialized");
        }
        if (!this.train.isActive() || !this.activeSourceOrDestination()) {
            this.deleteTrain();
            return;
        }
        const tile = this.getNextTile();
        if (tile) {
            this.updateCarsPositions(tile);
        }
        else {
            this.targetReached();
            this.deleteTrain();
        }
    }
    loadCargo() {
        if (this.hasCargo || this.train === null) {
            return;
        }
        this.hasCargo = true;
        // Starts at 1: don't load tail engine
        for (let i = 1; i < this.cars.length; i++) {
            this.cars[i].setLoaded(true);
        }
    }
    targetReached() {
        if (this.train === null) {
            return;
        }
        this.train.setReachedTarget();
        this.cars.forEach((car) => {
            car.setReachedTarget();
        });
    }
    createTrainUnits(tile) {
        const train = this.player.buildUnit(Game_1.UnitType.Train, tile, {
            targetUnit: this.destination.unit,
            trainType: Game_1.TrainType.Engine,
        });
        // Tail is also an engine, just for cosmetics
        this.cars.push(this.player.buildUnit(Game_1.UnitType.Train, tile, {
            targetUnit: this.destination.unit,
            trainType: Game_1.TrainType.Engine,
        }));
        for (let i = 0; i < this.numCars; i++) {
            this.cars.push(this.player.buildUnit(Game_1.UnitType.Train, tile, {
                trainType: Game_1.TrainType.Carriage,
                loaded: this.hasCargo,
            }));
        }
        return train;
    }
    deleteTrain() {
        var _a;
        this.active = false;
        if ((_a = this.train) === null || _a === void 0 ? void 0 : _a.isActive()) {
            this.train.delete(false);
        }
        for (const car of this.cars) {
            if (car.isActive()) {
                car.delete(false);
            }
        }
    }
    activeSourceOrDestination() {
        return (this.stations.length > 1 &&
            this.stations[1].isActive() &&
            this.stations[0].isActive());
    }
    /**
     * Save the tiles the train go through so the cars can reuse them
     * Don't simply save the tiles the engine uses, otherwise the spacing will be dictated by the train speed
     */
    saveTraversedTiles(from, speed) {
        if (!this.currentRailroad) {
            return;
        }
        let tileToSave = from;
        for (let i = 0; i < speed && tileToSave < this.currentRailroad.getTiles().length; i++) {
            this.saveTile(this.currentRailroad.getTiles()[tileToSave]);
            tileToSave = tileToSave + 1;
        }
    }
    saveTile(tile) {
        this.usedTiles.push(tile);
        if (this.usedTiles.length > this.cars.length * this.spacing + 3) {
            this.usedTiles.shift();
        }
    }
    updateCarsPositions(newTile) {
        if (this.cars.length > 0) {
            for (let i = this.cars.length - 1; i >= 0; --i) {
                const carTileIndex = (i + 1) * this.spacing + 2;
                if (this.usedTiles.length > carTileIndex) {
                    this.cars[i].move(this.usedTiles[carTileIndex]);
                }
            }
        }
        if (this.train !== null) {
            this.train.move(newTile);
        }
    }
    nextStation() {
        if (this.stations.length > 2) {
            this.stations.shift();
            const railRoad = (0, Railroad_1.getOrientedRailroad)(this.stations[0], this.stations[1]);
            if (railRoad) {
                this.currentRailroad = railRoad;
                return true;
            }
        }
        return false;
    }
    canTradeWithDestination() {
        return (this.stations.length > 1 && this.stations[1].tradeAvailable(this.player));
    }
    getNextTile() {
        if (this.currentRailroad === null || !this.canTradeWithDestination()) {
            return null;
        }
        this.saveTraversedTiles(this.currentTile, this.speed);
        this.currentTile = this.currentTile + this.speed;
        const leftOver = this.currentTile - this.currentRailroad.getTiles().length;
        if (leftOver >= 0) {
            // Station reached, pick the next station
            this.stationReached();
            if (!this.nextStation()) {
                return null; // Destination reached (or no valid connection)
            }
            this.currentTile = leftOver;
            this.saveTraversedTiles(0, leftOver);
        }
        return this.currentRailroad.getTiles()[this.currentTile];
    }
    stationReached() {
        if (this.mg === null || this.player === null) {
            throw new Error("Not initialized");
        }
        this.stations[1].onTrainStop(this);
        return;
    }
    isActive() {
        return this.active;
    }
    activeDuringSpawnPhase() {
        return false;
    }
}
exports.TrainExecution = TrainExecution;
