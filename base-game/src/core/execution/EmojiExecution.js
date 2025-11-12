"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EmojiExecution = void 0;
const Game_1 = require("../game/Game");
const Util_1 = require("../Util");
class EmojiExecution {
    constructor(requestor, recipientID, emoji) {
        this.requestor = requestor;
        this.recipientID = recipientID;
        this.emoji = emoji;
        this.active = true;
    }
    init(mg, ticks) {
        if (this.recipientID !== Game_1.AllPlayers && !mg.hasPlayer(this.recipientID)) {
            console.warn(`EmojiExecution: recipient ${this.recipientID} not found`);
            this.active = false;
            return;
        }
        this.recipient =
            this.recipientID === Game_1.AllPlayers
                ? Game_1.AllPlayers
                : mg.player(this.recipientID);
    }
    tick(ticks) {
        const emojiString = Util_1.flattenedEmojiTable[this.emoji];
        if (emojiString === undefined) {
            console.warn(`cannot send emoji ${this.emoji} from ${this.requestor} to ${this.recipient}`);
        }
        else if (this.requestor.canSendEmoji(this.recipient)) {
            this.requestor.sendEmoji(this.recipient, emojiString);
            if (emojiString === "🖕" &&
                this.recipient !== Game_1.AllPlayers &&
                this.recipient.type() === Game_1.PlayerType.FakeHuman) {
                this.recipient.updateRelation(this.requestor, -100);
            }
        }
        else {
            console.warn(`cannot send emoji from ${this.requestor} to ${this.recipient}`);
        }
        this.active = false;
    }
    isActive() {
        return this.active;
    }
    activeDuringSpawnPhase() {
        return false;
    }
}
exports.EmojiExecution = EmojiExecution;
