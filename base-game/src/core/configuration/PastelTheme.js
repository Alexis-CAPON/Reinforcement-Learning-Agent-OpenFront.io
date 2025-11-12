"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PastelTheme = void 0;
const colord_1 = require("colord");
const PseudoRandom_1 = require("../PseudoRandom");
const Game_1 = require("../game/Game");
const ColorAllocator_1 = require("./ColorAllocator");
const Colors_1 = require("./Colors");
class PastelTheme {
    constructor() {
        this.borderColorCache = new Map();
        this.rand = new PseudoRandom_1.PseudoRandom(123);
        this.humanColorAllocator = new ColorAllocator_1.ColorAllocator(Colors_1.humanColors, Colors_1.fallbackColors);
        this.botColorAllocator = new ColorAllocator_1.ColorAllocator(Colors_1.botColors, Colors_1.botColors);
        this.teamColorAllocator = new ColorAllocator_1.ColorAllocator(Colors_1.humanColors, Colors_1.fallbackColors);
        this.nationColorAllocator = new ColorAllocator_1.ColorAllocator(Colors_1.nationColors, Colors_1.nationColors);
        this.background = (0, colord_1.colord)({ r: 60, g: 60, b: 60 });
        this.shore = (0, colord_1.colord)({ r: 204, g: 203, b: 158 });
        this.falloutColors = [
            (0, colord_1.colord)({ r: 120, g: 255, b: 71 }), // Original color
            (0, colord_1.colord)({ r: 130, g: 255, b: 85 }), // Slightly lighter
            (0, colord_1.colord)({ r: 110, g: 245, b: 65 }), // Slightly darker
            (0, colord_1.colord)({ r: 125, g: 255, b: 75 }), // Warmer tint
            (0, colord_1.colord)({ r: 115, g: 250, b: 68 }), // Cooler tint
        ];
        this.water = (0, colord_1.colord)({ r: 70, g: 132, b: 180 });
        this.shorelineWater = (0, colord_1.colord)({ r: 100, g: 143, b: 255 });
        this._selfColor = (0, colord_1.colord)({ r: 0, g: 255, b: 0 });
        this._allyColor = (0, colord_1.colord)({ r: 255, g: 255, b: 0 });
        this._neutralColor = (0, colord_1.colord)({ r: 128, g: 128, b: 128 });
        this._enemyColor = (0, colord_1.colord)({ r: 255, g: 0, b: 0 });
        this._spawnHighlightColor = (0, colord_1.colord)({ r: 255, g: 213, b: 79 });
    }
    teamColor(team) {
        return this.teamColorAllocator.assignTeamColor(team);
    }
    territoryColor(player) {
        const team = player.team();
        if (team !== null) {
            return this.teamColorAllocator.assignTeamPlayerColor(team, player.id());
        }
        if (player.type() === Game_1.PlayerType.Human) {
            return this.humanColorAllocator.assignColor(player.id());
        }
        if (player.type() === Game_1.PlayerType.Bot) {
            return this.botColorAllocator.assignColor(player.id());
        }
        return this.nationColorAllocator.assignColor(player.id());
    }
    textColor(player) {
        return player.type() === Game_1.PlayerType.Human ? "#000000" : "#4D4D4D";
    }
    specialBuildingColor(player) {
        const tc = this.territoryColor(player).rgba;
        return (0, colord_1.colord)({
            r: Math.max(tc.r - 50, 0),
            g: Math.max(tc.g - 50, 0),
            b: Math.max(tc.b - 50, 0),
        });
    }
    railroadColor(player) {
        const tc = this.territoryColor(player).rgba;
        const color = (0, colord_1.colord)({
            r: Math.max(tc.r - 10, 0),
            g: Math.max(tc.g - 10, 0),
            b: Math.max(tc.b - 10, 0),
        });
        return color;
    }
    borderColor(player) {
        if (this.borderColorCache.has(player.id())) {
            return this.borderColorCache.get(player.id());
        }
        const tc = this.territoryColor(player).rgba;
        const color = (0, colord_1.colord)({
            r: Math.max(tc.r - 40, 0),
            g: Math.max(tc.g - 40, 0),
            b: Math.max(tc.b - 40, 0),
        });
        this.borderColorCache.set(player.id(), color);
        return color;
    }
    defendedBorderColors(player) {
        return {
            light: this.territoryColor(player).darken(0.2),
            dark: this.territoryColor(player).darken(0.4),
        };
    }
    focusedBorderColor() {
        return (0, colord_1.colord)({ r: 230, g: 230, b: 230 });
    }
    terrainColor(gm, tile) {
        const mag = gm.magnitude(tile);
        if (gm.isShore(tile)) {
            return this.shore;
        }
        switch (gm.terrainType(tile)) {
            case Game_1.TerrainType.Ocean:
            case Game_1.TerrainType.Lake:
                const w = this.water.rgba;
                if (gm.isShoreline(tile) && gm.isWater(tile)) {
                    return this.shorelineWater;
                }
                return (0, colord_1.colord)({
                    r: Math.max(w.r - 10 + (11 - Math.min(mag, 10)), 0),
                    g: Math.max(w.g - 10 + (11 - Math.min(mag, 10)), 0),
                    b: Math.max(w.b - 10 + (11 - Math.min(mag, 10)), 0),
                });
            case Game_1.TerrainType.Plains:
                return (0, colord_1.colord)({
                    r: 190,
                    g: 220 - 2 * mag,
                    b: 138,
                });
            case Game_1.TerrainType.Highland:
                return (0, colord_1.colord)({
                    r: 200 + 2 * mag,
                    g: 183 + 2 * mag,
                    b: 138 + 2 * mag,
                });
            case Game_1.TerrainType.Mountain:
                return (0, colord_1.colord)({
                    r: 230 + mag / 2,
                    g: 230 + mag / 2,
                    b: 230 + mag / 2,
                });
        }
    }
    backgroundColor() {
        return this.background;
    }
    falloutColor() {
        return this.rand.randElement(this.falloutColors);
    }
    font() {
        return "Overpass, sans-serif";
    }
    selfColor() {
        return this._selfColor;
    }
    allyColor() {
        return this._allyColor;
    }
    neutralColor() {
        return this._neutralColor;
    }
    enemyColor() {
        return this._enemyColor;
    }
    spawnHighlightColor() {
        return this._spawnHighlightColor;
    }
}
exports.PastelTheme = PastelTheme;
