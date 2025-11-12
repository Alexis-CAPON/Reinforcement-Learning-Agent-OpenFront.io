"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BotBehavior = void 0;
const Game_1 = require("../../game/Game");
const Util_1 = require("../../Util");
const AllianceExtensionExecution_1 = require("../alliance/AllianceExtensionExecution");
const AttackExecution_1 = require("../AttackExecution");
const EmojiExecution_1 = require("../EmojiExecution");
class BotBehavior {
    constructor(random, game, player, triggerRatio, reserveRatio, expandRatio) {
        this.random = random;
        this.game = game;
        this.player = player;
        this.triggerRatio = triggerRatio;
        this.reserveRatio = reserveRatio;
        this.expandRatio = expandRatio;
        this.enemy = null;
        this.assistAcceptEmoji = Util_1.flattenedEmojiTable.indexOf("👍");
    }
    handleAllianceRequests() {
        for (const req of this.player.incomingAllianceRequests()) {
            if (shouldAcceptAllianceRequest(this.player, req)) {
                req.accept();
            }
            else {
                req.reject();
            }
        }
    }
    handleAllianceExtensionRequests() {
        for (const alliance of this.player.alliances()) {
            // Alliance expiration tracked by Events Panel, only human ally can click Request to Renew
            // Skip if no expiration yet/ ally didn't request extension yet/ bot already agreed to extend
            if (!alliance.onlyOneAgreedToExtend())
                continue;
            // Nation is either Friendly or Neutral as an ally. Bot has no attitude
            // If Friendly or Bot, always agree to extend. If Neutral, have random chance decide
            const human = alliance.other(this.player);
            if (this.player.type() === Game_1.PlayerType.FakeHuman &&
                this.player.relation(human) === Game_1.Relation.Neutral) {
                if (!this.random.chance(1.5))
                    continue;
            }
            this.game.addExecution(new AllianceExtensionExecution_1.AllianceExtensionExecution(this.player, human.id()));
        }
    }
    emoji(player, emoji) {
        if (player.type() !== Game_1.PlayerType.Human)
            return;
        this.game.addExecution(new EmojiExecution_1.EmojiExecution(this.player, player.id(), emoji));
    }
    setNewEnemy(newEnemy) {
        this.enemy = newEnemy;
        this.enemyUpdated = this.game.ticks();
    }
    clearEnemy() {
        this.enemy = null;
    }
    forgetOldEnemies() {
        // Forget old enemies
        if (this.game.ticks() - this.enemyUpdated > 100) {
            this.clearEnemy();
        }
    }
    hasSufficientTroops() {
        const maxTroops = this.game.config().maxTroops(this.player);
        const ratio = this.player.troops() / maxTroops;
        return ratio >= this.triggerRatio;
    }
    checkIncomingAttacks() {
        // Switch enemies if we're under attack
        const incomingAttacks = this.player.incomingAttacks();
        let largestAttack = 0;
        let largestAttacker;
        for (const attack of incomingAttacks) {
            if (attack.troops() <= largestAttack)
                continue;
            largestAttack = attack.troops();
            largestAttacker = attack.attacker();
        }
        if (largestAttacker !== undefined) {
            this.setNewEnemy(largestAttacker);
        }
    }
    getNeighborTraitorToAttack() {
        const traitors = this.player
            .neighbors()
            .filter((n) => n.isPlayer() && n.isTraitor());
        return traitors.length > 0 ? this.random.randElement(traitors) : null;
    }
    assistAllies() {
        outer: for (const ally of this.player.allies()) {
            if (ally.targets().length === 0)
                continue;
            if (this.player.relation(ally) < Game_1.Relation.Friendly) {
                // this.emoji(ally, "🤦");
                continue;
            }
            for (const target of ally.targets()) {
                if (target === this.player) {
                    // this.emoji(ally, "💀");
                    continue;
                }
                if (this.player.isAlliedWith(target)) {
                    // this.emoji(ally, "👎");
                    continue;
                }
                // All checks passed, assist them
                this.player.updateRelation(ally, -20);
                this.setNewEnemy(target);
                this.emoji(ally, this.assistAcceptEmoji);
                break outer;
            }
        }
    }
    selectEnemy() {
        if (this.enemy === null) {
            // Save up troops until we reach the trigger ratio
            if (!this.hasSufficientTroops())
                return null;
            // Prefer neighboring bots
            const bots = this.player
                .neighbors()
                .filter((n) => n.isPlayer() && n.type() === Game_1.PlayerType.Bot);
            if (bots.length > 0) {
                const density = (p) => p.troops() / p.numTilesOwned();
                let lowestDensityBot;
                let lowestDensity = Infinity;
                for (const bot of bots) {
                    const currentDensity = density(bot);
                    if (currentDensity < lowestDensity) {
                        lowestDensity = currentDensity;
                        lowestDensityBot = bot;
                    }
                }
                if (lowestDensityBot !== undefined) {
                    this.setNewEnemy(lowestDensityBot);
                }
            }
            // Retaliate against incoming attacks
            if (this.enemy === null) {
                this.checkIncomingAttacks();
            }
            // Select the most hated player
            if (this.enemy === null) {
                const mostHated = this.player.allRelationsSorted()[0];
                if (mostHated !== undefined &&
                    mostHated.relation === Game_1.Relation.Hostile) {
                    this.setNewEnemy(mostHated.player);
                }
            }
        }
        // Sanity check, don't attack our allies or teammates
        return this.enemySanityCheck();
    }
    selectRandomEnemy() {
        if (this.enemy === null) {
            // Save up troops until we reach the trigger ratio
            if (!this.hasSufficientTroops())
                return null;
            // Choose a new enemy randomly
            const neighbors = this.player.neighbors();
            for (const neighbor of this.random.shuffleArray(neighbors)) {
                if (!neighbor.isPlayer())
                    continue;
                if (this.player.isFriendly(neighbor))
                    continue;
                if (neighbor.type() === Game_1.PlayerType.FakeHuman) {
                    if (this.random.chance(2)) {
                        continue;
                    }
                }
                this.setNewEnemy(neighbor);
            }
            // Retaliate against incoming attacks
            if (this.enemy === null) {
                this.checkIncomingAttacks();
            }
            // Select a traitor as an enemy
            if (this.enemy === null) {
                const toAttack = this.getNeighborTraitorToAttack();
                if (toAttack !== null) {
                    if (!this.player.isFriendly(toAttack) && this.random.chance(3)) {
                        this.setNewEnemy(toAttack);
                    }
                }
            }
        }
        // Sanity check, don't attack our allies or teammates
        return this.enemySanityCheck();
    }
    enemySanityCheck() {
        if (this.enemy && this.player.isFriendly(this.enemy)) {
            this.clearEnemy();
        }
        return this.enemy;
    }
    sendAttack(target) {
        if (target.isPlayer() && this.player.isOnSameTeam(target))
            return;
        const maxTroops = this.game.config().maxTroops(this.player);
        const reserveRatio = target.isPlayer()
            ? this.reserveRatio
            : this.expandRatio;
        const targetTroops = maxTroops * reserveRatio;
        const troops = this.player.troops() - targetTroops;
        if (troops < 1)
            return;
        this.game.addExecution(new AttackExecution_1.AttackExecution(troops, this.player, target.isPlayer() ? target.id() : null));
    }
}
exports.BotBehavior = BotBehavior;
function shouldAcceptAllianceRequest(player, request) {
    if (player.relation(request.requestor()) < Game_1.Relation.Neutral) {
        return false; // Reject if hasMalice
    }
    if (request.requestor().isTraitor()) {
        return false; // Reject if isTraitor
    }
    if (request.requestor().numTilesOwned() > player.numTilesOwned() * 3) {
        return true; // Accept if requestorIsMuchLarger
    }
    if (request.requestor().alliances().length >= 3) {
        return false; // Reject if tooManyAlliances
    }
    return true; // Accept otherwise
}
