import { simpleHash, toInt, withinInt } from "../Util";
import { MessageType, UnitType, } from "./Game";
import { GameUpdateType } from "./GameUpdates";
export class UnitImpl {
    constructor(_type, mg, _tile, _id, _owner, params = {}) {
        this._type = _type;
        this.mg = mg;
        this._tile = _tile;
        this._id = _id;
        this._owner = _owner;
        this._active = true;
        this._retreating = false;
        this._targetedBySAM = false;
        this._reachedTarget = false;
        this._lastOwner = null;
        // Number of missiles in cooldown, if empty all missiles are ready.
        this._missileTimerQueue = [];
        this._hasTrainStation = false;
        this._level = 1;
        this._targetable = true;
        // Nuke only
        this._trajectoryIndex = 0;
        this._lastTile = _tile;
        this._health = toInt(this.mg.unitInfo(_type).maxHealth ?? 1);
        this._targetTile =
            "targetTile" in params ? (params.targetTile ?? undefined) : undefined;
        this._trajectory = "trajectory" in params ? (params.trajectory ?? []) : [];
        this._troops = "troops" in params ? (params.troops ?? 0) : 0;
        this._lastSetSafeFromPirates =
            "lastSetSafeFromPirates" in params
                ? (params.lastSetSafeFromPirates ?? 0)
                : 0;
        this._patrolTile =
            "patrolTile" in params ? (params.patrolTile ?? undefined) : undefined;
        this._targetUnit =
            "targetUnit" in params ? (params.targetUnit ?? undefined) : undefined;
        this._loaded =
            "loaded" in params ? (params.loaded ?? undefined) : undefined;
        this._trainType = "trainType" in params ? params.trainType : undefined;
        switch (this._type) {
            case UnitType.Warship:
            case UnitType.Port:
            case UnitType.MissileSilo:
            case UnitType.DefensePost:
            case UnitType.SAMLauncher:
            case UnitType.City:
                this.mg.stats().unitBuild(_owner, this._type);
        }
    }
    setTargetable(targetable) {
        if (this._targetable !== targetable) {
            this._targetable = targetable;
            this.mg.addUpdate(this.toUpdate());
        }
    }
    isTargetable() {
        return this._targetable;
    }
    setPatrolTile(tile) {
        this._patrolTile = tile;
    }
    patrolTile() {
        return this._patrolTile;
    }
    isUnit() {
        return true;
    }
    touch() {
        this.mg.addUpdate(this.toUpdate());
    }
    setTileTarget(tile) {
        this._targetTile = tile;
    }
    tileTarget() {
        return this._targetTile;
    }
    id() {
        return this._id;
    }
    toUpdate() {
        return {
            type: GameUpdateType.Unit,
            unitType: this._type,
            id: this._id,
            troops: this._troops,
            ownerID: this._owner.smallID(),
            lastOwnerID: this._lastOwner?.smallID(),
            isActive: this._active,
            reachedTarget: this._reachedTarget,
            retreating: this._retreating,
            pos: this._tile,
            targetable: this._targetable,
            lastPos: this._lastTile,
            health: this.hasHealth() ? Number(this._health) : undefined,
            constructionType: this._constructionType,
            targetUnitId: this._targetUnit?.id() ?? undefined,
            targetTile: this.targetTile() ?? undefined,
            missileTimerQueue: this._missileTimerQueue,
            level: this.level(),
            hasTrainStation: this._hasTrainStation,
            trainType: this._trainType,
            loaded: this._loaded,
        };
    }
    type() {
        return this._type;
    }
    lastTile() {
        return this._lastTile;
    }
    move(tile) {
        if (tile === null) {
            throw new Error("tile cannot be null");
        }
        this._lastTile = this._tile;
        this._tile = tile;
        this.mg.updateUnitTile(this);
        this.mg.addUpdate(this.toUpdate());
    }
    setTroops(troops) {
        this._troops = troops;
    }
    troops() {
        return this._troops;
    }
    health() {
        return Number(this._health);
    }
    hasHealth() {
        return this.info().maxHealth !== undefined;
    }
    tile() {
        return this._tile;
    }
    owner() {
        return this._owner;
    }
    info() {
        return this.mg.unitInfo(this._type);
    }
    setOwner(newOwner) {
        switch (this._type) {
            case UnitType.Warship:
            case UnitType.Port:
            case UnitType.MissileSilo:
            case UnitType.DefensePost:
            case UnitType.SAMLauncher:
            case UnitType.City:
                this.mg.stats().unitCapture(newOwner, this._type);
                this.mg.stats().unitLose(this._owner, this._type);
                break;
        }
        this._lastOwner = this._owner;
        this._lastOwner._units = this._lastOwner._units.filter((u) => u !== this);
        this._owner = newOwner;
        this._owner._units.push(this);
        this.mg.addUpdate(this.toUpdate());
        this.mg.displayMessage(`Your ${this.type()} was captured by ${newOwner.displayName()}`, MessageType.UNIT_CAPTURED_BY_ENEMY, this._lastOwner.id());
        this.mg.displayMessage(`Captured ${this.type()} from ${this._lastOwner.displayName()}`, MessageType.CAPTURED_ENEMY_UNIT, newOwner.id());
    }
    modifyHealth(delta, attacker) {
        this._health = withinInt(this._health + toInt(delta), 0n, toInt(this.info().maxHealth ?? 1));
        if (this._health === 0n) {
            this.delete(true, attacker);
        }
    }
    delete(displayMessage, destroyer) {
        if (!this.isActive()) {
            throw new Error(`cannot delete ${this} not active`);
        }
        this._owner._units = this._owner._units.filter((b) => b !== this);
        this._active = false;
        this.mg.addUpdate(this.toUpdate());
        this.mg.removeUnit(this);
        if (displayMessage !== false && this._type !== UnitType.MIRVWarhead) {
            this.mg.displayMessage(`Your ${this._type} was destroyed`, MessageType.UNIT_DESTROYED, this.owner().id());
        }
        if (destroyer !== undefined) {
            switch (this._type) {
                case UnitType.TransportShip:
                    this.mg
                        .stats()
                        .boatDestroyTroops(destroyer, this._owner, this._troops);
                    break;
                case UnitType.TradeShip:
                    this.mg.stats().boatDestroyTrade(destroyer, this._owner);
                    break;
                case UnitType.City:
                case UnitType.DefensePost:
                case UnitType.MissileSilo:
                case UnitType.Port:
                case UnitType.SAMLauncher:
                case UnitType.Warship:
                case UnitType.Factory:
                    this.mg.stats().unitDestroy(destroyer, this._type);
                    this.mg.stats().unitLose(this.owner(), this._type);
                    break;
            }
        }
    }
    isActive() {
        return this._active;
    }
    retreating() {
        return this._retreating;
    }
    orderBoatRetreat() {
        if (this.type() !== UnitType.TransportShip) {
            throw new Error(`Cannot retreat ${this.type()}`);
        }
        this._retreating = true;
    }
    constructionType() {
        if (this.type() !== UnitType.Construction) {
            throw new Error(`Cannot get construction type on ${this.type()}`);
        }
        return this._constructionType ?? null;
    }
    setConstructionType(type) {
        if (this.type() !== UnitType.Construction) {
            throw new Error(`Cannot set construction type on ${this.type()}`);
        }
        this._constructionType = type;
        this.mg.addUpdate(this.toUpdate());
    }
    hash() {
        return this.tile() + simpleHash(this.type()) * this._id;
    }
    toString() {
        return `Unit:${this._type},owner:${this.owner().name()}`;
    }
    launch() {
        this._missileTimerQueue.push(this.mg.ticks());
        this.mg.addUpdate(this.toUpdate());
    }
    ticksLeftInCooldown() {
        return this._missileTimerQueue[0];
    }
    isInCooldown() {
        return this._missileTimerQueue.length === this._level;
    }
    missileTimerQueue() {
        return this._missileTimerQueue;
    }
    reloadMissile() {
        this._missileTimerQueue.shift();
        this.mg.addUpdate(this.toUpdate());
    }
    setTargetTile(targetTile) {
        this._targetTile = targetTile;
    }
    targetTile() {
        return this._targetTile;
    }
    setTrajectoryIndex(i) {
        const max = this._trajectory.length - 1;
        this._trajectoryIndex = i < 0 ? 0 : i > max ? max : i;
    }
    trajectoryIndex() {
        return this._trajectoryIndex;
    }
    trajectory() {
        return this._trajectory;
    }
    setTargetUnit(target) {
        this._targetUnit = target;
    }
    targetUnit() {
        return this._targetUnit;
    }
    setTargetedBySAM(targeted) {
        this._targetedBySAM = targeted;
    }
    targetedBySAM() {
        return this._targetedBySAM;
    }
    setReachedTarget() {
        this._reachedTarget = true;
    }
    reachedTarget() {
        return this._reachedTarget;
    }
    setSafeFromPirates() {
        this._lastSetSafeFromPirates = this.mg.ticks();
    }
    isSafeFromPirates() {
        return (this.mg.ticks() - this._lastSetSafeFromPirates <
            this.mg.config().safeFromPiratesCooldownMax());
    }
    level() {
        return this._level;
    }
    setTrainStation(trainStation) {
        this._hasTrainStation = trainStation;
        this.mg.addUpdate(this.toUpdate());
    }
    hasTrainStation() {
        return this._hasTrainStation;
    }
    increaseLevel() {
        this._level++;
        if ([UnitType.MissileSilo, UnitType.SAMLauncher].includes(this.type())) {
            this._missileTimerQueue.push(this.mg.ticks());
        }
        this.mg.addUpdate(this.toUpdate());
    }
    trainType() {
        return this._trainType;
    }
    isLoaded() {
        return this._loaded;
    }
    setLoaded(loaded) {
        if (this._loaded !== loaded) {
            this._loaded = loaded;
            this.mg.addUpdate(this.toUpdate());
        }
    }
}
