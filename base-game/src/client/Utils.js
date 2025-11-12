"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.severityColors = exports.translateText = void 0;
exports.renderDuration = renderDuration;
exports.renderTroops = renderTroops;
exports.renderNumber = renderNumber;
exports.createCanvas = createCanvas;
exports.generateCryptoRandomUUID = generateCryptoRandomUUID;
exports.getMessageTypeClasses = getMessageTypeClasses;
exports.getModifierKey = getModifierKey;
exports.getAltKey = getAltKey;
exports.getGamesPlayed = getGamesPlayed;
exports.incrementGamesPlayed = incrementGamesPlayed;
const intl_messageformat_1 = require("intl-messageformat");
const Game_1 = require("../core/game/Game");
function renderDuration(totalSeconds) {
    if (totalSeconds <= 0)
        return "0s";
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    let time = "";
    if (minutes > 0)
        time += `${minutes}min `;
    time += `${seconds}s`;
    return time.trim();
}
function renderTroops(troops) {
    return renderNumber(troops / 10);
}
function renderNumber(num, fixedPoints) {
    num = Number(num);
    num = Math.max(num, 0);
    if (num >= 10000000) {
        const value = Math.floor(num / 100000) / 10;
        return value.toFixed(fixedPoints !== null && fixedPoints !== void 0 ? fixedPoints : 1) + "M";
    }
    else if (num >= 1000000) {
        const value = Math.floor(num / 10000) / 100;
        return value.toFixed(fixedPoints !== null && fixedPoints !== void 0 ? fixedPoints : 2) + "M";
    }
    else if (num >= 100000) {
        return Math.floor(num / 1000) + "K";
    }
    else if (num >= 10000) {
        const value = Math.floor(num / 100) / 10;
        return value.toFixed(fixedPoints !== null && fixedPoints !== void 0 ? fixedPoints : 1) + "K";
    }
    else if (num >= 1000) {
        const value = Math.floor(num / 10) / 100;
        return value.toFixed(fixedPoints !== null && fixedPoints !== void 0 ? fixedPoints : 2) + "K";
    }
    else {
        return Math.floor(num).toString();
    }
}
function createCanvas() {
    const canvas = document.createElement("canvas");
    // Set canvas style to fill the screen
    canvas.style.position = "fixed";
    canvas.style.left = "0";
    canvas.style.top = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.touchAction = "none";
    return canvas;
}
/**
 * A polyfill for crypto.randomUUID that provides fallback implementations
 * for older browsers, particularly Safari versions < 15.4
 */
function generateCryptoRandomUUID() {
    // Type guard to check if randomUUID is available
    if (crypto !== undefined && "randomUUID" in crypto) {
        return crypto.randomUUID();
    }
    // Fallback using crypto.getRandomValues
    if (crypto !== undefined && "getRandomValues" in crypto) {
        return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) => (c ^
            (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16));
    }
    // Last resort fallback using Math.random
    // Note: This is less cryptographically secure but ensures functionality
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}
const translateText = (key, params = {}) => {
    var _a, _b;
    const self = exports.translateText;
    (_a = self.formatterCache) !== null && _a !== void 0 ? _a : (self.formatterCache = new Map());
    (_b = self.lastLang) !== null && _b !== void 0 ? _b : (self.lastLang = null);
    const langSelector = document.querySelector("lang-selector");
    if (!langSelector) {
        console.warn("LangSelector not found in DOM");
        return key;
    }
    if (!langSelector.translations ||
        Object.keys(langSelector.translations).length === 0) {
        return key;
    }
    if (self.lastLang !== langSelector.currentLang) {
        self.formatterCache.clear();
        self.lastLang = langSelector.currentLang;
    }
    let message = langSelector.translations[key];
    if (!message && langSelector.defaultTranslations) {
        const defaultTranslations = langSelector.defaultTranslations;
        if (defaultTranslations && defaultTranslations[key]) {
            message = defaultTranslations[key];
        }
    }
    if (!message)
        return key;
    try {
        const locale = !langSelector.translations[key] && langSelector.currentLang !== "en"
            ? "en"
            : langSelector.currentLang;
        const cacheKey = `${key}:${locale}:${message}`;
        let formatter = self.formatterCache.get(cacheKey);
        if (!formatter) {
            formatter = new intl_messageformat_1.default(message, locale);
            self.formatterCache.set(cacheKey, formatter);
        }
        return formatter.format(params);
    }
    catch (e) {
        console.warn("ICU format error", e);
        return message;
    }
};
exports.translateText = translateText;
/**
 * Severity colors mapping for message types
 */
