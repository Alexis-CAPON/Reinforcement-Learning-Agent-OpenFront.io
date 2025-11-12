"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ColorAllocator = void 0;
exports.selectDistinctColorIndex = selectDistinctColorIndex;
const colord_1 = require("colord");
const lab_1 = require("colord/plugins/lab");
const lch_1 = require("colord/plugins/lch");
const colorjs_io_1 = require("colorjs.io");
const Game_1 = require("../game/Game");
const PseudoRandom_1 = require("../PseudoRandom");
const Util_1 = require("../Util");
const Colors_1 = require("./Colors");
(0, colord_1.extend)([lch_1.default]);
(0, colord_1.extend)([lab_1.default]);
class ColorAllocator {
    constructor(colors, fallback) {
        this.assigned = new Map();
        this.teamPlayerColors = new Map();
        this.availableColors = [...colors];
        this.fallbackColors = [...colors, ...fallback];
    }
    getTeamColorVariations(team) {
        switch (team) {
            case Game_1.ColoredTeams.Blue:
                return Colors_1.blueTeamColors;
            case Game_1.ColoredTeams.Red:
                return Colors_1.redTeamColors;
            case Game_1.ColoredTeams.Teal:
                return Colors_1.tealTeamColors;
            case Game_1.ColoredTeams.Purple:
                return Colors_1.purpleTeamColors;
            case Game_1.ColoredTeams.Yellow:
                return Colors_1.yellowTeamColors;
            case Game_1.ColoredTeams.Orange:
                return Colors_1.orangeTeamColors;
            case Game_1.ColoredTeams.Green:
                return Colors_1.greenTeamColors;
            case Game_1.ColoredTeams.Bot:
                return Colors_1.botTeamColors;
            default:
                return [this.assignColor(team)];
        }
    }
    assignColor(id) {
        var _a;
        if (this.assigned.has(id)) {
            return this.assigned.get(id);
        }
        if (this.availableColors.length === 0) {
            this.availableColors = [...this.fallbackColors];
        }
        let selectedIndex = 0;
        if (this.assigned.size === 0 || this.assigned.size > 50) {
            // Randomly pick the first color if no colors have been assigned yet.
            //
            // Or if more than 50 colors assigned just pick a random one for perf reasons,
            // as selecting a distinct color is O(n^2), and the color palette is mostly exhausted anyways.
            const rand = new PseudoRandom_1.PseudoRandom((0, Util_1.simpleHash)(id));
            selectedIndex = rand.nextInt(0, this.availableColors.length);
        }
        else {
            const assignedColors = Array.from(this.assigned.values());
            selectedIndex =
                (_a = selectDistinctColorIndex(this.availableColors, assignedColors)) !== null && _a !== void 0 ? _a : 0;
        }
        const color = this.availableColors.splice(selectedIndex, 1)[0];
        this.assigned.set(id, color);
        return color;
    }
    assignTeamColor(team) {
        const teamColors = this.getTeamColorVariations(team);
        return teamColors[0];
    }
    assignTeamPlayerColor(team, playerId) {
        if (this.teamPlayerColors.has(playerId)) {
            return this.teamPlayerColors.get(playerId);
        }
        const teamColors = this.getTeamColorVariations(team);
        const hashValue = (0, Util_1.simpleHash)(playerId);
        const colorIndex = hashValue % teamColors.length;
        const color = teamColors[colorIndex];
        this.teamPlayerColors.set(playerId, color);
        return color;
    }
}
exports.ColorAllocator = ColorAllocator;
// Select a distinct color index from the available colors that
// is most different from the assigned colors
function selectDistinctColorIndex(availableColors, assignedColors) {
    if (assignedColors.length === 0) {
        throw new Error("No assigned colors");
    }
    const assignedLabColors = assignedColors.map(toColor);
    let maxDeltaE = 0;
    let maxIndex = 0;
    for (let i = 0; i < availableColors.length; i++) {
        const color = availableColors[i];
        const deltaE = minDeltaE(toColor(color), assignedLabColors);
        if (deltaE > maxDeltaE) {
            maxDeltaE = deltaE;
            maxIndex = i;
        }
    }
    return maxIndex;
}
function minDeltaE(lab1, assignedLabColors) {
    return assignedLabColors.reduce((min, assigned) => {
        return Math.min(min, deltaE2000(lab1, assigned));
    }, Infinity);
}
function deltaE2000(c1, c2) {
    return c1.deltaE(c2, "2000");
}
function toColor(colord) {
    const lab = colord.toLab();
    return new colorjs_io_1.default("lab", [lab.l, lab.a, lab.b]);
}
