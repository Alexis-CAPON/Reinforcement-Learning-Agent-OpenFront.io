"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefaultConfig = exports.DefaultServerConfig = void 0;
const zod_1 = require("zod");
const Game_1 = require("../game/Game");
const Util_1 = require("../Util");
const Config_1 = require("./Config");
const PastelTheme_1 = require("./PastelTheme");
const PastelThemeDark_1 = require("./PastelThemeDark");
const DEFENSE_DEBUFF_MIDPOINT = 150000;
const DEFENSE_DEBUFF_DECAY_RATE = Math.LN2 / 50000;
const JwksSchema = zod_1.z.object({
    keys: zod_1.z
        .object({
        alg: zod_1.z.literal("EdDSA"),
        crv: zod_1.z.literal("Ed25519"),
        kty: zod_1.z.literal("OKP"),
        x: zod_1.z.string(),
    })
        .array()
        .min(1),
});
const numPlayersConfig = {
    [Game_1.GameMapType.GatewayToTheAtlantic]: [80, 60, 40],
    [Game_1.GameMapType.SouthAmerica]: [70, 50, 40],
    [Game_1.GameMapType.NorthAmerica]: [80, 60, 50],
    [Game_1.GameMapType.Africa]: [100, 80, 50],
    [Game_1.GameMapType.Europe]: [80, 50, 30],
    [Game_1.GameMapType.Australia]: [50, 40, 30],
    [Game_1.GameMapType.Iceland]: [50, 40, 30],
    [Game_1.GameMapType.Britannia]: [50, 40, 30],
    [Game_1.GameMapType.Asia]: [60, 50, 30],
    [Game_1.GameMapType.FalklandIslands]: [80, 50, 30],
    [Game_1.GameMapType.Baikal]: [60, 50, 40],
    [Game_1.GameMapType.Mena]: [60, 50, 30],
    [Game_1.GameMapType.Mars]: [50, 40, 30],
    [Game_1.GameMapType.Oceania]: [30, 20, 10],
    [Game_1.GameMapType.EastAsia]: [50, 40, 30],
    [Game_1.GameMapType.FaroeIslands]: [50, 40, 30],
    [Game_1.GameMapType.DeglaciatedAntarctica]: [50, 40, 30],
    [Game_1.GameMapType.EuropeClassic]: [80, 30, 50],
    [Game_1.GameMapType.BetweenTwoSeas]: [40, 50, 30],
    [Game_1.GameMapType.BlackSea]: [40, 50, 30],
    [Game_1.GameMapType.Pangaea]: [40, 20, 30],
    [Game_1.GameMapType.World]: [150, 80, 50],
    [Game_1.GameMapType.GiantWorldMap]: [150, 100, 60],
    [Game_1.GameMapType.Halkidiki]: [50, 40, 30],
    [Game_1.GameMapType.StraitOfGibraltar]: [50, 40, 30],
    [Game_1.GameMapType.Italia]: [50, 40, 30],
    [Game_1.GameMapType.Pluto]: [70, 50, 40],
    [Game_1.GameMapType.Yenisei]: [60, 50, 40],
};
class DefaultServerConfig {
    allowedFlares() {
        return;
    }
    stripePublishableKey() {
        var _a;
        return (_a = process.env.STRIPE_PUBLISHABLE_KEY) !== null && _a !== void 0 ? _a : "";
    }
    domain() {
        var _a;
        return (_a = process.env.DOMAIN) !== null && _a !== void 0 ? _a : "";
    }
    subdomain() {
        var _a;
        return (_a = process.env.SUBDOMAIN) !== null && _a !== void 0 ? _a : "";
    }
    cloudflareAccountId() {
        var _a;
        return (_a = process.env.CF_ACCOUNT_ID) !== null && _a !== void 0 ? _a : "";
    }
    cloudflareApiToken() {
        var _a;
        return (_a = process.env.CF_API_TOKEN) !== null && _a !== void 0 ? _a : "";
    }
    cloudflareConfigPath() {
        var _a;
        return (_a = process.env.CF_CONFIG_PATH) !== null && _a !== void 0 ? _a : "";
    }
    cloudflareCredsPath() {
        var _a;
        return (_a = process.env.CF_CREDS_PATH) !== null && _a !== void 0 ? _a : "";
    }
    jwtIssuer() {
        const audience = this.jwtAudience();
        return audience === "localhost"
            ? "http://localhost:8787"
            : `https://api.${audience}`;
    }
    jwkPublicKey() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.publicKey)
                return this.publicKey;
            const jwksUrl = this.jwtIssuer() + "/.well-known/jwks.json";
            console.log(`Fetching JWKS from ${jwksUrl}`);
            const response = yield fetch(jwksUrl);
            const result = JwksSchema.safeParse(yield response.json());
            if (!result.success) {
                const error = zod_1.z.prettifyError(result.error);
                console.error("Error parsing JWKS", error);
                throw new Error("Invalid JWKS");
            }
            this.publicKey = result.data.keys[0];
            return this.publicKey;
        });
    }
    otelEnabled() {
        return (this.env() !== Config_1.GameEnv.Dev &&
            Boolean(this.otelEndpoint()) &&
            Boolean(this.otelAuthHeader()));
    }
    otelEndpoint() {
        var _a;
        return (_a = process.env.OTEL_EXPORTER_OTLP_ENDPOINT) !== null && _a !== void 0 ? _a : "";
    }
    otelAuthHeader() {
        var _a;
        return (_a = process.env.OTEL_AUTH_HEADER) !== null && _a !== void 0 ? _a : "";
    }
    gitCommit() {
        var _a;
        return (_a = process.env.GIT_COMMIT) !== null && _a !== void 0 ? _a : "";
    }
    r2Endpoint() {
        return `https://${process.env.CF_ACCOUNT_ID}.r2.cloudflarestorage.com`;
    }
    r2AccessKey() {
        var _a;
        return (_a = process.env.R2_ACCESS_KEY) !== null && _a !== void 0 ? _a : "";
    }
    r2SecretKey() {
        var _a;
        return (_a = process.env.R2_SECRET_KEY) !== null && _a !== void 0 ? _a : "";
    }
    r2Bucket() {
        var _a;
        return (_a = process.env.R2_BUCKET) !== null && _a !== void 0 ? _a : "";
    }
    adminHeader() {
        return "x-admin-key";
    }
    adminToken() {
        var _a;
        return (_a = process.env.ADMIN_TOKEN) !== null && _a !== void 0 ? _a : "dummy-admin-token";
    }
    turnIntervalMs() {
        return 100;
    }
    gameCreationRate() {
        return 60 * 1000;
    }
    lobbyMaxPlayers(map, mode, numPlayerTeams) {
        var _a;
        const [l, m, s] = (_a = numPlayersConfig[map]) !== null && _a !== void 0 ? _a : [50, 30, 20];
        const r = Math.random();
        const base = r < 0.3 ? l : r < 0.6 ? m : s;
        let p = Math.min(mode === Game_1.GameMode.Team ? Math.ceil(base * 1.5) : base, l);
        if (numPlayerTeams === undefined)
            return p;
        switch (numPlayerTeams) {
            case Game_1.Duos:
                p -= p % 2;
                break;
            case Game_1.Trios:
                p -= p % 3;
                break;
            case Game_1.Quads:
                p -= p % 4;
                break;
            default:
                p -= p % numPlayerTeams;
                break;
        }
        return p;
    }
    workerIndex(gameID) {
        return (0, Util_1.simpleHash)(gameID) % this.numWorkers();
    }
    workerPath(gameID) {
        return `w${this.workerIndex(gameID)}`;
    }
    workerPort(gameID) {
        return this.workerPortByIndex(this.workerIndex(gameID));
    }
    workerPortByIndex(index) {
        return 3001 + index;
    }
}
exports.DefaultServerConfig = DefaultServerConfig;
class DefaultConfig {
    constructor(_serverConfig, _gameConfig, _userSettings, _isReplay) {
        this._serverConfig = _serverConfig;
        this._gameConfig = _gameConfig;
        this._userSettings = _userSettings;
        this._isReplay = _isReplay;
        this.pastelTheme = new PastelTheme_1.PastelTheme();
        this.pastelThemeDark = new PastelThemeDark_1.PastelThemeDark();
    }
    stripePublishableKey() {
        var _a;
        return (_a = process.env.STRIPE_PUBLISHABLE_KEY) !== null && _a !== void 0 ? _a : "";
    }
    isReplay() {
        return this._isReplay;
    }
    samHittingChance() {
        return 0.8;
    }
    samWarheadHittingChance() {
        return 0.5;
    }
    traitorDefenseDebuff() {
        return 0.5;
    }
    traitorSpeedDebuff() {
        return 0.8;
    }
    traitorDuration() {
        return 30 * 10; // 30 seconds
    }
    spawnImmunityDuration() {
        return 5 * 10;
    }
    gameConfig() {
        return this._gameConfig;
    }
    serverConfig() {
        return this._serverConfig;
    }
    userSettings() {
        if (this._userSettings === null) {
            throw new Error("userSettings is null");
        }
        return this._userSettings;
    }
    difficultyModifier(difficulty) {
        switch (difficulty) {
            case Game_1.Difficulty.Easy:
                return 1;
            case Game_1.Difficulty.Medium:
                return 3;
            case Game_1.Difficulty.Hard:
                return 9;
            case Game_1.Difficulty.Impossible:
                return 18;
        }
    }
    cityTroopIncrease() {
        return 250000;
    }
    falloutDefenseModifier(falloutRatio) {
        // falloutRatio is between 0 and 1
        // So defense modifier is between [5, 2.5]
        return 5 - falloutRatio * 2;
    }
    SAMCooldown() {
        return 75;
    }
    SiloCooldown() {
        return 75;
    }
    defensePostRange() {
        return 30;
    }
    defensePostDefenseBonus() {
        return 5;
    }
    defensePostSpeedBonus() {
        return 3;
    }
    playerTeams() {
        var _a;
        return (_a = this._gameConfig.playerTeams) !== null && _a !== void 0 ? _a : 0;
    }
    spawnNPCs() {
        return !this._gameConfig.disableNPCs;
    }
    isUnitDisabled(unitType) {
        var _a, _b;
        return (_b = (_a = this._gameConfig.disabledUnits) === null || _a === void 0 ? void 0 : _a.includes(unitType)) !== null && _b !== void 0 ? _b : false;
    }
    bots() {
        return this._gameConfig.bots;
    }
    instantBuild() {
        return this._gameConfig.instantBuild;
    }
    infiniteGold() {
        return this._gameConfig.infiniteGold;
    }
    donateGold() {
        return this._gameConfig.donateGold;
    }
    infiniteTroops() {
        return this._gameConfig.infiniteTroops;
    }
    donateTroops() {
        return this._gameConfig.donateTroops;
    }
    trainSpawnRate(numPlayerFactories) {
        // hyperbolic decay, midpoint at 10 factories
        // expected number of trains = numPlayerFactories  / trainSpawnRate(numPlayerFactories)
        return (numPlayerFactories + 10) * 20;
    }
    trainGold(rel) {
        switch (rel) {
            case "ally":
                return 50000n;
            case "team":
            case "other":
                return 25000n;
            case "self":
                return 10000n;
        }
    }
    trainStationMinRange() {
        return 15;
    }
    trainStationMaxRange() {
        return 100;
    }
    railroadMaxSize() {
        return 120;
    }
    tradeShipGold(dist, numPorts) {
        const baseGold = Math.floor(100000 + 100 * dist);
        const numPortBonus = numPorts - 1;
        // Hyperbolic decay, midpoint at 5 ports, 3x bonus max.
        const bonus = 1 + 2 * (numPortBonus / (numPortBonus + 5));
        return BigInt(Math.floor(baseGold * bonus));
    }
    // Probability of trade ship spawn = 1 / tradeShipSpawnRate
    tradeShipSpawnRate(numTradeShips, numPlayerPorts, numPlayerTradeShips) {
        // Geometric mean of base spawn rate and port multiplier
        const combined = Math.sqrt(this.tradeShipBaseSpawn(numTradeShips, numPlayerTradeShips) *
            this.tradeShipPortMultiplier(numPlayerPorts));
        return Math.floor(25 / combined);
    }
    tradeShipBaseSpawn(numTradeShips, numPlayerTradeShips) {
        if (numPlayerTradeShips < 3) {
            // If other players have many ports, then they can starve out smaller players.
            // So this prevents smaller players from being completely starved out.
            return 1;
        }
        const decayRate = Math.LN2 / 10;
        return 1 - (0, Util_1.sigmoid)(numTradeShips, decayRate, 55);
    }
    tradeShipPortMultiplier(numPlayerPorts) {
        // Hyperbolic decay function with midpoint at 10 ports
        // Expected trade ship spawn rate is proportional to numPlayerPorts * multiplier
        // Gradual decay prevents scenario where more ports => fewer ships
        const decayRate = 1 / 10;
        return 1 / (1 + decayRate * numPlayerPorts);
    }
    unitInfo(type) {
        switch (type) {
            case Game_1.UnitType.TransportShip:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                };
            case Game_1.UnitType.Warship:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(1000000, (numUnits + 1) * 250000), Game_1.UnitType.Warship),
                    territoryBound: false,
                    maxHealth: 1000,
                };
            case Game_1.UnitType.Shell:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                    damage: 250,
                };
            case Game_1.UnitType.SAMMissile:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                };
            case Game_1.UnitType.Port:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(1000000, Math.pow(2, numUnits) * 125000), Game_1.UnitType.Port, Game_1.UnitType.Factory),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 2 * 10,
                    upgradable: true,
                    canBuildTrainStation: true,
                };
            case Game_1.UnitType.AtomBomb:
                return {
                    cost: this.costWrapper(() => 750000, Game_1.UnitType.AtomBomb),
                    territoryBound: false,
                };
            case Game_1.UnitType.HydrogenBomb:
                return {
                    cost: this.costWrapper(() => 5000000, Game_1.UnitType.HydrogenBomb),
                    territoryBound: false,
                };
            case Game_1.UnitType.MIRV:
                return {
                    cost: this.costWrapper(() => 35000000, Game_1.UnitType.MIRV),
                    territoryBound: false,
                };
            case Game_1.UnitType.MIRVWarhead:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                };
            case Game_1.UnitType.TradeShip:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                };
            case Game_1.UnitType.MissileSilo:
                return {
                    cost: this.costWrapper(() => 1000000, Game_1.UnitType.MissileSilo),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 10 * 10,
                    upgradable: true,
                };
            case Game_1.UnitType.DefensePost:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(250000, (numUnits + 1) * 50000), Game_1.UnitType.DefensePost),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 5 * 10,
                };
            case Game_1.UnitType.SAMLauncher:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(3000000, (numUnits + 1) * 1500000), Game_1.UnitType.SAMLauncher),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 30 * 10,
                    upgradable: true,
                };
            case Game_1.UnitType.City:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(1000000, Math.pow(2, numUnits) * 125000), Game_1.UnitType.City),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 2 * 10,
                    upgradable: true,
                    canBuildTrainStation: true,
                };
            case Game_1.UnitType.Factory:
                return {
                    cost: this.costWrapper((numUnits) => Math.min(1000000, Math.pow(2, numUnits) * 125000), Game_1.UnitType.Factory, Game_1.UnitType.Port),
                    territoryBound: true,
                    constructionDuration: this.instantBuild() ? 0 : 2 * 10,
                    canBuildTrainStation: true,
                    experimental: true,
                    upgradable: true,
                };
            case Game_1.UnitType.Construction:
                return {
                    cost: () => 0n,
                    territoryBound: true,
                };
            case Game_1.UnitType.Train:
                return {
                    cost: () => 0n,
                    territoryBound: false,
                    experimental: true,
                };
            default:
                (0, Util_1.assertNever)(type);
        }
    }
    costWrapper(costFn, ...types) {
        return (p) => {
            if (p.type() === Game_1.PlayerType.Human && this.infiniteGold()) {
                return 0n;
            }
            const numUnits = types.reduce((acc, type) => acc + Math.min(p.unitsOwned(type), p.unitsConstructed(type)), 0);
            return BigInt(costFn(numUnits));
        };
    }
    defaultDonationAmount(sender) {
        return Math.floor(sender.troops() / 3);
    }
    donateCooldown() {
        return 10 * 10;
    }
    deleteUnitCooldown() {
        return 5 * 10;
    }
    emojiMessageDuration() {
        return 5 * 10;
    }
    emojiMessageCooldown() {
        return 5 * 10;
    }
    targetDuration() {
        return 10 * 10;
    }
    targetCooldown() {
        return 15 * 10;
    }
    allianceRequestDuration() {
        return 20 * 10;
    }
    allianceRequestCooldown() {
        return 30 * 10;
    }
    allianceDuration() {
        return 300 * 10; // 5 minutes.
    }
    temporaryEmbargoDuration() {
        return 300 * 10; // 5 minutes.
    }
    percentageTilesOwnedToWin() {
        if (this._gameConfig.gameMode === Game_1.GameMode.Team) {
            return 95;
        }
        return 80;
    }
    boatMaxNumber() {
        return 3;
    }
    numSpawnPhaseTurns() {
        return this._gameConfig.gameType === Game_1.GameType.Singleplayer ? 100 : 300;
    }
    numBots() {
        return this.bots();
    }
    theme() {
        var _a;
        return ((_a = this.userSettings()) === null || _a === void 0 ? void 0 : _a.darkMode())
            ? this.pastelThemeDark
            : this.pastelTheme;
    }
    attackLogic(gm, attackTroops, attacker, defender, tileToConquer) {
        let mag = 0;
        let speed = 0;
        const type = gm.terrainType(tileToConquer);
        switch (type) {
            case Game_1.TerrainType.Plains:
                mag = 80;
                speed = 16.5;
                break;
            case Game_1.TerrainType.Highland:
                mag = 100;
                speed = 20;
                break;
            case Game_1.TerrainType.Mountain:
                mag = 120;
                speed = 25;
                break;
            default:
                throw new Error(`terrain type ${type} not supported`);
        }
        if (defender.isPlayer()) {
            for (const dp of gm.nearbyUnits(tileToConquer, gm.config().defensePostRange(), Game_1.UnitType.DefensePost)) {
                if (dp.unit.owner() === defender) {
                    mag *= this.defensePostDefenseBonus();
                    speed *= this.defensePostSpeedBonus();
                    break;
                }
            }
        }
        if (gm.hasFallout(tileToConquer)) {
            const falloutRatio = gm.numTilesWithFallout() / gm.numLandTiles();
            mag *= this.falloutDefenseModifier(falloutRatio);
            speed *= this.falloutDefenseModifier(falloutRatio);
        }
        if (attacker.isPlayer() && defender.isPlayer()) {
            if (attacker.type() === Game_1.PlayerType.Human &&
                defender.type() === Game_1.PlayerType.Bot) {
                mag *= 0.8;
            }
            if (attacker.type() === Game_1.PlayerType.FakeHuman &&
                defender.type() === Game_1.PlayerType.Bot) {
                mag *= 0.8;
            }
        }
        if (defender.isPlayer()) {
            const defenseSig = 1 -
                (0, Util_1.sigmoid)(defender.numTilesOwned(), DEFENSE_DEBUFF_DECAY_RATE, DEFENSE_DEBUFF_MIDPOINT);
            const largeDefenderSpeedDebuff = 0.7 + 0.3 * defenseSig;
            const largeDefenderAttackDebuff = 0.7 + 0.3 * defenseSig;
            let largeAttackBonus = 1;
            if (attacker.numTilesOwned() > 100000) {
                largeAttackBonus = Math.pow(Math.sqrt(100000 / attacker.numTilesOwned()), 0.7);
            }
            let largeAttackerSpeedBonus = 1;
            if (attacker.numTilesOwned() > 100000) {
                largeAttackerSpeedBonus = Math.pow((100000 / attacker.numTilesOwned()), 0.6);
            }
            return {
                attackerTroopLoss: (0, Util_1.within)(defender.troops() / attackTroops, 0.6, 2) *
                    mag *
                    0.8 *
                    largeDefenderAttackDebuff *
                    largeAttackBonus *
                    (defender.isTraitor() ? this.traitorDefenseDebuff() : 1),
                defenderTroopLoss: defender.troops() / defender.numTilesOwned(),
                tilesPerTickUsed: (0, Util_1.within)(defender.troops() / (5 * attackTroops), 0.2, 1.5) *
                    speed *
                    largeDefenderSpeedDebuff *
                    largeAttackerSpeedBonus *
                    (defender.isTraitor() ? this.traitorSpeedDebuff() : 1),
            };
        }
        else {
            return {
                attackerTroopLoss: attacker.type() === Game_1.PlayerType.Bot ? mag / 10 : mag / 5,
                defenderTroopLoss: 0,
                tilesPerTickUsed: (0, Util_1.within)((2000 * Math.max(10, speed)) / attackTroops, 5, 100),
            };
        }
    }
    attackTilesPerTick(attackTroops, attacker, defender, numAdjacentTilesWithEnemy) {
        if (defender.isPlayer()) {
            return ((0, Util_1.within)(((5 * attackTroops) / defender.troops()) * 2, 0.01, 0.5) *
                numAdjacentTilesWithEnemy *
                3);
        }
        else {
            return numAdjacentTilesWithEnemy * 2;
        }
    }
    boatAttackAmount(attacker, defender) {
        return Math.floor(attacker.troops() / 5);
    }
    warshipShellLifetime() {
        return 20; // in ticks (one tick is 100ms)
    }
    radiusPortSpawn() {
        return 20;
    }
    proximityBonusPortsNb(totalPorts) {
        return (0, Util_1.within)(totalPorts / 3, 4, totalPorts);
    }
    attackAmount(attacker, defender) {
        if (attacker.type() === Game_1.PlayerType.Bot) {
            return attacker.troops() / 20;
        }
        else {
            return attacker.troops() / 5;
        }
    }
    startManpower(playerInfo) {
        var _a, _b, _c, _d, _e, _f, _g, _h;
        if (playerInfo.playerType === Game_1.PlayerType.Bot) {
            return 10000;
        }
        if (playerInfo.playerType === Game_1.PlayerType.FakeHuman) {
            switch (this._gameConfig.difficulty) {
                case Game_1.Difficulty.Easy:
                    return 2500 * ((_b = (_a = playerInfo === null || playerInfo === void 0 ? void 0 : playerInfo.nation) === null || _a === void 0 ? void 0 : _a.strength) !== null && _b !== void 0 ? _b : 1);
                case Game_1.Difficulty.Medium:
                    return 5000 * ((_d = (_c = playerInfo === null || playerInfo === void 0 ? void 0 : playerInfo.nation) === null || _c === void 0 ? void 0 : _c.strength) !== null && _d !== void 0 ? _d : 1);
                case Game_1.Difficulty.Hard:
                    return 20000 * ((_f = (_e = playerInfo === null || playerInfo === void 0 ? void 0 : playerInfo.nation) === null || _e === void 0 ? void 0 : _e.strength) !== null && _f !== void 0 ? _f : 1);
                case Game_1.Difficulty.Impossible:
                    return 50000 * ((_h = (_g = playerInfo === null || playerInfo === void 0 ? void 0 : playerInfo.nation) === null || _g === void 0 ? void 0 : _g.strength) !== null && _h !== void 0 ? _h : 1);
            }
        }
        return this.infiniteTroops() ? 1000000 : 25000;
    }
    maxTroops(player) {
        const maxTroops = player.type() === Game_1.PlayerType.Human && this.infiniteTroops()
            ? 1000000000
            : 2 * (Math.pow(player.numTilesOwned(), 0.6) * 1000 + 50000) +
                player
                    .units(Game_1.UnitType.City)
                    .map((city) => city.level())
                    .reduce((a, b) => a + b, 0) *
                    this.cityTroopIncrease();
        if (player.type() === Game_1.PlayerType.Bot) {
            return maxTroops / 3;
        }
        if (player.type() === Game_1.PlayerType.Human) {
            return maxTroops;
        }
        switch (this._gameConfig.difficulty) {
            case Game_1.Difficulty.Easy:
                return maxTroops * 0.5;
            case Game_1.Difficulty.Medium:
                return maxTroops * 1;
            case Game_1.Difficulty.Hard:
                return maxTroops * 1.5;
            case Game_1.Difficulty.Impossible:
                return maxTroops * 2;
        }
    }
    troopIncreaseRate(player) {
        const max = this.maxTroops(player);
        let toAdd = 10 + Math.pow(player.troops(), 0.73) / 4;
        const ratio = 1 - player.troops() / max;
        toAdd *= ratio;
        if (player.type() === Game_1.PlayerType.Bot) {
            toAdd *= 0.6;
        }
        if (player.type() === Game_1.PlayerType.FakeHuman) {
            switch (this._gameConfig.difficulty) {
                case Game_1.Difficulty.Easy:
                    toAdd *= 0.9;
                    break;
                case Game_1.Difficulty.Medium:
                    toAdd *= 1;
                    break;
                case Game_1.Difficulty.Hard:
                    toAdd *= 1.1;
                    break;
                case Game_1.Difficulty.Impossible:
                    toAdd *= 1.2;
                    break;
            }
        }
        return Math.min(player.troops() + toAdd, max) - player.troops();
    }
    goldAdditionRate(player) {
        if (player.type() === Game_1.PlayerType.Bot) {
            return 50n;
        }
        return 100n;
    }
    nukeMagnitudes(unitType) {
        switch (unitType) {
            case Game_1.UnitType.MIRVWarhead:
                return { inner: 12, outer: 18 };
            case Game_1.UnitType.AtomBomb:
                return { inner: 12, outer: 30 };
            case Game_1.UnitType.HydrogenBomb:
                return { inner: 80, outer: 100 };
        }
        throw new Error(`Unknown nuke type: ${unitType}`);
    }
    nukeAllianceBreakThreshold() {
        return 100;
    }
    defaultNukeSpeed() {
        return 6;
    }
    defaultNukeTargetableRange() {
        return 150;
    }
    defaultSamRange() {
        return 70;
    }
    defaultSamMissileSpeed() {
        return 12;
    }
    // Humans can be soldiers, soldiers attacking, soldiers in boat etc.
    nukeDeathFactor(nukeType, humans, tilesOwned, maxTroops) {
        if (nukeType !== Game_1.UnitType.MIRVWarhead) {
            return (5 * humans) / Math.max(1, tilesOwned);
        }
        const targetTroops = 0.03 * maxTroops;
        const excessTroops = Math.max(0, humans - targetTroops);
        const scalingFactor = 500;
        const steepness = 2;
        const normalizedExcess = excessTroops / maxTroops;
        return scalingFactor * (1 - Math.exp(-steepness * normalizedExcess));
    }
    structureMinDist() {
        return 15;
    }
    shellLifetime() {
        return 50;
    }
    warshipPatrolRange() {
        return 100;
    }
    warshipTargettingRange() {
        return 130;
    }
    warshipShellAttackRate() {
        return 20;
    }
    defensePostShellAttackRate() {
        return 100;
    }
    safeFromPiratesCooldownMax() {
        return 20;
    }
    defensePostTargettingRange() {
        return 75;
    }
    allianceExtensionPromptOffset() {
        return 300; // 30 seconds before expiration
    }
}
exports.DefaultConfig = DefaultConfig;
