"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GameEndInfoSchema = exports.PlayerRecordSchema = exports.ClientMessageSchema = exports.ClientJoinMessageSchema = exports.ClientIntentMessageSchema = exports.ClientPingMessageSchema = exports.ClientLogMessageSchema = exports.ClientHashSchema = exports.ClientSendWinnerSchema = exports.ServerMessageSchema = exports.ServerErrorSchema = exports.ServerDesyncSchema = exports.ServerStartGameMessageSchema = exports.ServerPrestartMessageSchema = exports.ServerPingMessageSchema = exports.ServerTurnMessageSchema = exports.WinnerSchema = exports.GameStartInfoSchema = exports.PlayerSchema = exports.TurnSchema = exports.KickPlayerIntentSchema = exports.MarkDisconnectedIntentSchema = exports.QuickChatIntentSchema = exports.DeleteUnitIntentSchema = exports.MoveWarshipIntentSchema = exports.CancelBoatIntentSchema = exports.CancelAttackIntentSchema = exports.UpgradeStructureIntentSchema = exports.BuildUnitIntentSchema = exports.DonateTroopIntentSchema = exports.DonateGoldIntentSchema = exports.EmbargoIntentSchema = exports.EmojiIntentSchema = exports.TargetPlayerIntentSchema = exports.BreakAllianceIntentSchema = exports.AllianceRequestReplyIntentSchema = exports.AllianceRequestIntentSchema = exports.BoatAttackIntentSchema = exports.SpawnIntentSchema = exports.AttackIntentSchema = exports.AllianceExtensionIntentSchema = exports.QuickChatKeySchema = exports.FlagSchema = exports.UsernameSchema = exports.AllPlayersStatsSchema = exports.ID = exports.PersistentIdSchema = exports.TeamSchema = exports.GameConfigSchema = exports.LogSeverity = void 0;
exports.GameRecordSchema = exports.AnalyticsRecordSchema = void 0;
const zod_1 = require("zod");
const QuickChat_json_1 = require("../../resources/QuickChat.json");
const countries_json_1 = require("../client/data/countries.json");
const CosmeticSchemas_1 = require("./CosmeticSchemas");
const Game_1 = require("./game/Game");
const StatsSchemas_1 = require("./StatsSchemas");
const Util_1 = require("./Util");
const PlayerTypeSchema = zod_1.z.enum(Game_1.PlayerType);
var LogSeverity;
(function (LogSeverity) {
    LogSeverity["Debug"] = "DEBUG";
    LogSeverity["Info"] = "INFO";
    LogSeverity["Warn"] = "WARN";
    LogSeverity["Error"] = "ERROR";
    LogSeverity["Fatal"] = "FATAL";
})(LogSeverity || (exports.LogSeverity = LogSeverity = {}));
//
// Utility types
//
const TeamCountConfigSchema = zod_1.z.union([
    zod_1.z.number(),
    zod_1.z.literal(Game_1.Duos),
    zod_1.z.literal(Game_1.Trios),
    zod_1.z.literal(Game_1.Quads),
]);
exports.GameConfigSchema = zod_1.z.object({
    gameMap: zod_1.z.enum(Game_1.GameMapType),
    difficulty: zod_1.z.enum(Game_1.Difficulty),
    donateGold: zod_1.z.boolean(),
    donateTroops: zod_1.z.boolean(),
    gameType: zod_1.z.enum(Game_1.GameType),
    gameMode: zod_1.z.enum(Game_1.GameMode),
    disableNPCs: zod_1.z.boolean(),
    bots: zod_1.z.number().int().min(0).max(400),
    infiniteGold: zod_1.z.boolean(),
    infiniteTroops: zod_1.z.boolean(),
    instantBuild: zod_1.z.boolean(),
    maxPlayers: zod_1.z.number().optional(),
    disabledUnits: zod_1.z.enum(Game_1.UnitType).array().optional(),
    playerTeams: TeamCountConfigSchema.optional(),
});
exports.TeamSchema = zod_1.z.string();
const SafeString = zod_1.z
    .string()
    .regex(/^([a-zA-Z0-9\s.,!?@#$%&*()\-_+=[\]{}|;:"'/\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff]|[üÜ])*$/u)
    .max(1000);
exports.PersistentIdSchema = zod_1.z.uuid();
const JwtTokenSchema = zod_1.z.jwt();
const TokenSchema = zod_1.z
    .string()
    .refine((v) => exports.PersistentIdSchema.safeParse(v).success ||
    JwtTokenSchema.safeParse(v).success, {
    message: "Token must be a valid UUID or JWT",
});
const EmojiSchema = zod_1.z
    .number()
    .nonnegative()
    .max(Util_1.flattenedEmojiTable.length - 1);
exports.ID = zod_1.z
    .string()
    .regex(/^[a-zA-Z0-9]+$/)
    .length(8);
exports.AllPlayersStatsSchema = zod_1.z.record(exports.ID, StatsSchemas_1.PlayerStatsSchema);
exports.UsernameSchema = SafeString;
const countryCodes = countries_json_1.default.filter((c) => !c.restricted).map((c) => c.code);
exports.FlagSchema = zod_1.z
    .string()
    .max(128)
    .optional()
    .refine((val) => {
    if (val === undefined || val === "")
        return true;
    if (val.startsWith("!"))
        return true;
    return countryCodes.includes(val);
}, { message: "Invalid flag: must be a valid country code or start with !" });
exports.QuickChatKeySchema = zod_1.z.enum(Object.entries(QuickChat_json_1.default).flatMap(([category, entries]) => entries.map((entry) => `${category}.${entry.key}`)));
//
// Intents
//
const BaseIntentSchema = zod_1.z.object({
    clientID: exports.ID,
});
exports.AllianceExtensionIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("allianceExtension"),
    recipient: exports.ID,
});
exports.AttackIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("attack"),
    targetID: exports.ID.nullable(),
    troops: zod_1.z.number().nonnegative().nullable(),
});
exports.SpawnIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("spawn"),
    tile: zod_1.z.number(),
});
exports.BoatAttackIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("boat"),
    targetID: exports.ID.nullable(),
    troops: zod_1.z.number().nonnegative(),
    dst: zod_1.z.number(),
    src: zod_1.z.number().nullable(),
});
exports.AllianceRequestIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("allianceRequest"),
    recipient: exports.ID,
});
exports.AllianceRequestReplyIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("allianceRequestReply"),
    requestor: exports.ID, // The one who made the original alliance request
    accept: zod_1.z.boolean(),
});
exports.BreakAllianceIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("breakAlliance"),
    recipient: exports.ID,
});
exports.TargetPlayerIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("targetPlayer"),
    target: exports.ID,
});
exports.EmojiIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("emoji"),
    recipient: zod_1.z.union([exports.ID, zod_1.z.literal(Game_1.AllPlayers)]),
    emoji: EmojiSchema,
});
exports.EmbargoIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("embargo"),
    targetID: exports.ID,
    action: zod_1.z.union([zod_1.z.literal("start"), zod_1.z.literal("stop")]),
});
exports.DonateGoldIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("donate_gold"),
    recipient: exports.ID,
    gold: zod_1.z.bigint().nullable(),
});
exports.DonateTroopIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("donate_troops"),
    recipient: exports.ID,
    troops: zod_1.z.number().nullable(),
});
exports.BuildUnitIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("build_unit"),
    unit: zod_1.z.enum(Game_1.UnitType),
    tile: zod_1.z.number(),
});
exports.UpgradeStructureIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("upgrade_structure"),
    unit: zod_1.z.enum(Game_1.UnitType),
    unitId: zod_1.z.number(),
});
exports.CancelAttackIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("cancel_attack"),
    attackID: zod_1.z.string(),
});
exports.CancelBoatIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("cancel_boat"),
    unitID: zod_1.z.number(),
});
exports.MoveWarshipIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("move_warship"),
    unitId: zod_1.z.number(),
    tile: zod_1.z.number(),
});
exports.DeleteUnitIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("delete_unit"),
    unitId: zod_1.z.number(),
});
exports.QuickChatIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("quick_chat"),
    recipient: exports.ID,
    quickChatKey: exports.QuickChatKeySchema,
    target: exports.ID.optional(),
});
exports.MarkDisconnectedIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("mark_disconnected"),
    isDisconnected: zod_1.z.boolean(),
});
exports.KickPlayerIntentSchema = BaseIntentSchema.extend({
    type: zod_1.z.literal("kick_player"),
    target: exports.ID,
});
const IntentSchema = zod_1.z.discriminatedUnion("type", [
    exports.AttackIntentSchema,
    exports.CancelAttackIntentSchema,
    exports.SpawnIntentSchema,
    exports.MarkDisconnectedIntentSchema,
    exports.BoatAttackIntentSchema,
    exports.CancelBoatIntentSchema,
    exports.AllianceRequestIntentSchema,
    exports.AllianceRequestReplyIntentSchema,
    exports.BreakAllianceIntentSchema,
    exports.TargetPlayerIntentSchema,
    exports.EmojiIntentSchema,
    exports.DonateGoldIntentSchema,
    exports.DonateTroopIntentSchema,
    exports.BuildUnitIntentSchema,
    exports.UpgradeStructureIntentSchema,
    exports.EmbargoIntentSchema,
    exports.MoveWarshipIntentSchema,
    exports.QuickChatIntentSchema,
    exports.AllianceExtensionIntentSchema,
    exports.DeleteUnitIntentSchema,
    exports.KickPlayerIntentSchema,
]);
//
// Server utility types
//
exports.TurnSchema = zod_1.z.object({
    turnNumber: zod_1.z.number(),
    intents: IntentSchema.array(),
    // The hash of the game state at the end of the turn.
    hash: zod_1.z.number().nullable().optional(),
});
exports.PlayerSchema = zod_1.z.object({
    clientID: exports.ID,
    username: exports.UsernameSchema,
    flag: exports.FlagSchema,
    pattern: CosmeticSchemas_1.PatternSchema.optional(),
});
exports.GameStartInfoSchema = zod_1.z.object({
    gameID: exports.ID,
    config: exports.GameConfigSchema,
    players: exports.PlayerSchema.array(),
});
exports.WinnerSchema = zod_1.z
    .union([
    zod_1.z.tuple([zod_1.z.literal("player"), exports.ID]).rest(exports.ID),
    zod_1.z.tuple([zod_1.z.literal("team"), SafeString]).rest(exports.ID),
])
    .optional();
