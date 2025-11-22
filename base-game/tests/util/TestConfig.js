import { DefaultConfig } from "../../src/core/configuration/DefaultConfig";
export class TestConfig extends DefaultConfig {
    constructor() {
        super(...arguments);
        this._proximityBonusPortsNb = 0;
        this._defaultNukeSpeed = 4;
    }
    samHittingChance() {
        return 1;
    }
    radiusPortSpawn() {
        return 1;
    }
    proximityBonusPortsNb(totalPorts) {
        return this._proximityBonusPortsNb;
    }
    // Specific to TestConfig
    setProximityBonusPortsNb(nb) {
        this._proximityBonusPortsNb = nb;
    }
    nukeMagnitudes(_) {
        return { inner: 1, outer: 1 };
    }
    setDefaultNukeSpeed(speed) {
        this._defaultNukeSpeed = speed;
    }
    defaultNukeSpeed() {
        return this._defaultNukeSpeed;
    }
    defaultNukeTargetableRange() {
        return 20;
    }
    defaultSamRange() {
        return 20;
    }
    spawnImmunityDuration() {
        return 0;
    }
    attackLogic(gm, attackTroops, attacker, defender, tileToConquer) {
        return { attackerTroopLoss: 1, defenderTroopLoss: 1, tilesPerTickUsed: 1 };
    }
    attackTilesPerTick(attackTroops, attacker, defender, numAdjacentTilesWithEnemy) {
        return 1;
    }
}
