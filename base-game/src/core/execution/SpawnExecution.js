import { PlayerType } from "../game/Game";
import { BotExecution } from "./BotExecution";
import { PlayerExecution } from "./PlayerExecution";
import { getSpawnTiles } from "./Util";
export class SpawnExecution {
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
        getSpawnTiles(this.mg, this.tile).forEach((t) => {
            player.conquer(t);
        });
        if (!player.hasSpawned()) {
            this.mg.addExecution(new PlayerExecution(player));
            if (player.type() === PlayerType.Bot) {
                this.mg.addExecution(new BotExecution(player));
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
