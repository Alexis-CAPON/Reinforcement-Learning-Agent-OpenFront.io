import { ATTACK_INDEX_CANCEL, ATTACK_INDEX_RECV, ATTACK_INDEX_SENT, BOAT_INDEX_ARRIVE, BOAT_INDEX_CAPTURE, BOAT_INDEX_DESTROY, BOAT_INDEX_SENT, BOMB_INDEX_INTERCEPT, BOMB_INDEX_LAND, BOMB_INDEX_LAUNCH, GOLD_INDEX_STEAL, GOLD_INDEX_TRADE, GOLD_INDEX_WAR, GOLD_INDEX_WORK, OTHER_INDEX_BUILT, OTHER_INDEX_CAPTURE, OTHER_INDEX_DESTROY, OTHER_INDEX_LOST, OTHER_INDEX_UPGRADE, unitTypeToBombUnit, unitTypeToOtherUnit, } from "../StatsSchemas";
function _bigint(value) {
    switch (typeof value) {
        case "bigint":
            return value;
        case "number":
            return BigInt(Math.floor(value));
    }
}
export class StatsImpl {
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
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        p.attacks ?? (p.attacks = [0n]);
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
        var _a;
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        p.boats ?? (p.boats = { [type]: [0n] });
        (_a = p.boats)[type] ?? (_a[type] = [0n]);
        while (p.boats[type].length <= index)
            p.boats[type].push(0n);
        p.boats[type][index] += _bigint(value);
    }
    _addBomb(player, nukeType, index, value) {
        var _a;
        const type = unitTypeToBombUnit[nukeType];
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        p.bombs ?? (p.bombs = { [type]: [0n] });
        (_a = p.bombs)[type] ?? (_a[type] = [0n]);
        while (p.bombs[type].length <= index)
            p.bombs[type].push(0n);
        p.bombs[type][index] += _bigint(value);
    }
    _addGold(player, index, value) {
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        p.gold ?? (p.gold = [0n]);
        while (p.gold.length <= index)
            p.gold.push(0n);
        p.gold[index] += _bigint(value);
    }
    _addOtherUnit(player, otherUnitType, index, value) {
        var _a;
        const type = unitTypeToOtherUnit[otherUnitType];
        const p = this._makePlayerStats(player);
        if (p === undefined)
            return;
        p.units ?? (p.units = { [type]: [0n] });
        (_a = p.units)[type] ?? (_a[type] = [0n]);
        while (p.units[type].length <= index)
            p.units[type].push(0n);
        p.units[type][index] += _bigint(value);
    }
    attack(player, target, troops) {
        this._addAttack(player, ATTACK_INDEX_SENT, troops);
        if (target.isPlayer()) {
            this._addAttack(target, ATTACK_INDEX_RECV, troops);
        }
    }
    attackCancel(player, target, troops) {
        this._addAttack(player, ATTACK_INDEX_CANCEL, troops);
        this._addAttack(player, ATTACK_INDEX_SENT, -troops);
        if (target.isPlayer()) {
            this._addAttack(target, ATTACK_INDEX_RECV, -troops);
        }
    }
    betray(player) {
        this._addBetrayal(player, 1);
    }
    boatSendTrade(player, target) {
        this._addBoat(player, "trade", BOAT_INDEX_SENT, 1);
    }
    boatArriveTrade(player, target, gold) {
        this._addBoat(player, "trade", BOAT_INDEX_ARRIVE, 1);
        this._addGold(player, GOLD_INDEX_TRADE, gold);
        this._addGold(target, GOLD_INDEX_TRADE, gold);
    }
    boatCapturedTrade(player, target, gold) {
        this._addBoat(player, "trade", BOAT_INDEX_CAPTURE, 1);
        this._addGold(player, GOLD_INDEX_STEAL, gold);
    }
    boatDestroyTrade(player, target) {
        this._addBoat(player, "trade", BOAT_INDEX_DESTROY, 1);
    }
    boatSendTroops(player, target, troops) {
        this._addBoat(player, "trans", BOAT_INDEX_SENT, 1);
    }
    boatArriveTroops(player, target, troops) {
        this._addBoat(player, "trans", BOAT_INDEX_ARRIVE, 1);
    }
    boatDestroyTroops(player, target, troops) {
        this._addBoat(player, "trans", BOAT_INDEX_DESTROY, 1);
    }
    bombLaunch(player, target, type) {
        this._addBomb(player, type, BOMB_INDEX_LAUNCH, 1);
    }
    bombLand(player, target, type) {
        this._addBomb(player, type, BOMB_INDEX_LAND, 1);
    }
    bombIntercept(player, type, count) {
        this._addBomb(player, type, BOMB_INDEX_INTERCEPT, count);
    }
    goldWork(player, gold) {
        this._addGold(player, GOLD_INDEX_WORK, gold);
    }
    goldWar(player, captured, gold) {
        this._addGold(player, GOLD_INDEX_WAR, gold);
    }
    unitBuild(player, type) {
        this._addOtherUnit(player, type, OTHER_INDEX_BUILT, 1);
    }
    unitCapture(player, type) {
        this._addOtherUnit(player, type, OTHER_INDEX_CAPTURE, 1);
    }
    unitUpgrade(player, type) {
        this._addOtherUnit(player, type, OTHER_INDEX_UPGRADE, 1);
    }
    unitDestroy(player, type) {
        this._addOtherUnit(player, type, OTHER_INDEX_DESTROY, 1);
    }
    unitLose(player, type) {
        this._addOtherUnit(player, type, OTHER_INDEX_LOST, 1);
    }
}
