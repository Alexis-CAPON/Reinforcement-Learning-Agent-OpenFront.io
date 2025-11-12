"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BotExecution = void 0;
const PseudoRandom_1 = require("../PseudoRandom");
const Util_1 = require("../Util");
const BotBehavior_1 = require("./utils/BotBehavior");
class BotExecution {
    constructor(bot) {
        this.bot = bot;
        this.active = true;
        this.neighborsTerraNullius = true;
        this.behavior = null;
        this.random = new PseudoRandom_1.PseudoRandom((0, Util_1.simpleHash)(bot.id()));
        this.attackRate = this.random.nextInt(40, 80);
        this.attackTick = this.random.nextInt(0, this.attackRate);
        this.triggerRatio = this.random.nextInt(60, 90) / 100;
        this.reserveRatio = this.random.nextInt(20, 30) / 100;
        this.expandRatio = this.random.nextInt(10, 20) / 100;
    }
    activeDuringSpawnPhase() {
        return false;
    }
    init(mg) {
        this.mg = mg;
    }
    tick(ticks) {
        if (ticks % this.attackRate !== this.attackTick)
            return;
        if (!this.bot.isAlive()) {
            this.active = false;
            return;
        }
        if (this.behavior === null) {
            this.behavior = new BotBehavior_1.BotBehavior(this.random, this.mg, this.bot, this.triggerRatio, this.reserveRatio, this.expandRatio);
            // Send an attack on the first tick
            this.behavior.sendAttack(this.mg.terraNullius());
            return;
        }
        this.behavior.handleAllianceRequests();
        this.behavior.handleAllianceExtensionRequests();
        this.maybeAttack();
    }
    maybeAttack() {
        if (this.behavior === null) {
            throw new Error("not initialized");
        }
        const toAttack = this.behavior.getNeighborTraitorToAttack();
        if (toAttack !== null) {
            const odds = this.bot.isFriendly(toAttack) ? 6 : 3;
            if (this.random.chance(odds)) {
                this.behavior.sendAttack(toAttack);
                return;
            }
        }
        if (this.neighborsTerraNullius) {
            if (this.bot.sharesBorderWith(this.mg.terraNullius())) {
                this.behavior.sendAttack(this.mg.terraNullius());
                return;
            }
            this.neighborsTerraNullius = false;
        }
        this.behavior.forgetOldEnemies();
        const enemy = this.behavior.selectRandomEnemy();
        if (!enemy)
            return;
        if (!this.bot.sharesBorderWith(enemy))
            return;
        this.behavior.sendAttack(enemy);
    }
    isActive() {
        return this.active;
    }
}
exports.BotExecution = BotExecution;
