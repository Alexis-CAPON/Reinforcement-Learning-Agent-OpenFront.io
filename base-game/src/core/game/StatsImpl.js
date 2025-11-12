"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatsImpl = void 0;
const StatsSchemas_1 = require("../StatsSchemas");
function _bigint(value) {
    switch (typeof value) {
        case "bigint":
            return value;
        case "number":
            return BigInt(Math.floor(value));
    }
}
class StatsImpl {
    constructor() {
        this.data = {};
    }
    getPlayerStats(player) {
        const clientID = player.clientID();
        if (clientID === null)
            return undefined;
        return this.data[clientID];
    }
    stats() {
        return this.data;
    }
    _makePlayerStats(player) {
        const clientID = player.clientID();
        if (clientID === null)
            return undefined;
        if (clientID in this.data) {
            return this.data[clientID];
        }
        const data = {};
        this.data[clientID] = data;
        return data;
    }
    _addAttack(player, index, value) {
        var _a;
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        (_a = p.attacks) !== null && _a !== void 0 ? _a : (p.attacks = [0n]);
        while (p.attacks.length <= index)
            p.attacks.push(0n);
        p.attacks[index] += _bigint(value);
    }
    _addBetrayal(player, value) {
        const data = this._makePlayerStats(player);
        if (data === undefined)
            return;
        if (data.betrayals === undefined) {
            data.betrayals = _bigint(value);
        }
        else {
            data.betrayals += _bigint(value);
        }
    }
    _addBoat(player, type, index, value) {
        var _a, _b;
        var _c;
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        (_a = p.boats) !== null && _a !== void 0 ? _a : (p.boats = { [type]: [0n] });
        (_b = (_c = p.boats)[type]) !== null && _b !== void 0 ? _b : (_c[type] = [0n]);
        while (p.boats[type].length <= index)
            p.boats[type].push(0n);
        p.boats[type][index] += _bigint(value);
    }
    _addBomb(player, nukeType, index, value) {
        var _a, _b;
        var _c;
        const type = StatsSchemas_1.unitTypeToBombUnit[nukeType];
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        (_a = p.bombs) !== null && _a !== void 0 ? _a : (p.bombs = { [type]: [0n] });
        (_b = (_c = p.bombs)[type]) !== null && _b !== void 0 ? _b : (_c[type] = [0n]);
        while (p.bombs[type].length <= index)
            p.bombs[type].push(0n);
        p.bombs[type][index] += _bigint(value);
    }
    _addGold(player, index, value) {
        var _a;
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        (_a = p.gold) !== null && _a !== void 0 ? _a : (p.gold = [0n]);
        while (p.gold.length <= index)
            p.gold.push(0n);
        p.gold[index] += _bigint(value);
    }
    _addOtherUnit(player, otherUnitType, index, value) {
        var _a, _b;
        var _c;
        const type = StatsSchemas_1.unitTypeToOtherUnit[otherUnitType];
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        (_a = p.units) !== null && _a !== void 0 ? _a : (p.units = { [type]: [0n] });
        (_b = (_c = p.units)[type]) !== null && _b !== void 0 ? _b : (_c[type] = [0n]);
        while (p.units[type].length <= index)
            p.units[type].push(0n);
        p.units[type][index] += _bigint(value);
    }
    attack(player, target, troops) {
        this._addAttack(player, StatsSchemas_1.ATTACK_INDEX_SENT, troops);
        if (target.isPlayer()) {
            this._addAttack(target, StatsSchemas_1.ATTACK_INDEX_RECV, troops);
        }
    }
    attackCancel(player, target, troops) {
        this._addAttack(player, StatsSchemas_1.ATTACK_INDEX_CANCEL, troops);
        this._addAttack(player, StatsSchemas_1.ATTACK_INDEX_SENT, -troops);
        if (target.isPlayer()) {
            this._addAttack(target, StatsSchemas_1.ATTACK_INDEX_RECV, -troops);
        }
    }
    betray(player) {
        this._addBetrayal(player, 1);
    }
    boatSendTrade(player, target) {
        this._addBoat(player, "trade", StatsSchemas_1.BOAT_INDEX_SENT, 1);
    }
    boatArriveTrade(player, target, gold) {
        this._addBoat(player, "trade", StatsSchemas_1.BOAT_INDEX_ARRIVE, 1);
        this._addGold(player, StatsSchemas_1.GOLD_INDEX_TRADE, gold);
        this._addGold(target, StatsSchemas_1.GOLD_INDEX_TRADE, gold);
    }
    boatCapturedTrade(player, target, gold) {
        this._addBoat(player, "trade", StatsSchemas_1.BOAT_INDEX_CAPTURE, 1);
        this._addGold(player, StatsSchemas_1.GOLD_INDEX_STEAL, gold);
    }
    boatDestroyTrade(player, target) {
        this._addBoat(player, "trade", StatsSchemas_1.BOAT_INDEX_DESTROY, 1);
    }
    boatSendTroops(player, target, troops) {
        this._addBoat(player, "trans", StatsSchemas_1.BOAT_INDEX_SENT, 1);
    }
    boatArriveTroops(player, target, troops) {
        this._addBoat(player, "trans", StatsSchemas_1.BOAT_INDEX_ARRIVE, 1);
    }
    boatDestroyTroops(player, target, troops) {
        this._addBoat(player, "trans", StatsSchemas_1.BOAT_INDEX_DESTROY, 1);
    }
    bombLaunch(player, target, type) {
        this._addBomb(player, type, StatsSchemas_1.BOMB_INDEX_LAUNCH, 1);
    }
    bombLand(player, target, type) {
        this._addBomb(player, type, StatsSchemas_1.BOMB_INDEX_LAND, 1);
    }
    bombIntercept(player, type, count) {
        this._addBomb(player, type, StatsSchemas_1.BOMB_INDEX_INTERCEPT, count);
    }
    goldWork(player, gold) {
        this._addGold(player, StatsSchemas_1.GOLD_INDEX_WORK, gold);
    }
    goldWar(player, captured, gold) {
        this._addGold(player, StatsSchemas_1.GOLD_INDEX_WAR, gold);
    }
    unitBuild(player, type) {
        this._addOtherUnit(player, type, StatsSchemas_1.OTHER_INDEX_BUILT, 1);
    }
    unitCapture(player, type) {
        this._addOtherUnit(player, type, StatsSchemas_1.OTHER_INDEX_CAPTURE, 1);
    }
    unitUpgrade(player, type) {
        this._addOtherUnit(player, type, StatsSchemas_1.OTHER_INDEX_UPGRADE, 1);
    }
    unitDestroy(player, type) {
        this._addOtherUnit(player, type, StatsSchemas_1.OTHER_INDEX_DESTROY, 1);
    }
    unitLose(player, type) {
        this._addOtherUnit(player, type, StatsSchemas_1.OTHER_INDEX_LOST, 1);
    }
}
exports.StatsImpl = StatsImpl;
