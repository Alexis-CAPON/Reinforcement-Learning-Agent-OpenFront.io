"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PlayerImpl = void 0;
const Utils_1 = require("../../client/Utils");
const PseudoRandom_1 = require("../PseudoRandom");
const Util_1 = require("../Util");
const username_1 = require("../validations/username");
const AttackImpl_1 = require("./AttackImpl");
const Game_1 = require("./Game");
const GameMap_1 = require("./GameMap");
const GameUpdates_1 = require("./GameUpdates");
const TransportShipUtils_1 = require("./TransportShipUtils");
const UnitImpl_1 = require("./UnitImpl");
class Donation {
    constructor(recipient, tick) {
        this.recipient = recipient;
        this.tick = tick;
    }
}
class PlayerImpl {
    constructor(mg, _smallID, playerInfo, startTroops, _team) {
        this.mg = mg;
        this._smallID = _smallID;
        this.playerInfo = playerInfo;
        this._team = _team;
        this._lastTileChange = 0;
        this.markedTraitorTick = -1;
        this.embargoes = new Map();
        this._borderTiles = new Set();
        this._units = [];
        this._tiles = new Set();
        this.pastOutgoingAllianceRequests = [];
        this._expiredAlliances = [];
        this.targets_ = [];
        this.outgoingEmojis_ = [];
        this.sentDonations = [];
        this.relations = new Map();
        this.lastDeleteUnitTick = -1;
        this._incomingAttacks = [];
        this._outgoingAttacks = [];
        this._outgoingLandAttacks = [];
        this._hasSpawned = false;
        this._isDisconnected = false;
        this.numUnitsConstructed = {};
        this._name = (0, username_1.sanitizeUsername)(playerInfo.name);
        this._troops = (0, Util_1.toInt)(startTroops);
        this._gold = 0n;
        this._displayName = this._name;
        this._pseudo_random = new PseudoRandom_1.PseudoRandom((0, Util_1.simpleHash)(this.playerInfo.id));
    }
    toUpdate() {
        var _a;
        const outgoingAllianceRequests = this.outgoingAllianceRequests().map((ar) => ar.recipient().id());
        const stats = this.mg.stats().getPlayerStats(this);
        return {
            type: GameUpdates_1.GameUpdateType.Player,
            clientID: this.clientID(),
            name: this.name(),
            displayName: this.displayName(),
            id: this.id(),
            team: (_a = this.team()) !== null && _a !== void 0 ? _a : undefined,
            smallID: this.smallID(),
            playerType: this.type(),
            isAlive: this.isAlive(),
            isDisconnected: this.isDisconnected(),
            tilesOwned: this.numTilesOwned(),
            gold: this._gold,
            troops: this.troops(),
            allies: this.alliances().map((a) => a.other(this).smallID()),
            embargoes: new Set([...this.embargoes.keys()].map((p) => p.toString())),
            isTraitor: this.isTraitor(),
            targets: this.targets().map((p) => p.smallID()),
            outgoingEmojis: this.outgoingEmojis(),
            outgoingAttacks: this._outgoingAttacks.map((a) => {
                return {
                    attackerID: a.attacker().smallID(),
                    targetID: a.target().smallID(),
                    troops: a.troops(),
                    id: a.id(),
                    retreating: a.retreating(),
                };
            }),
            incomingAttacks: this._incomingAttacks.map((a) => {
                return {
                    attackerID: a.attacker().smallID(),
                    targetID: a.target().smallID(),
                    troops: a.troops(),
                    id: a.id(),
                    retreating: a.retreating(),
                };
            }),
            outgoingAllianceRequests: outgoingAllianceRequests,
            alliances: this.alliances().map((a) => ({
                id: a.id(),
                other: a.other(this).id(),
                createdAt: a.createdAt(),
                expiresAt: a.expiresAt(),
            })),
            hasSpawned: this.hasSpawned(),
            betrayals: stats === null || stats === void 0 ? void 0 : stats.betrayals,
        };
    }
    smallID() {
        return this._smallID;
    }
    name() {
        return this._name;
    }
    displayName() {
        return this._displayName;
    }
    clientID() {
        return this.playerInfo.clientID;
    }
    id() {
        return this.playerInfo.id;
    }
    type() {
        return this.playerInfo.playerType;
    }
    clan() {
        return this.playerInfo.clan;
    }
    units(...types) {
        if (types.length === 0) {
            return this._units;
        }
        const ts = new Set(types);
        return this._units.filter((u) => ts.has(u.type()));
    }
    recordUnitConstructed(type) {
        if (this.numUnitsConstructed[type] !== undefined) {
            this.numUnitsConstructed[type]++;
        }
        else {
            this.numUnitsConstructed[type] = 1;
        }
    }
    // Count of units built by the player, including construction
    unitsConstructed(type) {
        var _a;
        const built = (_a = this.numUnitsConstructed[type]) !== null && _a !== void 0 ? _a : 0;
        let constructing = 0;
        for (const unit of this._units) {
            if (unit.type() !== Game_1.UnitType.Construction)
                continue;
            if (unit.constructionType() !== type)
                continue;
            constructing++;
        }
        const total = constructing + built;
        return total;
    }
    // Count of units owned by the player, not including construction
    unitCount(type) {
        let total = 0;
        for (const unit of this._units) {
            if (unit.type() === type) {
                total += unit.level();
            }
        }
        return total;
    }
    // Count of units owned by the player, including construction
    unitsOwned(type) {
        let total = 0;
        for (const unit of this._units) {
            if (unit.type() === type) {
                total += unit.level();
                continue;
            }
            if (unit.type() !== Game_1.UnitType.Construction)
                continue;
            if (unit.constructionType() !== type)
                continue;
            total++;
        }
        return total;
    }
    sharesBorderWith(other) {
        for (const border of this._borderTiles) {
            for (const neighbor of this.mg.map().neighbors(border)) {
                if (this.mg.map().ownerID(neighbor) === other.smallID()) {
                    return true;
                }
            }
        }
        return false;
    }
    numTilesOwned() {
        return this._tiles.size;
    }
    tiles() {
        return new Set(this._tiles.values());
    }
    borderTiles() {
        return this._borderTiles;
    }
    neighbors() {
        const ns = new Set();
        for (const border of this.borderTiles()) {
            for (const neighbor of this.mg.map().neighbors(border)) {
                if (this.mg.map().isLand(neighbor)) {
                    const owner = this.mg.map().ownerID(neighbor);
                    if (owner !== this.smallID()) {
                        ns.add(this.mg.playerBySmallID(owner));
                    }
                }
            }
        }
        return Array.from(ns);
    }
    isPlayer() {
        return true;
    }
    setTroops(troops) {
        this._troops = (0, Util_1.toInt)(troops);
    }
    conquer(tile) {
        this.mg.conquer(this, tile);
    }
    orderRetreat(id) {
        const attack = this._outgoingAttacks.filter((attack) => attack.id() === id);
        if (!attack || !attack[0]) {
            console.warn(`Didn't find outgoing attack with id ${id}`);
            return;
        }
        attack[0].orderRetreat();
    }
    executeRetreat(id) {
        const attack = this._outgoingAttacks.filter((attack) => attack.id() === id);
        // Execution is delayed so it's not an error that the attack does not exist.
        if (!attack || !attack[0]) {
            return;
        }
        attack[0].executeRetreat();
    }
    relinquish(tile) {
        if (this.mg.owner(tile) !== this) {
            throw new Error(`Cannot relinquish tile not owned by this player`);
        }
        this.mg.relinquish(tile);
    }
    info() {
        return this.playerInfo;
    }
    isAlive() {
        return this._tiles.size > 0;
    }
    hasSpawned() {
        return this._hasSpawned;
    }
    setHasSpawned(hasSpawned) {
        this._hasSpawned = hasSpawned;
    }
    incomingAllianceRequests() {
        return this.mg.allianceRequests.filter((ar) => ar.recipient() === this);
    }
    outgoingAllianceRequests() {
        return this.mg.allianceRequests.filter((ar) => ar.requestor() === this);
    }
    alliances() {
        return this.mg.alliances_.filter((a) => a.requestor() === this || a.recipient() === this);
    }
    expiredAlliances() {
        return [...this._expiredAlliances];
    }
    allies() {
        return this.alliances().map((a) => a.other(this));
    }
    isAlliedWith(other) {
        if (other === this) {
            return false;
        }
        return this.allianceWith(other) !== null;
    }
    allianceWith(other) {
        var _a;
        if (other === this) {
            return null;
        }
        return ((_a = this.alliances().find((a) => a.recipient() === other || a.requestor() === other)) !== null && _a !== void 0 ? _a : null);
    }
    canSendAllianceRequest(other) {
        if (other === this) {
            return false;
        }
        if (this.isFriendly(other) || !this.isAlive()) {
            return false;
        }
        const hasPending = this.outgoingAllianceRequests().some((ar) => ar.recipient() === other);
        if (hasPending) {
            return false;
        }
        const recent = this.pastOutgoingAllianceRequests
            .filter((ar) => ar.recipient() === other)
            .sort((a, b) => b.createdAt() - a.createdAt());
        if (recent.length === 0) {
            return true;
        }
        const delta = this.mg.ticks() - recent[0].createdAt();
        return delta >= this.mg.config().allianceRequestCooldown();
    }
    breakAlliance(alliance) {
        this.mg.breakAlliance(this, alliance);
    }
    isTraitor() {
        return (this.markedTraitorTick >= 0 &&
            this.mg.ticks() - this.markedTraitorTick <
                this.mg.config().traitorDuration());
    }
    markTraitor() {
        this.markedTraitorTick = this.mg.ticks();
        // Record stats
        this.mg.stats().betray(this);
    }
    createAllianceRequest(recipient) {
        if (this.isAlliedWith(recipient)) {
            throw new Error(`cannot create alliance request, already allies`);
        }
        return this.mg.createAllianceRequest(this, recipient);
    }
    relation(other) {
        var _a;
        if (other === this) {
            throw new Error(`cannot get relation with self: ${this}`);
        }
        const relation = (_a = this.relations.get(other)) !== null && _a !== void 0 ? _a : 0;
        return this.relationFromValue(relation);
    }
    relationFromValue(relationValue) {
        if (relationValue < -50) {
            return Game_1.Relation.Hostile;
        }
        if (relationValue < 0) {
            return Game_1.Relation.Distrustful;
        }
        if (relationValue < 50) {
            return Game_1.Relation.Neutral;
        }
        return Game_1.Relation.Friendly;
    }
    allRelationsSorted() {
        return Array.from(this.relations, ([k, v]) => ({ player: k, relation: v }))
            .sort((a, b) => a.relation - b.relation)
            .map((r) => ({
            player: r.player,
            relation: this.relationFromValue(r.relation),
        }));
    }
    updateRelation(other, delta) {
        var _a;
        if (other === this) {
            throw new Error(`cannot update relation with self: ${this}`);
        }
        const relation = (_a = this.relations.get(other)) !== null && _a !== void 0 ? _a : 0;
        const newRelation = (0, Util_1.within)(relation + delta, -100, 100);
        this.relations.set(other, newRelation);
    }
    decayRelations() {
        this.relations.forEach((r, p) => {
            const sign = -1 * Math.sign(r);
            const delta = 0.05;
            r += sign * delta;
            if (Math.abs(r) < delta * 2) {
                r = 0;
            }
            this.relations.set(p, r);
        });
    }
    canTarget(other) {
        if (this === other) {
            return false;
        }
        if (this.isFriendly(other)) {
            return false;
        }
        for (const t of this.targets_) {
            if (this.mg.ticks() - t.tick < this.mg.config().targetCooldown()) {
                return false;
            }
        }
        return true;
    }
    target(other) {
        this.targets_.push({ tick: this.mg.ticks(), target: other });
        this.mg.target(this, other);
    }
    targets() {
        return this.targets_
            .filter((t) => this.mg.ticks() - t.tick < this.mg.config().targetDuration())
            .map((t) => t.target);
    }
    transitiveTargets() {
        const ts = this.alliances()
            .map((a) => a.other(this))
            .flatMap((ally) => ally.targets());
        ts.push(...this.targets());
        return [...new Set(ts)];
    }
    sendEmoji(recipient, emoji) {
        if (recipient === this) {
            throw Error(`Cannot send emoji to oneself: ${this}`);
        }
        const msg = {
            message: emoji,
            senderID: this.smallID(),
            recipientID: recipient === Game_1.AllPlayers ? recipient : recipient.smallID(),
            createdAt: this.mg.ticks(),
        };
        this.outgoingEmojis_.push(msg);
        this.mg.sendEmojiUpdate(msg);
    }
    outgoingEmojis() {
        return this.outgoingEmojis_
            .filter((e) => this.mg.ticks() - e.createdAt <
            this.mg.config().emojiMessageDuration())
            .sort((a, b) => b.createdAt - a.createdAt);
    }
    canSendEmoji(recipient) {
        if (recipient === this) {
            return false;
        }
        const recipientID = recipient === Game_1.AllPlayers ? Game_1.AllPlayers : recipient.smallID();
        const prevMsgs = this.outgoingEmojis_.filter((msg) => msg.recipientID === recipientID);
        for (const msg of prevMsgs) {
            if (this.mg.ticks() - msg.createdAt <
                this.mg.config().emojiMessageCooldown()) {
                return false;
            }
        }
        return true;
    }
    canDonateGold(recipient) {
        if (!this.isFriendly(recipient)) {
            return false;
        }
        if (recipient.type() === Game_1.PlayerType.Human &&
            this.mg.config().gameConfig().gameMode === Game_1.GameMode.FFA &&
            this.mg.config().gameConfig().gameType === Game_1.GameType.Public) {
            return false;
        }
        if (this.mg.config().donateGold() === false) {
            return false;
        }
        for (const donation of this.sentDonations) {
            if (donation.recipient === recipient) {
                if (this.mg.ticks() - donation.tick <
                    this.mg.config().donateCooldown()) {
                    return false;
                }
            }
        }
        return true;
    }
    canDonateTroops(recipient) {
        if (!this.isFriendly(recipient)) {
            return false;
        }
        if (recipient.type() === Game_1.PlayerType.Human &&
            this.mg.config().gameConfig().gameMode === Game_1.GameMode.FFA &&
            this.mg.config().gameConfig().gameType === Game_1.GameType.Public) {
            return false;
        }
        if (this.mg.config().donateTroops() === false) {
            return false;
        }
        for (const donation of this.sentDonations) {
            if (donation.recipient === recipient) {
                if (this.mg.ticks() - donation.tick <
                    this.mg.config().donateCooldown()) {
                    return false;
                }
            }
        }
        return true;
    }
    donateTroops(recipient, troops) {
        if (troops <= 0)
            return false;
        const removed = this.removeTroops(troops);
        if (removed === 0)
            return false;
        recipient.addTroops(removed);
        this.sentDonations.push(new Donation(recipient, this.mg.ticks()));
        this.mg.displayMessage(`Sent ${(0, Utils_1.renderTroops)(troops)} troops to ${recipient.name()}`, Game_1.MessageType.SENT_TROOPS_TO_PLAYER, this.id());
        this.mg.displayMessage(`Received ${(0, Utils_1.renderTroops)(troops)} troops from ${this.name()}`, Game_1.MessageType.RECEIVED_TROOPS_FROM_PLAYER, recipient.id());
        return true;
    }
    donateGold(recipient, gold) {
        if (gold <= 0n)
            return false;
        const removed = this.removeGold(gold);
        if (removed === 0n)
            return false;
        recipient.addGold(removed);
        this.sentDonations.push(new Donation(recipient, this.mg.ticks()));
        this.mg.displayMessage(`Sent ${(0, Utils_1.renderNumber)(gold)} gold to ${recipient.name()}`, Game_1.MessageType.SENT_GOLD_TO_PLAYER, this.id());
        this.mg.displayMessage(`Received ${(0, Utils_1.renderNumber)(gold)} gold from ${this.name()}`, Game_1.MessageType.RECEIVED_GOLD_FROM_PLAYER, recipient.id(), gold);
        return true;
    }
    canDeleteUnit() {
        return (this.mg.ticks() - this.lastDeleteUnitTick >=
            this.mg.config().deleteUnitCooldown());
    }
    recordDeleteUnit() {
        this.lastDeleteUnitTick = this.mg.ticks();
    }
    hasEmbargoAgainst(other) {
        return this.embargoes.has(other.id());
    }
    canTrade(other) {
        const embargo = other.hasEmbargoAgainst(this) || this.hasEmbargoAgainst(other);
        return !embargo && other.id() !== this.id();
    }
    getEmbargoes() {
        return [...this.embargoes.values()];
    }
    addEmbargo(other, isTemporary) {
        const embargo = this.embargoes.get(other.id());
        if (embargo !== undefined && !embargo.isTemporary)
            return;
        this.mg.addUpdate({
            type: GameUpdates_1.GameUpdateType.EmbargoEvent,
            event: "start",
            playerID: this.smallID(),
            embargoedID: other.smallID(),
        });
        this.embargoes.set(other.id(), {
            createdAt: this.mg.ticks(),
            isTemporary: isTemporary,
            target: other,
        });
    }
    stopEmbargo(other) {
        this.embargoes.delete(other.id());
        this.mg.addUpdate({
            type: GameUpdates_1.GameUpdateType.EmbargoEvent,
            event: "stop",
            playerID: this.smallID(),
            embargoedID: other.smallID(),
        });
    }
    endTemporaryEmbargo(other) {
        const embargo = this.embargoes.get(other.id());
        if (embargo !== undefined && !embargo.isTemporary)
            return;
        this.stopEmbargo(other);
    }
    tradingPartners() {
        return this.mg
            .players()
            .filter((other) => other !== this && this.canTrade(other));
    }
    team() {
        return this._team;
    }
    isOnSameTeam(other) {
        if (other === this) {
            return false;
        }
        if (this.team() === null || other.team() === null) {
            return false;
        }
        if (this.team() === Game_1.ColoredTeams.Bot || other.team() === Game_1.ColoredTeams.Bot) {
            return false;
        }
        return this._team === other.team();
    }
    isFriendly(other) {
        return this.isOnSameTeam(other) || this.isAlliedWith(other);
    }
    gold() {
        return this._gold;
    }
    addGold(toAdd, tile) {
        this._gold += toAdd;
        if (tile) {
            this.mg.addUpdate({
                type: GameUpdates_1.GameUpdateType.BonusEvent,
                player: this.id(),
                tile,
                gold: Number(toAdd),
                troops: 0,
            });
        }
    }
    removeGold(toRemove) {
        if (toRemove <= 0n) {
            return 0n;
        }
        const actualRemoved = (0, Util_1.minInt)(this._gold, toRemove);
        this._gold -= actualRemoved;
        return actualRemoved;
    }
    troops() {
        return Number(this._troops);
    }
    addTroops(troops) {
        if (troops < 0) {
            this.removeTroops(-1 * troops);
            return;
        }
        this._troops += (0, Util_1.toInt)(troops);
    }
    removeTroops(troops) {
        if (troops <= 0) {
            return 0;
        }
        const toRemove = (0, Util_1.minInt)(this._troops, (0, Util_1.toInt)(troops));
        this._troops -= toRemove;
        return Number(toRemove);
    }
    captureUnit(unit) {
        if (unit.owner() === this) {
            throw new Error(`Cannot capture unit, ${this} already owns ${unit}`);
        }
        unit.setOwner(this);
    }
    buildUnit(type, spawnTile, params) {
        var _a;
        if (this.mg.config().isUnitDisabled(type)) {
            throw new Error(`Attempted to build disabled unit ${type} at tile ${spawnTile} by player ${this.name()}`);
        }
        const cost = this.mg.unitInfo(type).cost(this);
        const b = new UnitImpl_1.UnitImpl(type, this.mg, spawnTile, this.mg.nextUnitID(), this, params);
        this._units.push(b);
        this.recordUnitConstructed(type);
        this.removeGold(cost);
        this.removeTroops("troops" in params ? ((_a = params.troops) !== null && _a !== void 0 ? _a : 0) : 0);
        this.mg.addUpdate(b.toUpdate());
        this.mg.addUnit(b);
        return b;
    }
    findUnitToUpgrade(type, targetTile) {
        const range = this.mg.config().structureMinDist();
        const existing = this.mg
            .nearbyUnits(targetTile, range, type)
            .sort((a, b) => a.distSquared - b.distSquared);
        if (existing.length === 0) {
            return false;
        }
        const unit = existing[0].unit;
        if (!this.canUpgradeUnit(unit.type())) {
            return false;
        }
        return unit;
    }
    canUpgradeUnit(unitType) {
        if (!this.mg.config().unitInfo(unitType).upgradable) {
            return false;
        }
        if (this.mg.config().isUnitDisabled(unitType)) {
            return false;
        }
        if (this._gold < this.mg.config().unitInfo(unitType).cost(this)) {
            return false;
        }
        return true;
    }
    upgradeUnit(unit) {
        const cost = this.mg.unitInfo(unit.type()).cost(this);
        this.removeGold(cost);
        unit.increaseLevel();
        this.recordUnitConstructed(unit.type());
    }
    buildableUnits(tile) {
        const validTiles = this.validStructureSpawnTiles(tile);
        return Object.values(Game_1.UnitType).map((u) => {
            let canUpgrade = false;
            if (!this.mg.inSpawnPhase()) {
                const existingUnit = this.findUnitToUpgrade(u, tile);
                if (existingUnit !== false) {
                    canUpgrade = existingUnit.id();
                }
            }
            return {
                type: u,
                canBuild: this.mg.inSpawnPhase()
                    ? false
                    : this.canBuild(u, tile, validTiles),
                canUpgrade: canUpgrade,
                cost: this.mg.config().unitInfo(u).cost(this),
            };
        });
    }
    canBuild(unitType, targetTile, validTiles = null) {
        if (this.mg.config().isUnitDisabled(unitType)) {
            return false;
        }
        const cost = this.mg.unitInfo(unitType).cost(this);
        if (!this.isAlive() || this.gold() < cost) {
            return false;
        }
        switch (unitType) {
            case Game_1.UnitType.MIRV:
                if (!this.mg.hasOwner(targetTile)) {
                    return false;
                }
                return this.nukeSpawn(targetTile);
            case Game_1.UnitType.AtomBomb:
            case Game_1.UnitType.HydrogenBomb:
                return this.nukeSpawn(targetTile);
            case Game_1.UnitType.MIRVWarhead:
                return targetTile;
            case Game_1.UnitType.Port:
                return this.portSpawn(targetTile, validTiles);
            case Game_1.UnitType.Warship:
                return this.warshipSpawn(targetTile);
            case Game_1.UnitType.Shell:
            case Game_1.UnitType.SAMMissile:
                return targetTile;
            case Game_1.UnitType.TransportShip:
                return (0, TransportShipUtils_1.canBuildTransportShip)(this.mg, this, targetTile);
            case Game_1.UnitType.TradeShip:
                return this.tradeShipSpawn(targetTile);
            case Game_1.UnitType.Train:
                return this.landBasedUnitSpawn(targetTile);
            case Game_1.UnitType.MissileSilo:
            case Game_1.UnitType.DefensePost:
            case Game_1.UnitType.SAMLauncher:
            case Game_1.UnitType.City:
            case Game_1.UnitType.Factory:
            case Game_1.UnitType.Construction:
                return this.landBasedStructureSpawn(targetTile, validTiles);
            default:
                (0, Util_1.assertNever)(unitType);
        }
    }
    nukeSpawn(tile) {
        const owner = this.mg.owner(tile);
        if (owner.isPlayer()) {
            if (this.isOnSameTeam(owner)) {
                return false;
            }
        }
        // only get missilesilos that are not on cooldown
        const spawns = this.units(Game_1.UnitType.MissileSilo)
            .filter((silo) => {
            return !silo.isInCooldown();
        })
            .sort((0, Util_1.distSortUnit)(this.mg, tile));
        if (spawns.length === 0) {
            return false;
        }
        return spawns[0].tile();
    }
    portSpawn(tile, validTiles) {
        const spawns = Array.from(this.mg.bfs(tile, (0, GameMap_1.manhattanDistFN)(tile, this.mg.config().radiusPortSpawn())))
            .filter((t) => this.mg.owner(t) === this && this.mg.isOceanShore(t))
            .sort((a, b) => this.mg.manhattanDist(a, tile) - this.mg.manhattanDist(b, tile));
        const validTileSet = new Set(validTiles !== null && validTiles !== void 0 ? validTiles : this.validStructureSpawnTiles(tile));
        for (const t of spawns) {
            if (validTileSet.has(t)) {
                return t;
            }
        }
        return false;
    }
    warshipSpawn(tile) {
        if (!this.mg.isOcean(tile)) {
            return false;
        }
        const spawns = this.units(Game_1.UnitType.Port).sort((a, b) => this.mg.manhattanDist(a.tile(), tile) -
            this.mg.manhattanDist(b.tile(), tile));
        if (spawns.length === 0) {
            return false;
        }
        return spawns[0].tile();
    }
    landBasedUnitSpawn(tile) {
        return this.mg.isLand(tile) ? tile : false;
    }
    landBasedStructureSpawn(tile, validTiles = null) {
        const tiles = validTiles !== null && validTiles !== void 0 ? validTiles : this.validStructureSpawnTiles(tile);
        if (tiles.length === 0) {
            return false;
        }
        return tiles[0];
    }
    validStructureSpawnTiles(tile) {
        if (this.mg.owner(tile) !== this) {
            return [];
        }
        const searchRadius = 15;
        const searchRadiusSquared = Math.pow(searchRadius, 2);
        const types = Object.values(Game_1.UnitType).filter((unitTypeValue) => {
            return this.mg.config().unitInfo(unitTypeValue).territoryBound;
        });
        const nearbyUnits = this.mg.nearbyUnits(tile, searchRadius * 2, types);
        const nearbyTiles = this.mg.bfs(tile, (gm, t) => {
            return (this.mg.euclideanDistSquared(tile, t) < searchRadiusSquared &&
                gm.ownerID(t) === this.smallID());
        });
        const validSet = new Set(nearbyTiles);
        const minDistSquared = Math.pow(this.mg.config().structureMinDist(), 2);
        for (const t of nearbyTiles) {
            for (const { unit } of nearbyUnits) {
                if (this.mg.euclideanDistSquared(unit.tile(), t) < minDistSquared) {
                    validSet.delete(t);
                    break;
                }
            }
        }
        const valid = Array.from(validSet);
        valid.sort((a, b) => this.mg.euclideanDistSquared(a, tile) -
            this.mg.euclideanDistSquared(b, tile));
        return valid;
    }
    tradeShipSpawn(targetTile) {
        const spawns = this.units(Game_1.UnitType.Port).filter((u) => u.tile() === targetTile);
        if (spawns.length === 0) {
            return false;
        }
        return spawns[0].tile();
    }
    lastTileChange() {
        return this._lastTileChange;
    }
    isDisconnected() {
        return this._isDisconnected;
    }
    markDisconnected(isDisconnected) {
        this._isDisconnected = isDisconnected;
    }
    hash() {
        return ((0, Util_1.simpleHash)(this.id()) * (this.troops() + this.numTilesOwned()) +
            this._units.reduce((acc, unit) => acc + unit.hash(), 0));
    }
    toString() {
        return `Player:{name:${this.info().name},clientID:${this.info().clientID},isAlive:${this.isAlive()},troops:${this._troops},numTileOwned:${this.numTilesOwned()}}]`;
    }
    playerProfile() {
        const rel = {
            relations: Object.fromEntries(this.allRelationsSorted().map(({ player, relation }) => [
                player.smallID(),
                relation,
            ])),
            alliances: this.alliances().map((a) => a.other(this).smallID()),
        };
        return rel;
    }
    createAttack(target, troops, sourceTile, border) {
        const attack = new AttackImpl_1.AttackImpl(this._pseudo_random.nextID(), target, this, troops, sourceTile, border, this.mg);
        this._outgoingAttacks.push(attack);
        if (target.isPlayer()) {
            target._incomingAttacks.push(attack);
        }
        return attack;
    }
    outgoingAttacks() {
        return this._outgoingAttacks;
    }
    incomingAttacks() {
        return this._incomingAttacks;
    }
    canAttack(tile) {
        if (this.mg.hasOwner(tile) &&
            this.mg.config().numSpawnPhaseTurns() +
                this.mg.config().spawnImmunityDuration() >
                this.mg.ticks()) {
            return false;
        }
        if (this.mg.owner(tile) === this) {
            return false;
        }
        const other = this.mg.owner(tile);
        if (other.isPlayer()) {
            if (this.isFriendly(other)) {
                return false;
            }
        }
        if (!this.mg.isLand(tile)) {
            return false;
        }
        if (this.mg.hasOwner(tile)) {
            return this.sharesBorderWith(other);
        }
        else {
            for (const t of this.mg.bfs(tile, (0, GameMap_1.andFN)((gm, t) => !gm.hasOwner(t) && gm.isLand(t), (0, GameMap_1.manhattanDistFN)(tile, 200)))) {
                for (const n of this.mg.neighbors(t)) {
                    if (this.mg.owner(n) === this) {
                        return true;
                    }
                }
            }
            return false;
        }
    }
    bestTransportShipSpawn(targetTile) {
        return (0, TransportShipUtils_1.bestShoreDeploymentSource)(this.mg, this, targetTile);
    }
    // It's a probability list, so if an element appears twice it's because it's
    // twice more likely to be picked later.
    tradingPorts(port) {
        const ports = this.mg
            .players()
            .filter((p) => p !== port.owner() && p.canTrade(port.owner()))
            .flatMap((p) => p.units(Game_1.UnitType.Port))
            .sort((p1, p2) => {
            return (this.mg.manhattanDist(port.tile(), p1.tile()) -
                this.mg.manhattanDist(port.tile(), p2.tile()));
        });
        const weightedPorts = [];
        for (const [i, otherPort] of ports.entries()) {
            const expanded = new Array(otherPort.level()).fill(otherPort);
            weightedPorts.push(...expanded);
            if (i < this.mg.config().proximityBonusPortsNb(ports.length)) {
                weightedPorts.push(...expanded);
            }
            if (port.owner().isFriendly(otherPort.owner())) {
                weightedPorts.push(...expanded);
            }
        }
        return weightedPorts;
    }
}
exports.PlayerImpl = PlayerImpl;
