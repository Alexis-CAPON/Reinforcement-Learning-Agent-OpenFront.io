import { colord } from "colord";
import { PseudoRandom } from "../PseudoRandom";
import { PlayerType, TerrainType } from "../game/Game";
import { ColorAllocator } from "./ColorAllocator";
import { botColors, fallbackColors, humanColors, nationColors } from "./Colors";
export class PastelThemeDark {
    constructor() {
        this.borderColorCache = new Map();
        this.rand = new PseudoRandom(123);
        this.humanColorAllocator = new ColorAllocator(humanColors, fallbackColors);
        this.botColorAllocator = new ColorAllocator(botColors, botColors);
        this.teamColorAllocator = new ColorAllocator(humanColors, fallbackColors);
        this.nationColorAllocator = new ColorAllocator(nationColors, nationColors);
        this.background = colord({ r: 0, g: 0, b: 0 });
        this.shore = colord({ r: 134, g: 133, b: 88 });
        this.falloutColors = [
            colord({ r: 120, g: 255, b: 71 }), // Original color
            colord({ r: 130, g: 255, b: 85 }), // Slightly lighter
            colord({ r: 110, g: 245, b: 65 }), // Slightly darker
            colord({ r: 125, g: 255, b: 75 }), // Warmer tint
            colord({ r: 115, g: 250, b: 68 }), // Cooler tint
        ];
        this.water = colord({ r: 14, g: 11, b: 30 });
        this.shorelineWater = colord({ r: 50, g: 50, b: 50 });
        this._selfColor = colord({ r: 0, g: 255, b: 0 });
        this._allyColor = colord({ r: 255, g: 255, b: 0 });
        this._neutralColor = colord({ r: 128, g: 128, b: 128 });
        this._enemyColor = colord({ r: 255, g: 0, b: 0 });
        this._spawnHighlightColor = colord({ r: 255, g: 213, b: 79 });
    }
    teamColor(team) {
        return this.teamColorAllocator.assignTeamColor(team);
    }
    territoryColor(player) {
        const team = player.team();
        if (team !== null) {
            return this.teamColorAllocator.assignTeamPlayerColor(team, player.id());
        }
        if (player.type() === PlayerType.Human) {
            return this.humanColorAllocator.assignColor(player.id());
        }
        if (player.type() === PlayerType.Bot) {
            return this.botColorAllocator.assignColor(player.id());
        }
        return this.nationColorAllocator.assignColor(player.id());
    }
    textColor(player) {
        return player.type() === PlayerType.Human ? "#ffffff" : "#e6e6e6";
    }
    specialBuildingColor(player) {
        const tc = this.territoryColor(player).rgba;
        return colord({
            r: Math.max(tc.r - 50, 0),
            g: Math.max(tc.g - 50, 0),
            b: Math.max(tc.b - 50, 0),
        });
    }
    railroadColor(player) {
        const tc = this.territoryColor(player).rgba;
        const color = colord({
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
        const color = colord({
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
        return colord({ r: 255, g: 255, b: 255 });
    }
    terrainColor(gm, tile) {
        const mag = gm.magnitude(tile);
        if (gm.isShore(tile)) {
            return this.shore;
        }
        switch (gm.terrainType(tile)) {
            case TerrainType.Ocean:
            case TerrainType.Lake:
                const w = this.water.rgba;
                if (gm.isShoreline(tile) && gm.isWater(tile)) {
                    return this.shorelineWater;
                }
                if (gm.magnitude(tile) < 10) {
                    return colord({
                        r: Math.max(w.r + 9 - mag, 0),
                        g: Math.max(w.g + 9 - mag, 0),
                        b: Math.max(w.b + 9 - mag, 0),
                    });
                }
                return this.water;
            case TerrainType.Plains:
                return colord({
                    r: 140,
                    g: 170 - 2 * mag,
                    b: 88,
                });
            case TerrainType.Highland:
                return colord({
                    r: 150 + 2 * mag,
                    g: 133 + 2 * mag,
                    b: 88 + 2 * mag,
                });
            case TerrainType.Mountain:
                return colord({
                    r: 180 + mag / 2,
                    g: 180 + mag / 2,
                    b: 180 + mag / 2,
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
