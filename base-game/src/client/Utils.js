import IntlMessageFormat from "intl-messageformat";
import { MessageType } from "../core/game/Game";
export function renderDuration(totalSeconds) {
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
export function renderTroops(troops) {
    return renderNumber(troops / 10);
}
export function renderNumber(num, fixedPoints) {
    num = Number(num);
    num = Math.max(num, 0);
    if (num >= 10000000) {
        const value = Math.floor(num / 100000) / 10;
        return value.toFixed(fixedPoints ?? 1) + "M";
    }
    else if (num >= 1000000) {
        const value = Math.floor(num / 10000) / 100;
        return value.toFixed(fixedPoints ?? 2) + "M";
    }
    else if (num >= 100000) {
        return Math.floor(num / 1000) + "K";
    }
    else if (num >= 10000) {
        const value = Math.floor(num / 100) / 10;
        return value.toFixed(fixedPoints ?? 1) + "K";
    }
    else if (num >= 1000) {
        const value = Math.floor(num / 10) / 100;
        return value.toFixed(fixedPoints ?? 2) + "K";
    }
    else {
        return Math.floor(num).toString();
    }
}
export function createCanvas() {
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
export function generateCryptoRandomUUID() {
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
export const translateText = (key, params = {}) => {
    const self = translateText;
    self.formatterCache ?? (self.formatterCache = new Map());
    self.lastLang ?? (self.lastLang = null);
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
            formatter = new IntlMessageFormat(message, locale);
            self.formatterCache.set(cacheKey, formatter);
        }
        return formatter.format(params);
    }
    catch (e) {
        console.warn("ICU format error", e);
        return message;
    }
};
/**
 * Severity colors mapping for message types
 */
export const severityColors = {
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
export function getMessageTypeClasses(type) {
    switch (type) {
        case MessageType.SAM_HIT:
        case MessageType.CAPTURED_ENEMY_UNIT:
        case MessageType.RECEIVED_GOLD_FROM_TRADE:
        case MessageType.CONQUERED_PLAYER:
            return severityColors["success"];
        case MessageType.ATTACK_FAILED:
        case MessageType.ALLIANCE_REJECTED:
        case MessageType.ALLIANCE_BROKEN:
        case MessageType.UNIT_CAPTURED_BY_ENEMY:
        case MessageType.UNIT_DESTROYED:
            return severityColors["fail"];
        case MessageType.ATTACK_CANCELLED:
        case MessageType.ATTACK_REQUEST:
        case MessageType.ALLIANCE_ACCEPTED:
        case MessageType.SENT_GOLD_TO_PLAYER:
        case MessageType.SENT_TROOPS_TO_PLAYER:
        case MessageType.RECEIVED_GOLD_FROM_PLAYER:
        case MessageType.RECEIVED_TROOPS_FROM_PLAYER:
            return severityColors["blue"];
        case MessageType.MIRV_INBOUND:
        case MessageType.NUKE_INBOUND:
        case MessageType.HYDROGEN_BOMB_INBOUND:
        case MessageType.SAM_MISS:
        case MessageType.ALLIANCE_EXPIRED:
        case MessageType.NAVAL_INVASION_INBOUND:
        case MessageType.RENEW_ALLIANCE:
            return severityColors["warn"];
        case MessageType.CHAT:
        case MessageType.ALLIANCE_REQUEST:
            return severityColors["info"];
        default:
            console.warn(`Message type ${type} has no explicit color`);
            return severityColors["white"];
    }
}
export function getModifierKey() {
    const isMac = /Mac/.test(navigator.userAgent);
    if (isMac) {
        return "⌘"; // Command key
    }
    else {
        return "Ctrl";
    }
}
export function getAltKey() {
    const isMac = /Mac/.test(navigator.userAgent);
    if (isMac) {
        return "⌥"; // Option key
    }
    else {
        return "Alt";
    }
}
export function getGamesPlayed() {
    try {
        return parseInt(localStorage.getItem("gamesPlayed") ?? "0", 10) || 0;
    }
    catch (error) {
        console.warn("Failed to read games played from localStorage:", error);
        return 0;
    }
}
export function incrementGamesPlayed() {
    try {
        localStorage.setItem("gamesPlayed", (getGamesPlayed() + 1).toString());
    }
    catch (error) {
        console.warn("Failed to increment games played in localStorage:", error);
    }
}
