"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UserSettings = void 0;
const PATTERN_KEY = "territoryPattern";
class UserSettings {
    get(key, defaultValue) {
        const value = localStorage.getItem(key);
        if (!value)
            return defaultValue;
        if (value === "true")
            return true;
        if (value === "false")
            return false;
        return defaultValue;
    }
    set(key, value) {
        localStorage.setItem(key, value ? "true" : "false");
    }
    emojis() {
        return this.get("settings.emojis", true);
    }
    performanceOverlay() {
        return this.get("settings.performanceOverlay", false);
    }
    alertFrame() {
        return this.get("settings.alertFrame", true);
    }
    anonymousNames() {
        return this.get("settings.anonymousNames", false);
    }
    lobbyIdVisibility() {
        return this.get("settings.lobbyIdVisibility", true);
    }
    fxLayer() {
        return this.get("settings.specialEffects", true);
    }
    structureSprites() {
        return this.get("settings.structureSprites", true);
    }
    darkMode() {
        return this.get("settings.darkMode", false);
    }
    leftClickOpensMenu() {
        return this.get("settings.leftClickOpensMenu", false);
    }
    territoryPatterns() {
        return this.get("settings.territoryPatterns", true);
    }
    focusLocked() {
        return false;
        // TODO: renable when performance issues are fixed.
        this.get("settings.focusLocked", true);
    }
    toggleLeftClickOpenMenu() {
        this.set("settings.leftClickOpensMenu", !this.leftClickOpensMenu());
    }
    toggleFocusLocked() {
        this.set("settings.focusLocked", !this.focusLocked());
    }
    toggleEmojis() {
        this.set("settings.emojis", !this.emojis());
    }
    togglePerformanceOverlay() {
        this.set("settings.performanceOverlay", !this.performanceOverlay());
    }
    toggleAlertFrame() {
        this.set("settings.alertFrame", !this.alertFrame());
    }
    toggleRandomName() {
        this.set("settings.anonymousNames", !this.anonymousNames());
    }
    toggleLobbyIdVisibility() {
        this.set("settings.lobbyIdVisibility", !this.lobbyIdVisibility());
    }
    toggleFxLayer() {
        this.set("settings.specialEffects", !this.fxLayer());
    }
    toggleStructureSprites() {
        this.set("settings.structureSprites", !this.structureSprites());
    }
    toggleTerritoryPatterns() {
        this.set("settings.territoryPatterns", !this.territoryPatterns());
    }
    toggleDarkMode() {
        this.set("settings.darkMode", !this.darkMode());
        if (this.darkMode()) {
            document.documentElement.classList.add("dark");
        }
        else {
            document.documentElement.classList.remove("dark");
        }
    }
    // For development only. Used for testing patterns, set in the console manually.
    getDevOnlyPattern() {
        var _a;
        return (_a = localStorage.getItem("dev-pattern")) !== null && _a !== void 0 ? _a : undefined;
    }
    getSelectedPatternName() {
        var _a;
        return (_a = localStorage.getItem(PATTERN_KEY)) !== null && _a !== void 0 ? _a : undefined;
    }
    setSelectedPatternName(patternName) {
        if (patternName === undefined) {
            localStorage.removeItem(PATTERN_KEY);
        }
        else {
            localStorage.setItem(PATTERN_KEY, patternName);
        }
    }
}
exports.UserSettings = UserSettings;
