"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkerClient = void 0;
const Game_1 = require("../game/Game");
const Util_1 = require("../Util");
class WorkerClient {
    constructor(gameStartInfo, clientID) {
        this.gameStartInfo = gameStartInfo;
        this.clientID = clientID;
        this.isInitialized = false;
        this.worker = new Worker(new URL("./Worker.worker.ts", import.meta.url));
        this.messageHandlers = new Map();
        // Set up global message handler
        this.worker.addEventListener("message", this.handleWorkerMessage.bind(this));
    }
    handleWorkerMessage(event) {
        const message = event.data;
        switch (message.type) {
            case "game_update":
                if (this.gameUpdateCallback && message.gameUpdate) {
                    this.gameUpdateCallback(message.gameUpdate);
                }
                break;
            case "initialized":
            default:
                if (message.id && this.messageHandlers.has(message.id)) {
                    const handler = this.messageHandlers.get(message.id);
                    handler(message);
                    this.messageHandlers.delete(message.id);
                }
                break;
        }
    }
    initialize() {
        return new Promise((resolve, reject) => {
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "initialized") {
                    this.isInitialized = true;
                    resolve();
                }
            });
            this.worker.postMessage({
                type: "init",
                id: messageId,
                gameStartInfo: this.gameStartInfo,
                clientID: this.clientID,
            });
            // Add timeout for initialization
            setTimeout(() => {
                if (!this.isInitialized) {
                    this.messageHandlers.delete(messageId);
                    reject(new Error("Worker initialization timeout"));
                }
            }, 5000); // 5 second timeout
        });
    }
    start(gameUpdate) {
        if (!this.isInitialized) {
            throw new Error("Failed to initialize pathfinder");
        }
        this.gameUpdateCallback = gameUpdate;
    }
    sendTurn(turn) {
        if (!this.isInitialized) {
            throw new Error("Worker not initialized");
        }
        this.worker.postMessage({
            type: "turn",
            turn,
        });
    }
    sendHeartbeat() {
        this.worker.postMessage({
            type: "heartbeat",
        });
    }
    playerProfile(playerID) {
        return new Promise((resolve, reject) => {
            if (!this.isInitialized) {
                reject(new Error("Worker not initialized"));
                return;
            }
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "player_profile_result" &&
                    message.result !== undefined) {
                    resolve(message.result);
                }
            });
            this.worker.postMessage({
                type: "player_profile",
                id: messageId,
                playerID: playerID,
            });
        });
    }
    playerBorderTiles(playerID) {
        return new Promise((resolve, reject) => {
            if (!this.isInitialized) {
                reject(new Error("Worker not initialized"));
                return;
            }
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "player_border_tiles_result" &&
                    message.result !== undefined) {
                    resolve(message.result);
                }
            });
            this.worker.postMessage({
                type: "player_border_tiles",
                id: messageId,
                playerID: playerID,
            });
        });
    }
    playerInteraction(playerID, x, y) {
        return new Promise((resolve, reject) => {
            if (!this.isInitialized) {
                reject(new Error("Worker not initialized"));
                return;
            }
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "player_actions_result" &&
                    message.result !== undefined) {
                    resolve(message.result);
                }
            });
            this.worker.postMessage({
                type: "player_actions",
                id: messageId,
                playerID: playerID,
                x: x,
                y: y,
            });
        });
    }
    attackAveragePosition(playerID, attackID) {
        return new Promise((resolve, reject) => {
            if (!this.isInitialized) {
                reject(new Error("Worker not initialized"));
                return;
            }
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "attack_average_position_result" &&
                    message.x !== undefined &&
                    message.y !== undefined) {
                    if (message.x === null || message.y === null) {
                        resolve(null);
                    }
                    else {
                        resolve(new Game_1.Cell(message.x, message.y));
                    }
                }
            });
            this.worker.postMessage({
                type: "attack_average_position",
                id: messageId,
                playerID: playerID,
                attackID: attackID,
            });
        });
    }
    transportShipSpawn(playerID, targetTile) {
        return new Promise((resolve, reject) => {
            if (!this.isInitialized) {
                reject(new Error("Worker not initialized"));
                return;
            }
            const messageId = (0, Util_1.generateID)();
            this.messageHandlers.set(messageId, (message) => {
                if (message.type === "transport_ship_spawn_result" &&
                    message.result !== undefined) {
                    resolve(message.result);
                }
            });
            this.worker.postMessage({
                type: "transport_ship_spawn",
                id: messageId,
                playerID: playerID,
                targetTile: targetTile,
            });
        });
    }
    cleanup() {
        this.worker.terminate();
        this.messageHandlers.clear();
        this.gameUpdateCallback = undefined;
    }
}
exports.WorkerClient = WorkerClient;
