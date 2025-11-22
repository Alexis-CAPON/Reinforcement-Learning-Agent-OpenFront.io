import { Cell } from "./Game";
export class AttackImpl {
    constructor(_id, _target, _attacker, _troops, _sourceTile, _border, _mg) {
        this._id = _id;
        this._target = _target;
        this._attacker = _attacker;
        this._troops = _troops;
        this._sourceTile = _sourceTile;
        this._border = _border;
        this._mg = _mg;
        this._isActive = true;
        this._borderSize = 0;
        this._retreating = false;
        this._retreated = false;
    }
    sourceTile() {
        return this._sourceTile;
    }
    target() {
        return this._target;
    }
    attacker() {
        return this._attacker;
    }
    troops() {
        return this._troops;
    }
    setTroops(troops) {
        this._troops = troops;
    }
    isActive() {
        return this._isActive;
    }
    id() {
        return this._id;
    }
    delete() {
        if (this._target.isPlayer()) {
            this._target._incomingAttacks = this._target._incomingAttacks.filter((a) => a !== this);
        }
        this._attacker._outgoingAttacks = this._attacker._outgoingAttacks.filter((a) => a !== this);
        this._isActive = false;
    }
    orderRetreat() {
        this._retreating = true;
    }
    executeRetreat() {
        this._retreated = true;
    }
    retreating() {
        return this._retreating;
    }
    retreated() {
        return this._retreated;
    }
    borderSize() {
        return this._borderSize;
    }
    clearBorder() {
        this._borderSize = 0;
        this._border.clear();
    }
    addBorderTile(tile) {
        if (!this._border.has(tile)) {
            this._borderSize += 1;
            this._border.add(tile);
        }
    }
    removeBorderTile(tile) {
        if (this._border.has(tile)) {
            this._borderSize -= 1;
            this._border.delete(tile);
        }
    }
    averagePosition() {
        if (this._borderSize === 0) {
            if (this.sourceTile() === null) {
                // No border tiles and no source tile—return a default position or throw an error
                return null;
            }
            // No border tiles yet—use the source tile's location
            const tile = this.sourceTile();
            return new Cell(this._mg.map().x(tile), this._mg.map().y(tile));
        }
        let averageX = 0;
        let averageY = 0;
        for (const t of this._border) {
            averageX += this._mg.map().x(t);
            averageY += this._mg.map().y(t);
        }
        averageX = averageX / this._borderSize;
        averageY = averageY / this._borderSize;
        return new Cell(averageX, averageY);
    }
}