//
// Server
//
exports.ServerTurnMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("turn"),
    turn: exports.TurnSchema,
});
exports.ServerPingMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("ping"),
});
exports.ServerPrestartMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("prestart"),
    gameMap: zod_1.z.nativeEnum(Game_1.GameMapType),
});
exports.ServerStartGameMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("start"),
    // Turns the client missed if they are late to the game.
    turns: exports.TurnSchema.array(),
    gameStartInfo: exports.GameStartInfoSchema,
});
exports.ServerDesyncSchema = zod_1.z.object({
    type: zod_1.z.literal("desync"),
    turn: zod_1.z.number(),
    correctHash: zod_1.z.number().nullable(),
    clientsWithCorrectHash: zod_1.z.number(),
    totalActiveClients: zod_1.z.number(),
    yourHash: zod_1.z.number().optional(),
});
exports.ServerErrorSchema = zod_1.z.object({
    type: zod_1.z.literal("error"),
    error: zod_1.z.string(),
    message: zod_1.z.string().optional(),
});
exports.ServerMessageSchema = zod_1.z.discriminatedUnion("type", [
    exports.ServerTurnMessageSchema,
    exports.ServerPrestartMessageSchema,
    exports.ServerStartGameMessageSchema,
    exports.ServerPingMessageSchema,
    exports.ServerDesyncSchema,
    exports.ServerErrorSchema,
]);
//
// Client
//
exports.ClientSendWinnerSchema = zod_1.z.object({
    type: zod_1.z.literal("winner"),
    winner: exports.WinnerSchema,
    allPlayersStats: exports.AllPlayersStatsSchema,
});
exports.ClientHashSchema = zod_1.z.object({
    type: zod_1.z.literal("hash"),
    hash: zod_1.z.number(),
    turnNumber: zod_1.z.number(),
});
exports.ClientLogMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("log"),
    severity: zod_1.z.enum(LogSeverity),
    log: exports.ID,
});
exports.ClientPingMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("ping"),
});
exports.ClientIntentMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("intent"),
    intent: IntentSchema,
});
// WARNING: never send this message to clients.
exports.ClientJoinMessageSchema = zod_1.z.object({
    type: zod_1.z.literal("join"),
    clientID: exports.ID,
    token: TokenSchema, // WARNING: PII
    gameID: exports.ID,
    lastTurn: zod_1.z.number(), // The last turn the client saw.
    username: exports.UsernameSchema,
    flag: exports.FlagSchema,
    patternName: zod_1.z.string().optional(),
});
exports.ClientMessageSchema = zod_1.z.discriminatedUnion("type", [
    exports.ClientSendWinnerSchema,
    exports.ClientPingMessageSchema,
    exports.ClientIntentMessageSchema,
    exports.ClientJoinMessageSchema,
    exports.ClientLogMessageSchema,
    exports.ClientHashSchema,
]);
//
// Records
//
exports.PlayerRecordSchema = exports.PlayerSchema.extend({
    persistentID: exports.PersistentIdSchema, // WARNING: PII
    stats: StatsSchemas_1.PlayerStatsSchema,
});
exports.GameEndInfoSchema = exports.GameStartInfoSchema.extend({
    players: exports.PlayerRecordSchema.array(),
    start: zod_1.z.number(),
    end: zod_1.z.number(),
    duration: zod_1.z.number().nonnegative(),
    num_turns: zod_1.z.number(),
    winner: exports.WinnerSchema,
});
const GitCommitSchema = zod_1.z.string().regex(/^[0-9a-fA-F]{40}$/);
exports.AnalyticsRecordSchema = zod_1.z.object({
    info: exports.GameEndInfoSchema,
    version: zod_1.z.literal("v0.0.2"),
    gitCommit: GitCommitSchema,
    subdomain: zod_1.z.string(),
    domain: zod_1.z.string(),
});
exports.GameRecordSchema = exports.AnalyticsRecordSchema.extend({
    turns: exports.TurnSchema.array(),
});
