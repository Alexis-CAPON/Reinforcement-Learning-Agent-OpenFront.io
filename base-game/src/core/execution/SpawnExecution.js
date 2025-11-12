"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpawnExecution = void 0;
const Game_1 = require("../game/Game");
const BotExecution_1 = require("./BotExecution");
const PlayerExecution_1 = require("./PlayerExecution");
const Util_1 = require("./Util");
class SpawnExecution {
    constructor(playerInfo, tile) {
        this.playerInfo = playerInfo;
        this.tile = tile;
        this.active = true;
    }
    init(mg, ticks) {
        this.mg = mg;
    }
    tick(ticks) {
        this.active = false;
        if (!this.mg.isValidRef(this.tile)) {
            console.warn(`SpawnExecution: tile ${this.tile} not valid`);
            return;
        }
        if (!this.mg.inSpawnPhase()) {
            this.active = false;
            return;
        }
        let player = null;
        if (this.mg.hasPlayer(this.playerInfo.id)) {
            player = this.mg.player(this.playerInfo.id);
        }
        else {
            player = this.mg.addPlayer(this.playerInfo);
        }
        player.tiles().forEach((t) => player.relinquish(t));
        (0, Util_1.getSpawnTiles)(this.mg, this.tile).forEach((t) => {
            player.conquer(t);
        });
        if (!player.hasSpawned()) {
            this.mg.addExecution(new PlayerExecution_1.PlayerExecution(player));
            if (player.type() === Game_1.PlayerType.Bot) {
                this.mg.addExecution(new BotExecution_1.BotExecution(player));
            }
        }
        player.setHasSpawned(true);
    }
    isActive() {
        return this.active;
    }
    activeDuringSpawnPhase() {
        return true;
    }
}
exports.SpawnExecution = SpawnExecution;
