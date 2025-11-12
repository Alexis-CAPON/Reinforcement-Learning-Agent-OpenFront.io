"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AllianceRequestImpl = void 0;
const GameUpdates_1 = require("./GameUpdates");
class AllianceRequestImpl {
    constructor(requestor_, recipient_, tickCreated, game) {
        this.requestor_ = requestor_;
        this.recipient_ = recipient_;
        this.tickCreated = tickCreated;
        this.game = game;
        this.status_ = "pending";
    }
    status() {
        return this.status_;
    }
    requestor() {
        return this.requestor_;
    }
    recipient() {
        return this.recipient_;
    }
    createdAt() {
        return this.tickCreated;
    }
    accept() {
        this.status_ = "accepted";
        this.game.acceptAllianceRequest(this);
    }
    reject() {
        this.status_ = "rejected";
        this.game.rejectAllianceRequest(this);
    }
    toUpdate() {
        return {
            type: GameUpdates_1.GameUpdateType.AllianceRequest,
            requestorID: this.requestor_.smallID(),
            recipientID: this.recipient_.smallID(),
            createdAt: this.tickCreated,
        };
    }
}
exports.AllianceRequestImpl = AllianceRequestImpl;