exports.severityColors = {
    fail: "text-red-400",
    warn: "text-yellow-400",
    success: "text-green-400",
    info: "text-gray-200",
    blue: "text-blue-400",
    white: "text-white",
};
/**
 * Gets the CSS classes for styling message types based on their severity
 * @param type The message type to get styling for
 * @returns CSS class string for the message type
 */
function getMessageTypeClasses(type) {
    switch (type) {
        case Game_1.MessageType.SAM_HIT:
        case Game_1.MessageType.CAPTURED_ENEMY_UNIT:
        case Game_1.MessageType.RECEIVED_GOLD_FROM_TRADE:
        case Game_1.MessageType.CONQUERED_PLAYER:
            return exports.severityColors["success"];
        case Game_1.MessageType.ATTACK_FAILED:
        case Game_1.MessageType.ALLIANCE_REJECTED:
        case Game_1.MessageType.ALLIANCE_BROKEN:
        case Game_1.MessageType.UNIT_CAPTURED_BY_ENEMY:
        case Game_1.MessageType.UNIT_DESTROYED:
            return exports.severityColors["fail"];
        case Game_1.MessageType.ATTACK_CANCELLED:
        case Game_1.MessageType.ATTACK_REQUEST:
        case Game_1.MessageType.ALLIANCE_ACCEPTED:
        case Game_1.MessageType.SENT_GOLD_TO_PLAYER:
        case Game_1.MessageType.SENT_TROOPS_TO_PLAYER:
        case Game_1.MessageType.RECEIVED_GOLD_FROM_PLAYER:
        case Game_1.MessageType.RECEIVED_TROOPS_FROM_PLAYER:
            return exports.severityColors["blue"];
        case Game_1.MessageType.MIRV_INBOUND:
        case Game_1.MessageType.NUKE_INBOUND:
        case Game_1.MessageType.HYDROGEN_BOMB_INBOUND:
        case Game_1.MessageType.SAM_MISS:
        case Game_1.MessageType.ALLIANCE_EXPIRED:
        case Game_1.MessageType.NAVAL_INVASION_INBOUND:
        case Game_1.MessageType.RENEW_ALLIANCE:
            return exports.severityColors["warn"];
        case Game_1.MessageType.CHAT:
        case Game_1.MessageType.ALLIANCE_REQUEST:
            return exports.severityColors["info"];
        default:
            console.warn(`Message type ${type} has no explicit color`);
            return exports.severityColors["white"];
    }
}
function getModifierKey() {
    const isMac = /Mac/.test(navigator.userAgent);
    if (isMac) {
        return "⌘"; // Command key
    }
    else {
        return "Ctrl";
    }
}
function getAltKey() {
    const isMac = /Mac/.test(navigator.userAgent);
    if (isMac) {
        return "⌥"; // Option key
    }
    else {
        return "Alt";
    }
}
function getGamesPlayed() {
    var _a;
    try {
        return parseInt((_a = localStorage.getItem("gamesPlayed")) !== null && _a !== void 0 ? _a : "0", 10) || 0;
    }
    catch (error) {
        console.warn("Failed to read games played from localStorage:", error);
        return 0;
    }
}
function incrementGamesPlayed() {
    try {
        localStorage.setItem("gamesPlayed", (getGamesPlayed() + 1).toString());
    }
    catch (error) {
        console.warn("Failed to increment games played in localStorage:", error);
    }
}
