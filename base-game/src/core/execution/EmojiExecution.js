import { AllPlayers, PlayerType, } from "../game/Game";
import { flattenedEmojiTable } from "../Util";
export class EmojiExecution {
    constructor(requestor, recipientID, emoji) {
        this.requestor = requestor;
        this.recipientID = recipientID;
        this.emoji = emoji;
        this.active = true;
    }
    init(mg, ticks) {
        if (this.recipientID !== AllPlayers && !mg.hasPlayer(this.recipientID)) {
            console.warn(`EmojiExecution: recipient ${this.recipientID} not found`);
            this.active = false;
            return;
        }
        this.recipient =
            this.recipientID === AllPlayers
                ? AllPlayers
                : mg.player(this.recipientID);
    }
    tick(ticks) {
        const emojiString = flattenedEmojiTable[this.emoji];
        if (emojiString === undefined) {
            console.warn(`cannot send emoji ${this.emoji} from ${this.requestor} to ${this.recipient}`);
        }
        else if (this.requestor.canSendEmoji(this.recipient)) {
            this.requestor.sendEmoji(this.recipient, emojiString);
            if (emojiString === "🖕" &&
                this.recipient !== AllPlayers &&
                this.recipient.type() === PlayerType.FakeHuman) {
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
