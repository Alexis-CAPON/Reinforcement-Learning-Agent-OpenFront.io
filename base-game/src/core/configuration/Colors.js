"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.fallbackColors = exports.botColors = exports.humanColors = exports.nationColors = exports.botTeamColors = exports.greenTeamColors = exports.orangeTeamColors = exports.yellowTeamColors = exports.purpleTeamColors = exports.tealTeamColors = exports.blueTeamColors = exports.redTeamColors = exports.botColor = exports.green = exports.orange = exports.yellow = exports.purple = exports.teal = exports.blue = exports.red = void 0;
const colord_1 = require("colord");
const lab_1 = require("colord/plugins/lab");
const lch_1 = require("colord/plugins/lch");
(0, colord_1.extend)([lch_1.default]);
(0, colord_1.extend)([lab_1.default]);
exports.red = (0, colord_1.colord)({ h: 0, s: 82, l: 56 });
exports.blue = (0, colord_1.colord)({ h: 224, s: 100, l: 58 });
exports.teal = (0, colord_1.colord)({ h: 172, s: 66, l: 50 });
exports.purple = (0, colord_1.colord)({ h: 271, s: 81, l: 56 });
exports.yellow = (0, colord_1.colord)({ h: 45, s: 93, l: 47 });
exports.orange = (0, colord_1.colord)({ h: 25, s: 95, l: 53 });
exports.green = (0, colord_1.colord)({ h: 128, s: 49, l: 50 });
exports.botColor = (0, colord_1.colord)({ h: 36, s: 10, l: 80 });
exports.redTeamColors = generateTeamColors(exports.red);
exports.blueTeamColors = generateTeamColors(exports.blue);
exports.tealTeamColors = generateTeamColors(exports.teal);
exports.purpleTeamColors = generateTeamColors(exports.purple);
exports.yellowTeamColors = generateTeamColors(exports.yellow);
exports.orangeTeamColors = generateTeamColors(exports.orange);
exports.greenTeamColors = generateTeamColors(exports.green);
exports.botTeamColors = [(0, colord_1.colord)(exports.botColor)];
function generateTeamColors(baseColor) {
    const { h: baseHue, s: baseSaturation, l: baseLightness } = baseColor.toHsl();
    const colorCount = 64;
    return Array.from({ length: colorCount }, (_, index) => {
        const progression = index / (colorCount - 1);
        const saturation = baseSaturation * (1.0 - 0.3 * progression);
        const lightness = Math.min(100, baseLightness + progression * 30);
        return (0, colord_1.colord)({
            h: baseHue,
            s: saturation,
            l: lightness,
        });
    });
}
exports.nationColors = [
    (0, colord_1.colord)({ r: 230, g: 100, b: 100 }), // Bright Red
    (0, colord_1.colord)({ r: 100, g: 180, b: 230 }), // Sky Blue
    (0, colord_1.colord)({ r: 230, g: 180, b: 80 }), // Golden Yellow
    (0, colord_1.colord)({ r: 180, g: 100, b: 230 }), // Purple
    (0, colord_1.colord)({ r: 80, g: 200, b: 120 }), // Emerald Green
    (0, colord_1.colord)({ r: 230, g: 130, b: 180 }), // Pink
    (0, colord_1.colord)({ r: 100, g: 160, b: 80 }), // Olive Green
    (0, colord_1.colord)({ r: 230, g: 150, b: 100 }), // Peach
    (0, colord_1.colord)({ r: 80, g: 130, b: 190 }), // Navy Blue
    (0, colord_1.colord)({ r: 210, g: 210, b: 100 }), // Lime Yellow
    (0, colord_1.colord)({ r: 190, g: 100, b: 130 }), // Maroon
    (0, colord_1.colord)({ r: 100, g: 210, b: 210 }), // Turquoise
    (0, colord_1.colord)({ r: 210, g: 140, b: 80 }), // Light Orange
    (0, colord_1.colord)({ r: 150, g: 110, b: 190 }), // Lavender
    (0, colord_1.colord)({ r: 180, g: 210, b: 120 }), // Light Green
    (0, colord_1.colord)({ r: 210, g: 100, b: 160 }), // Hot Pink
    (0, colord_1.colord)({ r: 100, g: 140, b: 110 }), // Sea Green
    (0, colord_1.colord)({ r: 230, g: 180, b: 180 }), // Light Pink
    (0, colord_1.colord)({ r: 120, g: 120, b: 190 }), // Periwinkle
    (0, colord_1.colord)({ r: 190, g: 170, b: 100 }), // Sand
    (0, colord_1.colord)({ r: 100, g: 180, b: 160 }), // Aquamarine
    (0, colord_1.colord)({ r: 210, g: 160, b: 200 }), // Orchid
    (0, colord_1.colord)({ r: 170, g: 190, b: 100 }), // Yellow Green
    (0, colord_1.colord)({ r: 100, g: 130, b: 150 }), // Steel Blue
    (0, colord_1.colord)({ r: 230, g: 140, b: 140 }), // Salmon
    (0, colord_1.colord)({ r: 140, g: 180, b: 220 }), // Light Blue
    (0, colord_1.colord)({ r: 200, g: 160, b: 110 }), // Tan
    (0, colord_1.colord)({ r: 180, g: 130, b: 180 }), // Plum
    (0, colord_1.colord)({ r: 130, g: 200, b: 130 }), // Light Sea Green
    (0, colord_1.colord)({ r: 220, g: 120, b: 120 }), // Coral
    (0, colord_1.colord)({ r: 120, g: 160, b: 200 }), // Cornflower Blue
    (0, colord_1.colord)({ r: 200, g: 200, b: 140 }), // Khaki
    (0, colord_1.colord)({ r: 160, g: 120, b: 160 }), // Purple Gray
    (0, colord_1.colord)({ r: 140, g: 180, b: 140 }), // Dark Sea Green
    (0, colord_1.colord)({ r: 200, g: 130, b: 110 }), // Dark Salmon
    (0, colord_1.colord)({ r: 130, g: 170, b: 190 }), // Cadet Blue
    (0, colord_1.colord)({ r: 190, g: 180, b: 160 }), // Tan Gray
    (0, colord_1.colord)({ r: 170, g: 140, b: 190 }), // Medium Purple
    (0, colord_1.colord)({ r: 160, g: 190, b: 160 }), // Pale Green
    (0, colord_1.colord)({ r: 190, g: 150, b: 130 }), // Rosy Brown
    (0, colord_1.colord)({ r: 140, g: 150, b: 180 }), // Light Slate Gray
    (0, colord_1.colord)({ r: 180, g: 170, b: 140 }), // Dark Khaki
    (0, colord_1.colord)({ r: 150, g: 130, b: 150 }), // Thistle
    (0, colord_1.colord)({ r: 170, g: 190, b: 180 }), // Pale Blue Green
    (0, colord_1.colord)({ r: 190, g: 140, b: 150 }), // Puce
    (0, colord_1.colord)({ r: 130, g: 180, b: 170 }), // Medium Aquamarine
    (0, colord_1.colord)({ r: 180, g: 160, b: 180 }), // Mauve
    (0, colord_1.colord)({ r: 160, g: 180, b: 140 }), // Dark Olive Green
    (0, colord_1.colord)({ r: 170, g: 150, b: 170 }), // Dusty Rose
    (0, colord_1.colord)({ r: 100, g: 180, b: 230 }), // Sky Blue
    (0, colord_1.colord)({ r: 230, g: 180, b: 80 }), // Golden Yellow
    (0, colord_1.colord)({ r: 180, g: 100, b: 230 }), // Purple
    (0, colord_1.colord)({ r: 80, g: 200, b: 120 }), // Emerald Green
    (0, colord_1.colord)({ r: 230, g: 130, b: 180 }), // Pink
    (0, colord_1.colord)({ r: 100, g: 160, b: 80 }), // Olive Green
    (0, colord_1.colord)({ r: 230, g: 150, b: 100 }), // Peach
    (0, colord_1.colord)({ r: 80, g: 130, b: 190 }), // Navy Blue
    (0, colord_1.colord)({ r: 210, g: 210, b: 100 }), // Lime Yellow
    (0, colord_1.colord)({ r: 190, g: 100, b: 130 }), // Maroon
    (0, colord_1.colord)({ r: 100, g: 210, b: 210 }), // Turquoise
    (0, colord_1.colord)({ r: 210, g: 140, b: 80 }), // Light Orange
    (0, colord_1.colord)({ r: 150, g: 110, b: 190 }), // Lavender
    (0, colord_1.colord)({ r: 180, g: 210, b: 120 }), // Light Green
    (0, colord_1.colord)({ r: 210, g: 100, b: 160 }), // Hot Pink
    (0, colord_1.colord)({ r: 100, g: 140, b: 110 }), // Sea Green
    (0, colord_1.colord)({ r: 230, g: 180, b: 180 }), // Light Pink
    (0, colord_1.colord)({ r: 120, g: 120, b: 190 }), // Periwinkle
    (0, colord_1.colord)({ r: 190, g: 170, b: 100 }), // Sand
    (0, colord_1.colord)({ r: 100, g: 180, b: 160 }), // Aquamarine
    (0, colord_1.colord)({ r: 210, g: 160, b: 200 }), // Orchid
    (0, colord_1.colord)({ r: 170, g: 190, b: 100 }), // Yellow Green
    (0, colord_1.colord)({ r: 100, g: 130, b: 150 }), // Steel Blue
    (0, colord_1.colord)({ r: 230, g: 140, b: 140 }), // Salmon
    (0, colord_1.colord)({ r: 140, g: 180, b: 220 }), // Light Blue
    (0, colord_1.colord)({ r: 200, g: 160, b: 110 }), // Tan
    (0, colord_1.colord)({ r: 180, g: 130, b: 180 }), // Plum
    (0, colord_1.colord)({ r: 130, g: 200, b: 130 }), // Light Sea Green
    (0, colord_1.colord)({ r: 220, g: 120, b: 120 }), // Coral
    (0, colord_1.colord)({ r: 120, g: 160, b: 200 }), // Cornflower Blue
    (0, colord_1.colord)({ r: 200, g: 200, b: 140 }), // Khaki
    (0, colord_1.colord)({ r: 160, g: 120, b: 160 }), // Purple Gray
    (0, colord_1.colord)({ r: 140, g: 180, b: 140 }), // Dark Sea Green
    (0, colord_1.colord)({ r: 200, g: 130, b: 110 }), // Dark Salmon
    (0, colord_1.colord)({ r: 130, g: 170, b: 190 }), // Cadet Blue
    (0, colord_1.colord)({ r: 190, g: 180, b: 160 }), // Tan Gray
    (0, colord_1.colord)({ r: 170, g: 140, b: 190 }), // Medium Purple
    (0, colord_1.colord)({ r: 160, g: 190, b: 160 }), // Pale Green
    (0, colord_1.colord)({ r: 190, g: 150, b: 130 }), // Rosy Brown
    (0, colord_1.colord)({ r: 140, g: 150, b: 180 }), // Light Slate Gray
    (0, colord_1.colord)({ r: 180, g: 170, b: 140 }), // Dark Khaki
    (0, colord_1.colord)({ r: 150, g: 130, b: 150 }), // Thistle
    (0, colord_1.colord)({ r: 170, g: 190, b: 180 }), // Pale Blue Green
    (0, colord_1.colord)({ r: 190, g: 140, b: 150 }), // Puce
    (0, colord_1.colord)({ r: 130, g: 180, b: 170 }), // Medium Aquamarine
    (0, colord_1.colord)({ r: 180, g: 160, b: 180 }), // Mauve
    (0, colord_1.colord)({ r: 160, g: 180, b: 140 }), // Dark Olive Green
    (0, colord_1.colord)({ r: 170, g: 150, b: 170 }), // Dusty Rose
];
// Bright pastel theme with 64 colors
exports.humanColors = [
    (0, colord_1.colord)({ r: 16, g: 185, b: 129 }), // Sea Green
    (0, colord_1.colord)({ r: 34, g: 197, b: 94 }), // Emerald
    (0, colord_1.colord)({ r: 45, g: 212, b: 191 }), // Turquoise
    (0, colord_1.colord)({ r: 48, g: 178, b: 180 }), // Teal
    (0, colord_1.colord)({ r: 52, g: 211, b: 153 }), // Spearmint
    (0, colord_1.colord)({ r: 56, g: 189, b: 248 }), // Light Blue
    (0, colord_1.colord)({ r: 59, g: 130, b: 246 }), // Royal Blue
    (0, colord_1.colord)({ r: 67, g: 190, b: 84 }), // Fresh Green
    (0, colord_1.colord)({ r: 74, g: 222, b: 128 }), // Mint
    (0, colord_1.colord)({ r: 79, g: 70, b: 229 }), // Indigo
    (0, colord_1.colord)({ r: 82, g: 183, b: 136 }), // Jade
    (0, colord_1.colord)({ r: 96, g: 165, b: 250 }), // Sky Blue
    (0, colord_1.colord)({ r: 99, g: 202, b: 253 }), // Azure
    (0, colord_1.colord)({ r: 110, g: 231, b: 183 }), // Seafoam
    (0, colord_1.colord)({ r: 124, g: 58, b: 237 }), // Royal Purple
    (0, colord_1.colord)({ r: 125, g: 211, b: 252 }), // Crystal Blue
    (0, colord_1.colord)({ r: 132, g: 204, b: 22 }), // Lime
    (0, colord_1.colord)({ r: 133, g: 77, b: 14 }), // Chocolate
    (0, colord_1.colord)({ r: 134, g: 239, b: 172 }), // Light Green
    (0, colord_1.colord)({ r: 147, g: 51, b: 234 }), // Bright Purple
    (0, colord_1.colord)({ r: 147, g: 197, b: 253 }), // Powder Blue
    (0, colord_1.colord)({ r: 151, g: 255, b: 187 }), // Fresh Mint
    (0, colord_1.colord)({ r: 163, g: 230, b: 53 }), // Yellow Green
    (0, colord_1.colord)({ r: 167, g: 139, b: 250 }), // Periwinkle
    (0, colord_1.colord)({ r: 168, g: 85, b: 247 }), // Vibrant Purple
    (0, colord_1.colord)({ r: 179, g: 136, b: 255 }), // Light Purple
    (0, colord_1.colord)({ r: 186, g: 255, b: 201 }), // Pale Emerald
    (0, colord_1.colord)({ r: 190, g: 92, b: 251 }), // Amethyst
    (0, colord_1.colord)({ r: 192, g: 132, b: 252 }), // Lavender
    (0, colord_1.colord)({ r: 202, g: 138, b: 4 }), // Rich Gold
    (0, colord_1.colord)({ r: 202, g: 225, b: 255 }), // Baby Blue
    (0, colord_1.colord)({ r: 204, g: 204, b: 255 }), // Soft Lavender Blue
    (0, colord_1.colord)({ r: 217, g: 70, b: 239 }), // Fuchsia
    (0, colord_1.colord)({ r: 220, g: 38, b: 38 }), // Ruby
    (0, colord_1.colord)({ r: 220, g: 220, b: 255 }), // Meringue Blue
    (0, colord_1.colord)({ r: 220, g: 240, b: 250 }), // Ice Blue
    (0, colord_1.colord)({ r: 230, g: 250, b: 210 }), // Pastel Lime
    (0, colord_1.colord)({ r: 230, g: 255, b: 250 }), // Mint Whisper
    (0, colord_1.colord)({ r: 233, g: 213, b: 255 }), // Light Lilac
    (0, colord_1.colord)({ r: 234, g: 88, b: 12 }), // Burnt Orange
    (0, colord_1.colord)({ r: 234, g: 179, b: 8 }), // Sunflower
    (0, colord_1.colord)({ r: 235, g: 75, b: 75 }), // Bright Red
    (0, colord_1.colord)({ r: 236, g: 72, b: 153 }), // Deep Pink
    (0, colord_1.colord)({ r: 239, g: 68, b: 68 }), // Crimson
    (0, colord_1.colord)({ r: 240, g: 171, b: 252 }), // Orchid
    (0, colord_1.colord)({ r: 240, g: 240, b: 200 }), // Light Khaki
    (0, colord_1.colord)({ r: 244, g: 114, b: 182 }), // Rose
    (0, colord_1.colord)({ r: 245, g: 101, b: 101 }), // Coral
    (0, colord_1.colord)({ r: 245, g: 158, b: 11 }), // Amber
    (0, colord_1.colord)({ r: 248, g: 113, b: 113 }), // Warm Red
    (0, colord_1.colord)({ r: 249, g: 115, b: 22 }), // Tangerine
    (0, colord_1.colord)({ r: 250, g: 215, b: 225 }), // Cotton Candy
    (0, colord_1.colord)({ r: 250, g: 250, b: 210 }), // Pastel Lemon
    (0, colord_1.colord)({ r: 251, g: 113, b: 133 }), // Watermelon
    (0, colord_1.colord)({ r: 251, g: 146, b: 60 }), // Light Orange
    (0, colord_1.colord)({ r: 251, g: 191, b: 36 }), // Marigold
    (0, colord_1.colord)({ r: 251, g: 235, b: 245 }), // Rose Powder
    (0, colord_1.colord)({ r: 252, g: 165, b: 165 }), // Peach
    (0, colord_1.colord)({ r: 252, g: 211, b: 77 }), // Golden
    (0, colord_1.colord)({ r: 253, g: 164, b: 175 }), // Salmon Pink
    (0, colord_1.colord)({ r: 255, g: 204, b: 229 }), // Blush Pink
    (0, colord_1.colord)({ r: 255, g: 223, b: 186 }), // Apricot Cream
    (0, colord_1.colord)({ r: 255, g: 240, b: 200 }), // Vanilla
];
exports.botColors = [
    (0, colord_1.colord)({ r: 190, g: 120, b: 120 }), // Muted Red
    (0, colord_1.colord)({ r: 120, g: 160, b: 190 }), // Muted Sky Blue
    (0, colord_1.colord)({ r: 190, g: 160, b: 100 }), // Muted Golden Yellow
    (0, colord_1.colord)({ r: 160, g: 120, b: 190 }), // Muted Purple
    (0, colord_1.colord)({ r: 100, g: 170, b: 130 }), // Muted Emerald Green
    (0, colord_1.colord)({ r: 190, g: 130, b: 160 }), // Muted Pink
    (0, colord_1.colord)({ r: 120, g: 150, b: 100 }), // Muted Olive Green
    (0, colord_1.colord)({ r: 190, g: 140, b: 120 }), // Muted Peach
    (0, colord_1.colord)({ r: 100, g: 120, b: 160 }), // Muted Navy Blue
    (0, colord_1.colord)({ r: 170, g: 170, b: 120 }), // Muted Lime Yellow
    (0, colord_1.colord)({ r: 160, g: 120, b: 130 }), // Muted Maroon
    (0, colord_1.colord)({ r: 120, g: 170, b: 170 }), // Muted Turquoise
    (0, colord_1.colord)({ r: 170, g: 140, b: 100 }), // Muted Light Orange
    (0, colord_1.colord)({ r: 140, g: 120, b: 160 }), // Muted Lavender
    (0, colord_1.colord)({ r: 150, g: 170, b: 130 }), // Muted Light Green
    (0, colord_1.colord)({ r: 170, g: 120, b: 140 }), // Muted Hot Pink
    (0, colord_1.colord)({ r: 120, g: 140, b: 120 }), // Muted Sea Green
    (0, colord_1.colord)({ r: 180, g: 160, b: 160 }), // Muted Light Pink
    (0, colord_1.colord)({ r: 130, g: 130, b: 160 }), // Muted Periwinkle
    (0, colord_1.colord)({ r: 160, g: 150, b: 120 }), // Muted Sand
    (0, colord_1.colord)({ r: 120, g: 160, b: 150 }), // Muted Aquamarine
    (0, colord_1.colord)({ r: 170, g: 150, b: 170 }), // Muted Orchid
    (0, colord_1.colord)({ r: 150, g: 160, b: 120 }), // Muted Yellow Green
    (0, colord_1.colord)({ r: 120, g: 130, b: 140 }), // Muted Steel Blue
    (0, colord_1.colord)({ r: 180, g: 140, b: 140 }), // Muted Salmon
    (0, colord_1.colord)({ r: 140, g: 160, b: 170 }), // Muted Light Blue
    (0, colord_1.colord)({ r: 170, g: 150, b: 130 }), // Muted Tan
    (0, colord_1.colord)({ r: 160, g: 130, b: 160 }), // Muted Plum
    (0, colord_1.colord)({ r: 130, g: 170, b: 130 }), // Muted Light Sea Green
    (0, colord_1.colord)({ r: 170, g: 130, b: 130 }), // Muted Coral
    (0, colord_1.colord)({ r: 130, g: 150, b: 170 }), // Muted Cornflower Blue
    (0, colord_1.colord)({ r: 170, g: 170, b: 140 }), // Muted Khaki
    (0, colord_1.colord)({ r: 150, g: 130, b: 150 }), // Muted Purple Gray
    (0, colord_1.colord)({ r: 140, g: 160, b: 140 }), // Muted Dark Sea Green
    (0, colord_1.colord)({ r: 170, g: 130, b: 120 }), // Muted Dark Salmon
    (0, colord_1.colord)({ r: 130, g: 150, b: 160 }), // Muted Cadet Blue
    (0, colord_1.colord)({ r: 160, g: 160, b: 150 }), // Muted Tan Gray
    (0, colord_1.colord)({ r: 150, g: 140, b: 160 }), // Muted Medium Purple
    (0, colord_1.colord)({ r: 150, g: 170, b: 150 }), // Muted Pale Green
    (0, colord_1.colord)({ r: 160, g: 140, b: 130 }), // Muted Rosy Brown
    (0, colord_1.colord)({ r: 140, g: 150, b: 160 }), // Muted Light Slate Gray
    (0, colord_1.colord)({ r: 160, g: 150, b: 140 }), // Muted Dark Khaki
    (0, colord_1.colord)({ r: 140, g: 130, b: 140 }), // Muted Thistle
    (0, colord_1.colord)({ r: 150, g: 160, b: 160 }), // Muted Pale Blue Green
    (0, colord_1.colord)({ r: 160, g: 140, b: 150 }), // Muted Puce
    (0, colord_1.colord)({ r: 130, g: 160, b: 150 }), // Muted Medium Aquamarine
    (0, colord_1.colord)({ r: 160, g: 150, b: 160 }), // Muted Mauve
    (0, colord_1.colord)({ r: 150, g: 160, b: 140 }), // Muted Dark Olive Green
    (0, colord_1.colord)({ r: 150, g: 140, b: 150 }), // Muted Dusty Rose
];
// Fallback colors for when the color palette is exhausted. Currently 100 colors.
exports.fallbackColors = [
    (0, colord_1.colord)({ r: 0, g: 5, b: 0 }), // Black Mint
    (0, colord_1.colord)({ r: 0, g: 15, b: 0 }), // Deep Forest
    (0, colord_1.colord)({ r: 0, g: 25, b: 0 }), // Jungle
    (0, colord_1.colord)({ r: 0, g: 35, b: 0 }), // Dark Emerald
    (0, colord_1.colord)({ r: 0, g: 45, b: 0 }), // Green Moss
    (0, colord_1.colord)({ r: 0, g: 55, b: 0 }), // Moss Shadow
    (0, colord_1.colord)({ r: 0, g: 65, b: 0 }), // Dark Meadow
    (0, colord_1.colord)({ r: 0, g: 75, b: 0 }), // Forest Fern
    (0, colord_1.colord)({ r: 0, g: 85, b: 0 }), // Pine Leaf
    (0, colord_1.colord)({ r: 0, g: 95, b: 0 }), // Shadow Grass
    (0, colord_1.colord)({ r: 0, g: 105, b: 0 }), // Classic Green
    (0, colord_1.colord)({ r: 0, g: 115, b: 0 }), // Deep Lime
    (0, colord_1.colord)({ r: 0, g: 125, b: 0 }), // Dense Leaf
    (0, colord_1.colord)({ r: 0, g: 135, b: 0 }), // Basil Green
    (0, colord_1.colord)({ r: 0, g: 145, b: 0 }), // Organic Green
    (0, colord_1.colord)({ r: 0, g: 155, b: 0 }), // Bitter Herb
    (0, colord_1.colord)({ r: 0, g: 165, b: 0 }), // Raw Spinach
    (0, colord_1.colord)({ r: 0, g: 175, b: 0 }), // Woodland
    (0, colord_1.colord)({ r: 0, g: 185, b: 0 }), // Spring Weed
    (0, colord_1.colord)({ r: 0, g: 195, b: 5 }), // Apple Stem
    (0, colord_1.colord)({ r: 0, g: 205, b: 10 }), // Crisp Lettuce
    (0, colord_1.colord)({ r: 0, g: 215, b: 15 }), // Vibrant Green
    (0, colord_1.colord)({ r: 0, g: 225, b: 20 }), // Bright Herb
    (0, colord_1.colord)({ r: 0, g: 235, b: 25 }), // Green Splash
    (0, colord_1.colord)({ r: 0, g: 245, b: 30 }), // Mint Leaf
    (0, colord_1.colord)({ r: 0, g: 255, b: 35 }), // Fresh Mint
    (0, colord_1.colord)({ r: 10, g: 255, b: 45 }), // Neon Grass
    (0, colord_1.colord)({ r: 20, g: 255, b: 55 }), // Lemon Balm
    (0, colord_1.colord)({ r: 30, g: 255, b: 65 }), // Juicy Green
    (0, colord_1.colord)({ r: 40, g: 255, b: 75 }), // Pear Tint
    (0, colord_1.colord)({ r: 50, g: 255, b: 85 }), // Avocado Pastel
    (0, colord_1.colord)({ r: 60, g: 255, b: 95 }), // Lime Glow
    (0, colord_1.colord)({ r: 70, g: 255, b: 105 }), // Light Leaf
    (0, colord_1.colord)({ r: 80, g: 255, b: 115 }), // Soft Fern
    (0, colord_1.colord)({ r: 90, g: 255, b: 125 }), // Pastel Green
    (0, colord_1.colord)({ r: 100, g: 255, b: 135 }), // Green Melon
    (0, colord_1.colord)({ r: 110, g: 255, b: 145 }), // Herbal Mist
    (0, colord_1.colord)({ r: 120, g: 255, b: 155 }), // Kiwi Foam
    (0, colord_1.colord)({ r: 130, g: 255, b: 165 }), // Aloe Fresh
    (0, colord_1.colord)({ r: 140, g: 255, b: 175 }), // Light Mint
    (0, colord_1.colord)({ r: 150, g: 200, b: 255 }), // Cornflower Mist
    (0, colord_1.colord)({ r: 150, g: 255, b: 185 }), // Green Sorbet
    (0, colord_1.colord)({ r: 160, g: 215, b: 255 }), // Powder Blue
    (0, colord_1.colord)({ r: 160, g: 255, b: 195 }), // Pastel Apple
    (0, colord_1.colord)({ r: 170, g: 190, b: 255 }), // Periwinkle Ice
    (0, colord_1.colord)({ r: 170, g: 225, b: 255 }), // Baby Sky
    (0, colord_1.colord)({ r: 170, g: 255, b: 205 }), // Aloe Breeze
    (0, colord_1.colord)({ r: 180, g: 180, b: 255 }), // Pale Indigo
    (0, colord_1.colord)({ r: 180, g: 235, b: 250 }), // Aqua Pastel
    (0, colord_1.colord)({ r: 180, g: 255, b: 215 }), // Pale Mint
    (0, colord_1.colord)({ r: 190, g: 140, b: 195 }), // Fuchsia Tint
    (0, colord_1.colord)({ r: 190, g: 245, b: 240 }), // Ice Mint
    (0, colord_1.colord)({ r: 190, g: 255, b: 225 }), // Mint Water
    (0, colord_1.colord)({ r: 195, g: 145, b: 200 }), // Dusky Rose
    (0, colord_1.colord)({ r: 200, g: 150, b: 205 }), // Plum Frost
    (0, colord_1.colord)({ r: 200, g: 170, b: 255 }), // Lilac Bloom
    (0, colord_1.colord)({ r: 200, g: 255, b: 215 }), // Cool Aloe
    (0, colord_1.colord)({ r: 200, g: 255, b: 235 }), // Cool Mist
    (0, colord_1.colord)({ r: 205, g: 155, b: 210 }), // Berry Foam
    (0, colord_1.colord)({ r: 210, g: 160, b: 215 }), // Grape Cloud
    (0, colord_1.colord)({ r: 210, g: 255, b: 245 }), // Sea Mist
    (0, colord_1.colord)({ r: 215, g: 165, b: 220 }), // Light Bloom
    (0, colord_1.colord)({ r: 215, g: 255, b: 200 }), // Fresh Mint
    (0, colord_1.colord)({ r: 220, g: 160, b: 255 }), // Violet Mist
    (0, colord_1.colord)({ r: 220, g: 170, b: 225 }), // Cherry Blossom
    (0, colord_1.colord)({ r: 220, g: 255, b: 255 }), // Pale Aqua
    (0, colord_1.colord)({ r: 225, g: 175, b: 230 }), // Faded Rose
    (0, colord_1.colord)({ r: 225, g: 255, b: 175 }), // Soft Lime
    (0, colord_1.colord)({ r: 230, g: 180, b: 235 }), // Dreamy Mauve
    (0, colord_1.colord)({ r: 230, g: 250, b: 255 }), // Sky Haze
    (0, colord_1.colord)({ r: 235, g: 150, b: 255 }), // Orchid Glow
    (0, colord_1.colord)({ r: 235, g: 185, b: 240 }), // Powder Violet
    (0, colord_1.colord)({ r: 240, g: 190, b: 245 }), // Pastel Violet
    (0, colord_1.colord)({ r: 240, g: 240, b: 255 }), // Frosted Lilac
    (0, colord_1.colord)({ r: 240, g: 250, b: 160 }), // Citrus Wash
    (0, colord_1.colord)({ r: 245, g: 160, b: 240 }), // Rose Lilac
    (0, colord_1.colord)({ r: 245, g: 195, b: 250 }), // Soft Magenta
    (0, colord_1.colord)({ r: 245, g: 245, b: 175 }), // Lemon Mist
    (0, colord_1.colord)({ r: 250, g: 200, b: 255 }), // Lilac Cream
    (0, colord_1.colord)({ r: 250, g: 230, b: 255 }), // Misty Mauve
    (0, colord_1.colord)({ r: 255, g: 170, b: 225 }), // Bubblegum Pink
    (0, colord_1.colord)({ r: 255, g: 185, b: 215 }), // Blush Mist
    (0, colord_1.colord)({ r: 255, g: 195, b: 235 }), // Faded Fuchsia
    (0, colord_1.colord)({ r: 255, g: 200, b: 220 }), // Cotton Rose
    (0, colord_1.colord)({ r: 255, g: 205, b: 245 }), // Pastel Orchid
    (0, colord_1.colord)({ r: 255, g: 205, b: 255 }), // Violet Bloom
    (0, colord_1.colord)({ r: 255, g: 210, b: 230 }), // Pastel Blush
    (0, colord_1.colord)({ r: 255, g: 210, b: 250 }), // Lavender Mist
    (0, colord_1.colord)({ r: 255, g: 210, b: 255 }), // Orchid Mist
    (0, colord_1.colord)({ r: 255, g: 215, b: 195 }), // Apricot Glow
    (0, colord_1.colord)({ r: 255, g: 215, b: 245 }), // Rose Whisper
    (0, colord_1.colord)({ r: 255, g: 220, b: 235 }), // Pink Mist
    (0, colord_1.colord)({ r: 255, g: 220, b: 250 }), // Powder Petal
    (0, colord_1.colord)({ r: 255, g: 225, b: 180 }), // Butter Peach
    (0, colord_1.colord)({ r: 255, g: 225, b: 255 }), // Petal Mist
    (0, colord_1.colord)({ r: 255, g: 230, b: 245 }), // Light Rose
    (0, colord_1.colord)({ r: 255, g: 235, b: 200 }), // Cream Peach
    (0, colord_1.colord)({ r: 255, g: 235, b: 235 }), // Blushed Petal
    (0, colord_1.colord)({ r: 255, g: 240, b: 220 }), // Pastel Sand
    (0, colord_1.colord)({ r: 255, g: 245, b: 210 }), // Soft Banana
];
