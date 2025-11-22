import { z } from "zod";
import { UnitType } from "./game/Game";
export const BombUnitSchema = z.union([
    z.literal("abomb"),
    z.literal("hbomb"),
    z.literal("mirv"),
    z.literal("mirvw"),
]);
export const unitTypeToBombUnit = {
    [UnitType.AtomBomb]: "abomb",
    [UnitType.HydrogenBomb]: "hbomb",
    [UnitType.MIRV]: "mirv",
    [UnitType.MIRVWarhead]: "mirvw",
};
export const BoatUnitSchema = z.union([z.literal("trade"), z.literal("trans")]);
// export const unitTypeToBoatUnit = {
//   [UnitType.TradeShip]: "trade",
//   [UnitType.TransportShip]: "trans",
// } as const satisfies Record<BoatUnitType, BoatUnit>;
export const OtherUnitSchema = z.union([
    z.literal("city"),
    z.literal("defp"),
    z.literal("port"),
    z.literal("wshp"),
    z.literal("silo"),
    z.literal("saml"),
    z.literal("fact"),
]);
export const unitTypeToOtherUnit = {
    [UnitType.City]: "city",
    [UnitType.DefensePost]: "defp",
    [UnitType.MissileSilo]: "silo",
    [UnitType.Port]: "port",
    [UnitType.SAMLauncher]: "saml",
    [UnitType.Warship]: "wshp",
    [UnitType.Factory]: "fact",
};
// Attacks
export const ATTACK_INDEX_SENT = 0; // Outgoing attack troops
export const ATTACK_INDEX_RECV = 1; // Incmoing attack troops
export const ATTACK_INDEX_CANCEL = 2; // Cancelled attack troops
// Boats
export const BOAT_INDEX_SENT = 0; // Boats launched
export const BOAT_INDEX_ARRIVE = 1; // Boats arrived
export const BOAT_INDEX_CAPTURE = 2; // Boats captured
export const BOAT_INDEX_DESTROY = 3; // Boats destroyed
// Bombs
export const BOMB_INDEX_LAUNCH = 0; // Bombs launched
export const BOMB_INDEX_LAND = 1; // Bombs landed
export const BOMB_INDEX_INTERCEPT = 2; // Bombs intercepted
// Gold
export const GOLD_INDEX_WORK = 0; // Gold earned by workers
export const GOLD_INDEX_WAR = 1; // Gold earned by conquering players
export const GOLD_INDEX_TRADE = 2; // Gold earned by trade ships
export const GOLD_INDEX_STEAL = 3; // Gold earned by capturing trade ships
// Other Units
export const OTHER_INDEX_BUILT = 0; // Structures and warships built
export const OTHER_INDEX_DESTROY = 1; // Structures and warships destroyed
export const OTHER_INDEX_CAPTURE = 2; // Structures captured
export const OTHER_INDEX_LOST = 3; // Structures/warships destroyed/captured by others
export const OTHER_INDEX_UPGRADE = 4; // Structures upgraded
const BigIntStringSchema = z.preprocess((val) => {
    if (typeof val === "string" && /^-?\d+$/.test(val))
        return BigInt(val);
    if (typeof val === "bigint")
        return val;
    return val;
}, z.bigint());
const AtLeastOneNumberSchema = BigIntStringSchema.array().min(1);
export const PlayerStatsSchema = z
    .object({
    attacks: AtLeastOneNumberSchema.optional(),
    betrayals: BigIntStringSchema.optional(),
    boats: z.partialRecord(BoatUnitSchema, AtLeastOneNumberSchema).optional(),
    bombs: z.partialRecord(BombUnitSchema, AtLeastOneNumberSchema).optional(),
    gold: AtLeastOneNumberSchema.optional(),
    units: z.partialRecord(OtherUnitSchema, AtLeastOneNumberSchema).optional(),
})
    .optional();
