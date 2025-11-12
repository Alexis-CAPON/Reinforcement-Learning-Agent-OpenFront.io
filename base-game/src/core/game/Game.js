"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MESSAGE_TYPE_CATEGORIES = exports.MessageCategory = exports.MessageType = exports.PlayerInfo = exports.PlayerType = exports.TerrainType = exports.Cell = exports.Nation = exports.Relation = exports.nukeTypes = exports.TrainType = exports.UnitType = exports.GameMode = exports.GameType = exports.mapCategories = exports.GameMapType = exports.ColoredTeams = exports.Quads = exports.Trios = exports.Duos = exports.Difficulty = exports.AllPlayers = void 0;
exports.isStructureType = isStructureType;
exports.isUnit = isUnit;
exports.getMessageCategory = getMessageCategory;
exports.AllPlayers = "AllPlayers";
var Difficulty;
(function (Difficulty) {
    Difficulty["Easy"] = "Easy";
    Difficulty["Medium"] = "Medium";
    Difficulty["Hard"] = "Hard";
    Difficulty["Impossible"] = "Impossible";
})(Difficulty || (exports.Difficulty = Difficulty = {}));
exports.Duos = "Duos";
exports.Trios = "Trios";
exports.Quads = "Quads";
exports.ColoredTeams = {
    Red: "Red",
    Blue: "Blue",
    Teal: "Teal",
    Purple: "Purple",
    Yellow: "Yellow",
    Orange: "Orange",
    Green: "Green",
    Bot: "Bot",
};
var GameMapType;
(function (GameMapType) {
    GameMapType["World"] = "World";
    GameMapType["GiantWorldMap"] = "Giant World Map";
    GameMapType["Europe"] = "Europe";
    GameMapType["EuropeClassic"] = "Europe Classic";
    GameMapType["Mena"] = "Mena";
    GameMapType["NorthAmerica"] = "North America";
    GameMapType["SouthAmerica"] = "South America";
    GameMapType["Oceania"] = "Oceania";
    GameMapType["BlackSea"] = "Black Sea";
    GameMapType["Africa"] = "Africa";
    GameMapType["Pangaea"] = "Pangaea";
    GameMapType["Asia"] = "Asia";
    GameMapType["Mars"] = "Mars";
    GameMapType["Britannia"] = "Britannia";
    GameMapType["GatewayToTheAtlantic"] = "Gateway to the Atlantic";
    GameMapType["Australia"] = "Australia";
    GameMapType["Iceland"] = "Iceland";
    GameMapType["EastAsia"] = "East Asia";
    GameMapType["BetweenTwoSeas"] = "Between Two Seas";
    GameMapType["FaroeIslands"] = "Faroe Islands";
    GameMapType["DeglaciatedAntarctica"] = "Deglaciated Antarctica";
    GameMapType["FalklandIslands"] = "Falkland Islands";
    GameMapType["Baikal"] = "Baikal";
    GameMapType["Halkidiki"] = "Halkidiki";
    GameMapType["StraitOfGibraltar"] = "Strait of Gibraltar";
    GameMapType["Italia"] = "Italia";
    GameMapType["Yenisei"] = "Yenisei";
    GameMapType["Pluto"] = "Pluto";
})(GameMapType || (exports.GameMapType = GameMapType = {}));
exports.mapCategories = {
    continental: [
        GameMapType.World,
        GameMapType.GiantWorldMap,
        GameMapType.NorthAmerica,
        GameMapType.SouthAmerica,
        GameMapType.Europe,
        GameMapType.EuropeClassic,
        GameMapType.Asia,
        GameMapType.Africa,
        GameMapType.Oceania,
    ],
    regional: [
        GameMapType.BlackSea,
        GameMapType.Britannia,
        GameMapType.GatewayToTheAtlantic,
        GameMapType.BetweenTwoSeas,
        GameMapType.Iceland,
        GameMapType.EastAsia,
        GameMapType.Mena,
        GameMapType.Australia,
        GameMapType.FaroeIslands,
        GameMapType.FalklandIslands,
        GameMapType.Baikal,
        GameMapType.Halkidiki,
        GameMapType.StraitOfGibraltar,
        GameMapType.Italia,
        GameMapType.Yenisei,
    ],
    fantasy: [
        GameMapType.Pangaea,
        GameMapType.Pluto,
        GameMapType.Mars,
        GameMapType.DeglaciatedAntarctica,
    ],
};
var GameType;
(function (GameType) {
    GameType["Singleplayer"] = "Singleplayer";
    GameType["Public"] = "Public";
    GameType["Private"] = "Private";
})(GameType || (exports.GameType = GameType = {}));
var GameMode;
(function (GameMode) {
    GameMode["FFA"] = "Free For All";
    GameMode["Team"] = "Team";
})(GameMode || (exports.GameMode = GameMode = {}));
var UnitType;
(function (UnitType) {
    UnitType["TransportShip"] = "Transport";
    UnitType["Warship"] = "Warship";
    UnitType["Shell"] = "Shell";
    UnitType["SAMMissile"] = "SAMMissile";
    UnitType["Port"] = "Port";
    UnitType["AtomBomb"] = "Atom Bomb";
    UnitType["HydrogenBomb"] = "Hydrogen Bomb";
    UnitType["TradeShip"] = "Trade Ship";
    UnitType["MissileSilo"] = "Missile Silo";
    UnitType["DefensePost"] = "Defense Post";
    UnitType["SAMLauncher"] = "SAM Launcher";
    UnitType["City"] = "City";
    UnitType["MIRV"] = "MIRV";
    UnitType["MIRVWarhead"] = "MIRV Warhead";
    UnitType["Construction"] = "Construction";
    UnitType["Train"] = "Train";
    UnitType["Factory"] = "Factory";
})(UnitType || (exports.UnitType = UnitType = {}));
var TrainType;
(function (TrainType) {
    TrainType["Engine"] = "Engine";
    TrainType["Carriage"] = "Carriage";
})(TrainType || (exports.TrainType = TrainType = {}));
const _structureTypes = new Set([
    UnitType.City,
    UnitType.Construction,
    UnitType.DefensePost,
    UnitType.SAMLauncher,
    UnitType.MissileSilo,
    UnitType.Port,
]);
function isStructureType(type) {
    return _structureTypes.has(type);
}
exports.nukeTypes = [
    UnitType.AtomBomb,
    UnitType.HydrogenBomb,
    UnitType.MIRVWarhead,
    UnitType.MIRV,
];
var Relation;
(function (Relation) {
    Relation[Relation["Hostile"] = 0] = "Hostile";
    Relation[Relation["Distrustful"] = 1] = "Distrustful";
    Relation[Relation["Neutral"] = 2] = "Neutral";
    Relation[Relation["Friendly"] = 3] = "Friendly";
})(Relation || (exports.Relation = Relation = {}));
class Nation {
    constructor(spawnCell, strength, playerInfo) {
        this.spawnCell = spawnCell;
        this.strength = strength;
        this.playerInfo = playerInfo;
    }
}
exports.Nation = Nation;
class Cell {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.strRepr = `Cell[${this.x},${this.y}]`;
    }
    pos() {
        return {
            x: this.x,
            y: this.y,
        };
    }
    toString() {
        return this.strRepr;
    }
}
exports.Cell = Cell;
var TerrainType;
(function (TerrainType) {
    TerrainType[TerrainType["Plains"] = 0] = "Plains";
    TerrainType[TerrainType["Highland"] = 1] = "Highland";
    TerrainType[TerrainType["Mountain"] = 2] = "Mountain";
    TerrainType[TerrainType["Lake"] = 3] = "Lake";
    TerrainType[TerrainType["Ocean"] = 4] = "Ocean";
})(TerrainType || (exports.TerrainType = TerrainType = {}));
var PlayerType;
(function (PlayerType) {
    PlayerType["Bot"] = "BOT";
    PlayerType["Human"] = "HUMAN";
    PlayerType["FakeHuman"] = "FAKEHUMAN";
})(PlayerType || (exports.PlayerType = PlayerType = {}));
class PlayerInfo {
    constructor(name, playerType, 
    // null if bot.
    clientID, 
    // TODO: make player id the small id
    id, nation) {
        this.name = name;
        this.playerType = playerType;
        this.clientID = clientID;
        this.id = id;
        this.nation = nation;
        // Compute clan from name
        if (!name.startsWith("[") || !name.includes("]")) {
            this.clan = null;
        }
        else {
            const clanMatch = name.match(/^\[([a-zA-Z]{2,5})\]/);
            this.clan = clanMatch ? clanMatch[1] : null;
        }
    }
}
exports.PlayerInfo = PlayerInfo;
function isUnit(unit) {
    return (unit &&
        typeof unit === "object" &&
        "isUnit" in unit &&
        typeof unit.isUnit === "function" &&
        unit.isUnit());
}
var MessageType;
(function (MessageType) {
    MessageType[MessageType["ATTACK_FAILED"] = 0] = "ATTACK_FAILED";
    MessageType[MessageType["ATTACK_CANCELLED"] = 1] = "ATTACK_CANCELLED";
    MessageType[MessageType["ATTACK_REQUEST"] = 2] = "ATTACK_REQUEST";
    MessageType[MessageType["CONQUERED_PLAYER"] = 3] = "CONQUERED_PLAYER";
    MessageType[MessageType["MIRV_INBOUND"] = 4] = "MIRV_INBOUND";
    MessageType[MessageType["NUKE_INBOUND"] = 5] = "NUKE_INBOUND";
    MessageType[MessageType["HYDROGEN_BOMB_INBOUND"] = 6] = "HYDROGEN_BOMB_INBOUND";
    MessageType[MessageType["NAVAL_INVASION_INBOUND"] = 7] = "NAVAL_INVASION_INBOUND";
    MessageType[MessageType["SAM_MISS"] = 8] = "SAM_MISS";
    MessageType[MessageType["SAM_HIT"] = 9] = "SAM_HIT";
    MessageType[MessageType["CAPTURED_ENEMY_UNIT"] = 10] = "CAPTURED_ENEMY_UNIT";
    MessageType[MessageType["UNIT_CAPTURED_BY_ENEMY"] = 11] = "UNIT_CAPTURED_BY_ENEMY";
    MessageType[MessageType["UNIT_DESTROYED"] = 12] = "UNIT_DESTROYED";
    MessageType[MessageType["ALLIANCE_ACCEPTED"] = 13] = "ALLIANCE_ACCEPTED";
    MessageType[MessageType["ALLIANCE_REJECTED"] = 14] = "ALLIANCE_REJECTED";
    MessageType[MessageType["ALLIANCE_REQUEST"] = 15] = "ALLIANCE_REQUEST";
    MessageType[MessageType["ALLIANCE_BROKEN"] = 16] = "ALLIANCE_BROKEN";
    MessageType[MessageType["ALLIANCE_EXPIRED"] = 17] = "ALLIANCE_EXPIRED";
    MessageType[MessageType["SENT_GOLD_TO_PLAYER"] = 18] = "SENT_GOLD_TO_PLAYER";
    MessageType[MessageType["RECEIVED_GOLD_FROM_PLAYER"] = 19] = "RECEIVED_GOLD_FROM_PLAYER";
    MessageType[MessageType["RECEIVED_GOLD_FROM_TRADE"] = 20] = "RECEIVED_GOLD_FROM_TRADE";
    MessageType[MessageType["SENT_TROOPS_TO_PLAYER"] = 21] = "SENT_TROOPS_TO_PLAYER";
    MessageType[MessageType["RECEIVED_TROOPS_FROM_PLAYER"] = 22] = "RECEIVED_TROOPS_FROM_PLAYER";
    MessageType[MessageType["CHAT"] = 23] = "CHAT";
    MessageType[MessageType["RENEW_ALLIANCE"] = 24] = "RENEW_ALLIANCE";
})(MessageType || (exports.MessageType = MessageType = {}));
// Message categories used for filtering events in the EventsDisplay
var MessageCategory;
(function (MessageCategory) {
    MessageCategory["ATTACK"] = "ATTACK";
    MessageCategory["ALLIANCE"] = "ALLIANCE";
    MessageCategory["TRADE"] = "TRADE";
    MessageCategory["CHAT"] = "CHAT";
})(MessageCategory || (exports.MessageCategory = MessageCategory = {}));
// Ensures that all message types are included in a category
exports.MESSAGE_TYPE_CATEGORIES = {
    [MessageType.ATTACK_FAILED]: MessageCategory.ATTACK,
    [MessageType.ATTACK_CANCELLED]: MessageCategory.ATTACK,
    [MessageType.ATTACK_REQUEST]: MessageCategory.ATTACK,
    [MessageType.CONQUERED_PLAYER]: MessageCategory.ATTACK,
    [MessageType.MIRV_INBOUND]: MessageCategory.ATTACK,
    [MessageType.NUKE_INBOUND]: MessageCategory.ATTACK,
    [MessageType.HYDROGEN_BOMB_INBOUND]: MessageCategory.ATTACK,
    [MessageType.NAVAL_INVASION_INBOUND]: MessageCategory.ATTACK,
    [MessageType.SAM_MISS]: MessageCategory.ATTACK,
    [MessageType.SAM_HIT]: MessageCategory.ATTACK,
    [MessageType.CAPTURED_ENEMY_UNIT]: MessageCategory.ATTACK,
    [MessageType.UNIT_CAPTURED_BY_ENEMY]: MessageCategory.ATTACK,
    [MessageType.UNIT_DESTROYED]: MessageCategory.ATTACK,
    [MessageType.ALLIANCE_ACCEPTED]: MessageCategory.ALLIANCE,
    [MessageType.ALLIANCE_REJECTED]: MessageCategory.ALLIANCE,
    [MessageType.ALLIANCE_REQUEST]: MessageCategory.ALLIANCE,
    [MessageType.ALLIANCE_BROKEN]: MessageCategory.ALLIANCE,
    [MessageType.ALLIANCE_EXPIRED]: MessageCategory.ALLIANCE,
    [MessageType.RENEW_ALLIANCE]: MessageCategory.ALLIANCE,
    [MessageType.SENT_GOLD_TO_PLAYER]: MessageCategory.TRADE,
    [MessageType.RECEIVED_GOLD_FROM_PLAYER]: MessageCategory.TRADE,
    [MessageType.RECEIVED_GOLD_FROM_TRADE]: MessageCategory.TRADE,
    [MessageType.SENT_TROOPS_TO_PLAYER]: MessageCategory.TRADE,
    [MessageType.RECEIVED_TROOPS_FROM_PLAYER]: MessageCategory.TRADE,
    [MessageType.CHAT]: MessageCategory.CHAT,
};
/**
 * Get the category of a message type
 */
function getMessageCategory(messageType) {
    return exports.MESSAGE_TYPE_CATEGORIES[messageType];
}
