"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PlayerStatsSchema = exports.OTHER_INDEX_UPGRADE = exports.OTHER_INDEX_LOST = exports.OTHER_INDEX_CAPTURE = exports.OTHER_INDEX_DESTROY = exports.OTHER_INDEX_BUILT = exports.GOLD_INDEX_STEAL = exports.GOLD_INDEX_TRADE = exports.GOLD_INDEX_WAR = exports.GOLD_INDEX_WORK = exports.BOMB_INDEX_INTERCEPT = exports.BOMB_INDEX_LAND = exports.BOMB_INDEX_LAUNCH = exports.BOAT_INDEX_DESTROY = exports.BOAT_INDEX_CAPTURE = exports.BOAT_INDEX_ARRIVE = exports.BOAT_INDEX_SENT = exports.ATTACK_INDEX_CANCEL = exports.ATTACK_INDEX_RECV = exports.ATTACK_INDEX_SENT = exports.unitTypeToOtherUnit = exports.OtherUnitSchema = exports.BoatUnitSchema = exports.unitTypeToBombUnit = exports.BombUnitSchema = void 0;
const zod_1 = require("zod");
const Game_1 = require("./game/Game");
exports.BombUnitSchema = zod_1.z.union([
    zod_1.z.literal("abomb"),
    zod_1.z.literal("hbomb"),
    zod_1.z.literal("mirv"),
    zod_1.z.literal("mirvw"),
]);
exports.unitTypeToBombUnit = {
    [Game_1.UnitType.AtomBomb]: "abomb",
    [Game_1.UnitType.HydrogenBomb]: "hbomb",
    [Game_1.UnitType.MIRV]: "mirv",
    [Game_1.UnitType.MIRVWarhead]: "mirvw",
};
exports.BoatUnitSchema = zod_1.z.union([zod_1.z.literal("trade"), zod_1.z.literal("trans")]);
// export const unitTypeToBoatUnit = {
//   [UnitType.TradeShip]: "trade",
//   [UnitType.TransportShip]: "trans",
// } as const satisfies Record<BoatUnitType, BoatUnit>;
exports.OtherUnitSchema = zod_1.z.union([
    zod_1.z.literal("city"),
    zod_1.z.literal("defp"),
    zod_1.z.literal("port"),
    zod_1.z.literal("wshp"),
    zod_1.z.literal("silo"),
    zod_1.z.literal("saml"),
    zod_1.z.literal("fact"),
]);
exports.unitTypeToOtherUnit = {
    [Game_1.UnitType.City]: "city",
    [Game_1.UnitType.DefensePost]: "defp",
    [Game_1.UnitType.MissileSilo]: "silo",
    [Game_1.UnitType.Port]: "port",
    [Game_1.UnitType.SAMLauncher]: "saml",
    [Game_1.UnitType.Warship]: "wshp",
    [Game_1.UnitType.Factory]: "fact",
};
// Attacks
exports.ATTACK_INDEX_SENT = 0; // Outgoing attack troops
exports.ATTACK_INDEX_RECV = 1; // Incmoing attack troops
exports.ATTACK_INDEX_CANCEL = 2; // Cancelled attack troops
// Boats
exports.BOAT_INDEX_SENT = 0; // Boats launched
exports.BOAT_INDEX_ARRIVE = 1; // Boats arrived
exports.BOAT_INDEX_CAPTURE = 2; // Boats captured
exports.BOAT_INDEX_DESTROY = 3; // Boats destroyed
// Bombs
exports.BOMB_INDEX_LAUNCH = 0; // Bombs launched
exports.BOMB_INDEX_LAND = 1; // Bombs landed
exports.BOMB_INDEX_INTERCEPT = 2; // Bombs intercepted
// Gold
exports.GOLD_INDEX_WORK = 0; // Gold earned by workers
exports.GOLD_INDEX_WAR = 1; // Gold earned by conquering players
exports.GOLD_INDEX_TRADE = 2; // Gold earned by trade ships
exports.GOLD_INDEX_STEAL = 3; // Gold earned by capturing trade ships
// Other Units
exports.OTHER_INDEX_BUILT = 0; // Structures and warships built
exports.OTHER_INDEX_DESTROY = 1; // Structures and warships destroyed
exports.OTHER_INDEX_CAPTURE = 2; // Structures captured
exports.OTHER_INDEX_LOST = 3; // Structures/warships destroyed/captured by others
exports.OTHER_INDEX_UPGRADE = 4; // Structures upgraded
const BigIntStringSchema = zod_1.z.preprocess((val) => {
    if (typeof val === "string" && /^-?\d+$/.test(val))
        return BigInt(val);
    if (typeof val === "bigint")
        return val;
    return val;
}, zod_1.z.bigint());
const AtLeastOneNumberSchema = BigIntStringSchema.array().min(1);
exports.PlayerStatsSchema = zod_1.z
    .object({
    attacks: AtLeastOneNumberSchema.optional(),
    betrayals: BigIntStringSchema.optional(),
    boats: zod_1.z.partialRecord(exports.BoatUnitSchema, AtLeastOneNumberSchema).optional(),
    bombs: zod_1.z.partialRecord(exports.BombUnitSchema, AtLeastOneNumberSchema).optional(),
    gold: AtLeastOneNumberSchema.optional(),
    units: zod_1.z.partialRecord(exports.OtherUnitSchema, AtLeastOneNumberSchema).optional(),
})
    .optional();
