"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.flattenedEmojiTable = exports.emojiTable = void 0;
exports.manhattanDistWrapped = manhattanDistWrapped;
exports.within = within;
exports.distSort = distSort;
exports.distSortUnit = distSortUnit;
exports.simpleHash = simpleHash;
exports.calculateBoundingBox = calculateBoundingBox;
exports.calculateBoundingBoxCenter = calculateBoundingBoxCenter;
exports.inscribed = inscribed;
exports.getMode = getMode;
exports.sanitize = sanitize;
exports.onlyImages = onlyImages;
exports.createGameRecord = createGameRecord;
exports.decompressGameRecord = decompressGameRecord;
exports.assertNever = assertNever;
exports.generateID = generateID;
exports.toInt = toInt;
exports.maxInt = maxInt;
exports.minInt = minInt;
exports.withinInt = withinInt;
exports.createRandomName = createRandomName;
exports.replacer = replacer;
exports.sigmoid = sigmoid;
const dompurify_1 = require("dompurify");
const nanoid_1 = require("nanoid");
const Game_1 = require("./game/Game");
const BotNames_1 = require("./execution/utils/BotNames");
function manhattanDistWrapped(c1, c2, width) {
    // Calculate x distance
    let dx = Math.abs(c1.x - c2.x);
    // Check if wrapping around the x-axis is shorter
    dx = Math.min(dx, width - dx);
    // Calculate y distance (no wrapping for y-axis)
    const dy = Math.abs(c1.y - c2.y);
    // Return the sum of x and y distances
    return dx + dy;
}
function within(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
function distSort(gm, target) {
    return (a, b) => {
        return gm.manhattanDist(a, target) - gm.manhattanDist(b, target);
    };
}
function distSortUnit(gm, target) {
    const targetRef = typeof target === "number" ? target : target.tile();
    return (a, b) => {
        return (gm.manhattanDist(a.tile(), targetRef) -
            gm.manhattanDist(b.tile(), targetRef));
    };
}
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
}
function calculateBoundingBox(gm, borderTiles) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    borderTiles.forEach((tile) => {
        const cell = gm.cell(tile);
        minX = Math.min(minX, cell.x);
        minY = Math.min(minY, cell.y);
        maxX = Math.max(maxX, cell.x);
        maxY = Math.max(maxY, cell.y);
    });
    return { min: new Game_1.Cell(minX, minY), max: new Game_1.Cell(maxX, maxY) };
}
function calculateBoundingBoxCenter(gm, borderTiles) {
    const { min, max } = calculateBoundingBox(gm, borderTiles);
    return new Game_1.Cell(min.x + Math.floor((max.x - min.x) / 2), min.y + Math.floor((max.y - min.y) / 2));
}
function inscribed(outer, inner) {
    return (outer.min.x <= inner.min.x &&
        outer.min.y <= inner.min.y &&
        outer.max.x >= inner.max.x &&
        outer.max.y >= inner.max.y);
}
function getMode(list) {
    var _a;
    // Count occurrences
    const counts = new Map();
    for (const item of list) {
        counts.set(item, ((_a = counts.get(item)) !== null && _a !== void 0 ? _a : 0) + 1);
    }
    // Find the item with the highest count
    let mode = 0;
    let maxCount = 0;
    for (const [item, count] of counts) {
        if (count > maxCount) {
            maxCount = count;
            mode = item;
        }
    }
    return mode;
}
function sanitize(name) {
    return Array.from(name)
        .join("")
        .replace(/[^\p{L}\p{N}\s\p{Emoji}\p{Emoji_Component}[\]_]/gu, "");
}
function onlyImages(html) {
    return dompurify_1.default.sanitize(html, {
        ALLOWED_TAGS: ["span", "img"],
        ALLOWED_ATTR: ["src", "alt", "class", "style"],
        ALLOWED_URI_REGEXP: /^https:\/\/cdn\.jsdelivr\.net\/gh\/twitter\/twemoji/,
        ADD_ATTR: ["style"],
    });
}
function createGameRecord(gameID, config, 
// username does not need to be set.
players, allTurns, start, end, winner, serverConfig) {
    const duration = Math.floor((end - start) / 1000);
    const version = "v0.0.2";
    const gitCommit = serverConfig.gitCommit();
    const subdomain = serverConfig.subdomain();
    const domain = serverConfig.domain();
    const num_turns = allTurns.length;
    const turns = allTurns.filter((t) => t.intents.length !== 0 || t.hash !== undefined);
    const record = {
        info: {
            gameID,
            config,
            players,
            start,
            end,
            duration,
            num_turns,
            winner,
        },
        version,
        gitCommit,
        subdomain,
        domain,
        turns,
    };
    return record;
}
function decompressGameRecord(gameRecord) {
    const turns = [];
    let lastTurnNum = -1;
    for (const turn of gameRecord.turns) {
        while (lastTurnNum < turn.turnNumber - 1) {
            lastTurnNum++;
            turns.push({
                turnNumber: lastTurnNum,
                intents: [],
            });
        }
        turns.push(turn);
        lastTurnNum = turn.turnNumber;
    }
    const turnLength = turns.length;
    for (let i = turnLength; i < gameRecord.info.num_turns; i++) {
        turns.push({
            turnNumber: i,
            intents: [],
        });
    }
    gameRecord.turns = turns;
    return gameRecord;
}
function assertNever(x) {
    throw new Error("Unexpected value: " + x);
}
function generateID() {
    const nanoid = (0, nanoid_1.customAlphabet)("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", 8);
    return nanoid();
}
function toInt(num) {
    if (num === Infinity) {
        return BigInt(Number.MAX_SAFE_INTEGER);
    }
    if (num === -Infinity) {
        return BigInt(Number.MIN_SAFE_INTEGER);
    }
    return BigInt(Math.floor(num));
}
function maxInt(a, b) {
    return a > b ? a : b;
}
function minInt(a, b) {
    return a < b ? a : b;
}
function withinInt(num, min, max) {
    const atLeastMin = maxInt(num, min);
    return minInt(atLeastMin, max);
}
function createRandomName(name, playerType) {
    let randomName = null;
    if (playerType === "HUMAN") {
        const hash = simpleHash(name);
        const prefixIndex = hash % BotNames_1.BOT_NAME_PREFIXES.length;
        const suffixIndex = Math.floor(hash / BotNames_1.BOT_NAME_PREFIXES.length) % BotNames_1.BOT_NAME_SUFFIXES.length;
        randomName = `👤 ${BotNames_1.BOT_NAME_PREFIXES[prefixIndex]} ${BotNames_1.BOT_NAME_SUFFIXES[suffixIndex]}`;
    }
    return randomName;
}
exports.emojiTable = [
    ["😀", "😊", "🥰", "😇", "😎"],
    ["😞", "🥺", "😭", "😱", "😡"],
    ["😈", "🤡", "🖕", "🥱", "🤦‍♂️"],
    ["👋", "👏", "🤌", "💪", "🫡"],
    ["👍", "👎", "❓", "🐔", "🐀"],
    ["🤝", "🆘", "🕊️", "🏳️", "⏳"],
    ["🔥", "💥", "💀", "☢️", "⚠️"],
    ["↖️", "⬆️", "↗️", "👑", "🥇"],
    ["⬅️", "🎯", "➡️", "🥈", "🥉"],
    ["↙️", "⬇️", "↘️", "❤️", "💔"],
    ["💰", "⚓", "⛵", "🏡", "🛡️"],
];
// 2d to 1d array
exports.flattenedEmojiTable = exports.emojiTable.flat();
/**
 * JSON.stringify replacer function that converts bigint values to strings.
 */
function replacer(_key, value) {
    return typeof value === "bigint" ? value.toString() : value;
}
function sigmoid(value, decayRate, midpoint) {
    return 1 / (1 + Math.exp(-decayRate * (value - midpoint)));
}
