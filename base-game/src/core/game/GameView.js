"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.GameView = exports.PlayerView = exports.UnitView = void 0;
const jose_1 = require("jose");
const PatternDecoder_1 = require("../PatternDecoder");
const Util_1 = require("../Util");
const Game_1 = require("./Game");
const GameUpdates_1 = require("./GameUpdates");
const TerraNulliusImpl_1 = require("./TerraNulliusImpl");
const UnitGrid_1 = require("./UnitGrid");
const UserSettings_1 = require("./UserSettings");
const userSettings = new UserSettings_1.UserSettings();
class UnitView {
    constructor(gameView, data) {
        this.gameView = gameView;
        this.data = data;
        this._wasUpdated = true;
        this.lastPos = [];
        this.lastPos.push(data.pos);
        this._createdAt = this.gameView.ticks();
    }
    createdAt() {
        return this._createdAt;
    }
    wasUpdated() {
        return this._wasUpdated;
    }
    lastTiles() {
        return this.lastPos;
    }
    lastTile() {
        if (this.lastPos.length === 0) {
            return this.data.pos;
        }
        return this.lastPos[0];
    }
    update(data) {
        this.lastPos.push(data.pos);
        this._wasUpdated = true;
        this.data = data;
    }
    id() {
        return this.data.id;
    }
    targetable() {
        return this.data.targetable;
    }
    type() {
        return this.data.unitType;
    }
    troops() {
        return this.data.troops;
    }
    retreating() {
        if (this.type() !== Game_1.UnitType.TransportShip) {
            throw Error("Must be a transport ship");
        }
        return this.data.retreating;
    }
    tile() {
        return this.data.pos;
    }
    owner() {
        return this.gameView.playerBySmallID(this.data.ownerID);
    }
    isActive() {
        return this.data.isActive;
    }
    reachedTarget() {
        return this.data.reachedTarget;
    }
    hasHealth() {
        return this.data.health !== undefined;
    }
    health() {
        var _a;
        return (_a = this.data.health) !== null && _a !== void 0 ? _a : 0;
    }
    constructionType() {
        return this.data.constructionType;
    }
    targetUnitId() {
        return this.data.targetUnitId;
    }
    targetTile() {
        return this.data.targetTile;
    }
    // How "ready" this unit is from 0 to 1.
    missileReadinesss() {
        const maxMissiles = this.data.level;
        const missilesReloading = this.data.missileTimerQueue.length;
        if (missilesReloading === 0) {
            return 1;
        }
        const missilesReady = maxMissiles - missilesReloading;
        if (missilesReady === 0 && maxMissiles > 1) {
            // Unless we have just one missile (level 1),
            // show 0% readiness so user knows no missiles are ready.
            return 0;
        }
        let readiness = missilesReady / maxMissiles;
        const cooldownDuration = this.data.unitType === Game_1.UnitType.SAMLauncher
            ? this.gameView.config().SAMCooldown()
            : this.gameView.config().SiloCooldown();
        for (const cooldown of this.data.missileTimerQueue) {
            const cooldownProgress = this.gameView.ticks() - cooldown;
            const cooldownRatio = cooldownProgress / cooldownDuration;
            const adjusted = cooldownRatio / maxMissiles;
            readiness += adjusted;
        }
        return readiness;
    }
    level() {
        return this.data.level;
    }
    hasTrainStation() {
        return this.data.hasTrainStation;
    }
    trainType() {
        return this.data.trainType;
    }
    isLoaded() {
        return this.data.loaded;
    }
}
exports.UnitView = UnitView;
class PlayerView {
    constructor(game, data, nameData, cosmetics) {
        this.game = game;
        this.data = data;
        this.nameData = nameData;
        this.cosmetics = cosmetics;
        this.anonymousName = null;
        if (data.clientID === game.myClientID()) {
            this.anonymousName = this.data.name;
        }
        else {
            this.anonymousName = (0, Util_1.createRandomName)(this.data.name, this.data.playerType);
        }
        this.decoder =
            this.cosmetics.pattern === undefined
                ? undefined
                : new PatternDecoder_1.PatternDecoder(this.cosmetics.pattern, jose_1.base64url.decode);
    }
    patternDecoder() {
        return this.decoder;
    }
    actions(tile) {
        return __awaiter(this, void 0, void 0, function* () {
            return this.game.worker.playerInteraction(this.id(), this.game.x(tile), this.game.y(tile));
        });
    }
    borderTiles() {
        return __awaiter(this, void 0, void 0, function* () {
            return this.game.worker.playerBorderTiles(this.id());
        });
    }
    outgoingAttacks() {
        return this.data.outgoingAttacks;
    }
    incomingAttacks() {
        return this.data.incomingAttacks;
    }
    attackAveragePosition(playerID, attackID) {
        return __awaiter(this, void 0, void 0, function* () {
            return this.game.worker.attackAveragePosition(playerID, attackID);
        });
    }
    units(...types) {
        return this.game
            .units(...types)
            .filter((u) => u.owner().smallID() === this.smallID());
    }
    nameLocation() {
        return this.nameData;
    }
    smallID() {
        return this.data.smallID;
    }
    name() {
        return this.anonymousName !== null && userSettings.anonymousNames()
            ? this.anonymousName
            : this.data.name;
    }
    displayName() {
        return this.anonymousName !== null && userSettings.anonymousNames()
            ? this.anonymousName
            : this.data.name;
    }
    clientID() {
        return this.data.clientID;
    }
    id() {
        return this.data.id;
    }
    team() {
        var _a;
        return (_a = this.data.team) !== null && _a !== void 0 ? _a : null;
    }
    type() {
        return this.data.playerType;
    }
    isAlive() {
        return this.data.isAlive;
    }
    isPlayer() {
        return true;
    }
    numTilesOwned() {
        return this.data.tilesOwned;
    }
    allies() {
        return this.data.allies.map((a) => this.game.playerBySmallID(a));
    }
    targets() {
        return this.data.targets.map((id) => this.game.playerBySmallID(id));
    }
    gold() {
        return this.data.gold;
    }
    troops() {
        return this.data.troops;
    }
    totalUnitLevels(type) {
        return this.units(type)
            .map((unit) => unit.level())
            .reduce((a, b) => a + b, 0);
    }
    isAlliedWith(other) {
        return this.data.allies.some((n) => other.smallID() === n);
    }
    isOnSameTeam(other) {
        return this.data.team !== undefined && this.data.team === other.data.team;
    }
    isFriendly(other) {
        return this.isAlliedWith(other) || this.isOnSameTeam(other);
    }
    isRequestingAllianceWith(other) {
        return this.data.outgoingAllianceRequests.some((id) => other.id() === id);
    }
    alliances() {
        return this.data.alliances;
    }
    hasEmbargoAgainst(other) {
        return this.data.embargoes.has(other.id());
    }
    hasEmbargo(other) {
        return this.hasEmbargoAgainst(other) || other.hasEmbargoAgainst(this);
    }
    profile() {
        return this.game.worker.playerProfile(this.smallID());
    }
    bestTransportShipSpawn(targetTile) {
        return this.game.worker.transportShipSpawn(this.id(), targetTile);
    }
    transitiveTargets() {
        return [...this.targets(), ...this.allies().flatMap((p) => p.targets())];
    }
    isTraitor() {
        return this.data.isTraitor;
    }
    outgoingEmojis() {
        return this.data.outgoingEmojis;
    }
    hasSpawned() {
        return this.data.hasSpawned;
    }
    isDisconnected() {
        return this.data.isDisconnected;
    }
    canDeleteUnit() {
        return true;
    }
}
exports.PlayerView = PlayerView;
class GameView {
    constructor(worker, _config, _mapData, _myClientID, _gameID, humans) {
        this.worker = worker;
        this._config = _config;
        this._mapData = _mapData;
        this._myClientID = _myClientID;
        this._gameID = _gameID;
        this.humans = humans;
        this.smallIDToID = new Map();
        this._players = new Map();
        this._units = new Map();
        this.updatedTiles = [];
        this._myPlayer = null;
        this._focusedPlayer = null;
        this.toDelete = new Set();
        this._cosmetics = new Map();
        this._map = this._mapData.gameMap;
        this.lastUpdate = null;
        this.unitGrid = new UnitGrid_1.UnitGrid(this._map);
        this._cosmetics = new Map(this.humans.map((h) => [
            h.clientID,
            { flag: h.flag, pattern: h.pattern },
        ]));
        for (const nation of this._mapData.manifest.nations) {
            // Nations don't have client ids, so we use their name as the key instead.
            this._cosmetics.set(nation.name, {
                flag: nation.flag,
            });
        }
    }
    isOnEdgeOfMap(ref) {
        return this._map.isOnEdgeOfMap(ref);
    }
    updatesSinceLastTick() {
        var _a, _b;
        return (_b = (_a = this.lastUpdate) === null || _a === void 0 ? void 0 : _a.updates) !== null && _b !== void 0 ? _b : null;
    }
    update(gu) {
        this.toDelete.forEach((id) => this._units.delete(id));
        this.toDelete.clear();
        this.lastUpdate = gu;
        this.updatedTiles = [];
        this.lastUpdate.packedTileUpdates.forEach((tu) => {
            this.updatedTiles.push(this.updateTile(tu));
        });
        if (gu.updates === null) {
            throw new Error("lastUpdate.updates not initialized");
        }
        gu.updates[GameUpdates_1.GameUpdateType.Player].forEach((pu) => {
            var _a, _b, _c;
            this.smallIDToID.set(pu.smallID, pu.id);
            const player = this._players.get(pu.id);
            if (player !== undefined) {
                player.data = pu;
                player.nameData = gu.playerNameViewData[pu.id];
            }
            else {
                this._players.set(pu.id, new PlayerView(this, pu, gu.playerNameViewData[pu.id], 
                // First check human by clientID, then check nation by name.
                (_c = (_b = this._cosmetics.get((_a = pu.clientID) !== null && _a !== void 0 ? _a : "")) !== null && _b !== void 0 ? _b : this._cosmetics.get(pu.name)) !== null && _c !== void 0 ? _c : {}));
            }
        });
        for (const unit of this._units.values()) {
            unit._wasUpdated = false;
            unit.lastPos = unit.lastPos.slice(-1);
        }
        gu.updates[GameUpdates_1.GameUpdateType.Unit].forEach((update) => {
            let unit = this._units.get(update.id);
            if (unit !== undefined) {
                unit.update(update);
            }
            else {
                unit = new UnitView(this, update);
                this._units.set(update.id, unit);
                this.unitGrid.addUnit(unit);
            }
            if (!update.isActive) {
                this.unitGrid.removeUnit(unit);
            }
            else if (unit.tile() !== unit.lastTile()) {
                this.unitGrid.updateUnitCell(unit);
            }
            if (!unit.isActive()) {
                // Wait until next tick to delete the unit.
                this.toDelete.add(unit.id());
            }
        });
    }
    recentlyUpdatedTiles() {
        return this.updatedTiles;
    }
    nearbyUnits(tile, searchRange, types, predicate) {
        return this.unitGrid.nearbyUnits(tile, searchRange, types, predicate);
    }
    hasUnitNearby(tile, searchRange, type, playerId) {
        return this.unitGrid.hasUnitNearby(tile, searchRange, type, playerId);
    }
    myClientID() {
        return this._myClientID;
    }
    myPlayer() {
        var _a;
        (_a = this._myPlayer) !== null && _a !== void 0 ? _a : (this._myPlayer = this.playerByClientID(this._myClientID));
        return this._myPlayer;
    }
    player(id) {
        const player = this._players.get(id);
        if (player === undefined) {
            throw Error(`player id ${id} not found`);
        }
        return player;
    }
    players() {
        return Array.from(this._players.values());
    }
    playerBySmallID(id) {
        if (id === 0) {
            return new TerraNulliusImpl_1.TerraNulliusImpl();
        }
        const playerId = this.smallIDToID.get(id);
        if (playerId === undefined) {
            throw new Error(`small id ${id} not found`);
        }
        return this.player(playerId);
    }
    playerByClientID(id) {
        var _a;
        const player = (_a = Array.from(this._players.values()).filter((p) => p.clientID() === id)[0]) !== null && _a !== void 0 ? _a : null;
        if (player === null) {
            return null;
        }
        return player;
    }
    hasPlayer(id) {
        return false;
    }
    playerViews() {
        return Array.from(this._players.values());
    }
    owner(tile) {
        return this.playerBySmallID(this.ownerID(tile));
    }
    ticks() {
        if (this.lastUpdate === null)
            return 0;
        return this.lastUpdate.tick;
    }
    inSpawnPhase() {
        return this.ticks() <= this._config.numSpawnPhaseTurns();
    }
    config() {
        return this._config;
    }
    units(...types) {
        if (types.length === 0) {
            return Array.from(this._units.values()).filter((u) => u.isActive());
        }
        return Array.from(this._units.values()).filter((u) => u.isActive() && types.includes(u.type()));
    }
    unit(id) {
        return this._units.get(id);
    }
    unitInfo(type) {
        return this._config.unitInfo(type);
    }
    ref(x, y) {
        return this._map.ref(x, y);
    }
    isValidRef(ref) {
        return this._map.isValidRef(ref);
    }
    x(ref) {
        return this._map.x(ref);
    }
    y(ref) {
        return this._map.y(ref);
    }
    cell(ref) {
        return this._map.cell(ref);
    }
    width() {
        return this._map.width();
    }
    height() {
        return this._map.height();
    }
    numLandTiles() {
        return this._map.numLandTiles();
    }
    isValidCoord(x, y) {
        return this._map.isValidCoord(x, y);
    }
    isLand(ref) {
        return this._map.isLand(ref);
    }
    isOceanShore(ref) {
        return this._map.isOceanShore(ref);
    }
    isOcean(ref) {
        return this._map.isOcean(ref);
    }
    isShoreline(ref) {
        return this._map.isShoreline(ref);
    }
    magnitude(ref) {
        return this._map.magnitude(ref);
    }
    ownerID(ref) {
        return this._map.ownerID(ref);
    }
    hasOwner(ref) {
        return this._map.hasOwner(ref);
    }
    setOwnerID(ref, playerId) {
        return this._map.setOwnerID(ref, playerId);
    }
    hasFallout(ref) {
        return this._map.hasFallout(ref);
    }
    setFallout(ref, value) {
        return this._map.setFallout(ref, value);
    }
    isBorder(ref) {
        return this._map.isBorder(ref);
    }
    neighbors(ref) {
        return this._map.neighbors(ref);
    }
    isWater(ref) {
        return this._map.isWater(ref);
    }
    isLake(ref) {
        return this._map.isLake(ref);
    }
    isShore(ref) {
        return this._map.isShore(ref);
    }
    cost(ref) {
        return this._map.cost(ref);
    }
    terrainType(ref) {
        return this._map.terrainType(ref);
    }
    forEachTile(fn) {
        return this._map.forEachTile(fn);
    }
    manhattanDist(c1, c2) {
        return this._map.manhattanDist(c1, c2);
    }
    euclideanDistSquared(c1, c2) {
        return this._map.euclideanDistSquared(c1, c2);
    }
    bfs(tile, filter) {
        return this._map.bfs(tile, filter);
    }
    toTileUpdate(tile) {
        return this._map.toTileUpdate(tile);
    }
    updateTile(tu) {
        return this._map.updateTile(tu);
    }
    numTilesWithFallout() {
        return this._map.numTilesWithFallout();
    }
    gameID() {
        return this._gameID;
    }
    focusedPlayer() {
        // TODO: renable when performance issues are fixed.
        return this.myPlayer();
    }
    setFocusedPlayer(player) {
        this._focusedPlayer = player;
    }
}
exports.GameView = GameView;
