export class AllianceImpl {
    constructor(mg, requestor_, recipient_, createdAt_, id_) {
        this.mg = mg;
        this.requestor_ = requestor_;
        this.recipient_ = recipient_;
        this.createdAt_ = createdAt_;
        this.id_ = id_;
        this.extensionRequestedRequestor_ = false;
        this.extensionRequestedRecipient_ = false;
        this.expiresAt_ = createdAt_ + mg.config().allianceDuration();
    }
    other(player) {
        if (this.requestor_ === player) {
            return this.recipient_;
        }
        return this.requestor_;
    }
    requestor() {
        return this.requestor_;
    }
    recipient() {
        return this.recipient_;
    }
    createdAt() {
        return this.createdAt_;
    }
    expire() {
        this.mg.expireAlliance(this);
    }
    addExtensionRequest(player) {
        if (this.requestor_ === player) {
            this.extensionRequestedRequestor_ = true;
        }
        else if (this.recipient_ === player) {
            this.extensionRequestedRecipient_ = true;
        }
    }
    bothAgreedToExtend() {
        return (this.extensionRequestedRequestor_ && this.extensionRequestedRecipient_);
    }
    onlyOneAgreedToExtend() {
        // Requestor / Recipient of the original alliance request, not of the extension request
        // False if: no expiration or neither requested extension yet (both false), or both agreed to extend (both true)
        // True if: one requested extension, other didn't yet or actively ignored (one true, one false)
        return (this.extensionRequestedRequestor_ !== this.extensionRequestedRecipient_);
    }
    id() {
        return this.id_;
    }
    extend() {
        this.extensionRequestedRequestor_ = false;
        this.extensionRequestedRecipient_ = false;
        this.expiresAt_ = this.mg.ticks() + this.mg.config().allianceDuration();
    }
    expiresAt() {
        return this.expiresAt_;
    }
}
