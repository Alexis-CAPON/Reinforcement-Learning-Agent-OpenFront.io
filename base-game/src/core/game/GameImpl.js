import { renderNumber } from "../../client/Utils";
import { simpleHash } from "../Util";
import { AllianceImpl } from "./AllianceImpl";
import { AllianceRequestImpl } from "./AllianceRequestImpl";
import { ColoredTeams, Duos, GameMode, MessageType, PlayerType, Quads, Trios, } from "./Game";
import { GameUpdateType } from "./GameUpdates";
import { PlayerImpl } from "./PlayerImpl";
import { createRailNetwork } from "./RailNetworkImpl";
import { StatsImpl } from "./StatsImpl";
import { assignTeams } from "./TeamAssignment";
import { TerraNulliusImpl } from "./TerraNulliusImpl";
import { UnitGrid } from "./UnitGrid";
export function createGame(humans, nations, gameMap, miniGameMap, config) {
    const stats = new StatsImpl();
    return new GameImpl(humans, nations, gameMap, miniGameMap, config, stats);
}
export class GameImpl {
    constructor(_humans, _nations, _map, miniGameMap, _config, _stats) {
        this._humans = _humans;
        this._nations = _nations;
        this._map = _map;
        this.miniGameMap = miniGameMap;
        this._config = _config;
        this._stats = _stats;
        this._ticks = 0;
        this.unInitExecs = [];
        this._players = new Map();
        this._playersBySmallID = [];
        this.execs = [];
        this.allianceRequests = [];
        this.alliances_ = [];
        this.nextPlayerID = 1;
        this._nextUnitID = 1;
        this.updates = createGameUpdatesMap();
        this.botTeam = ColoredTeams.Bot;
        this._railNetwork = createRailNetwork(this);
        // Used to assign unique IDs to each new alliance
        this.nextAllianceID = 0;
        this._terraNullius = new TerraNulliusImpl();
        this._width = _map.width();
        this._height = _map.height();
        this.unitGrid = new UnitGrid(this._map);
        if (_config.gameConfig().gameMode === GameMode.Team) {
            this.populateTeams();
        }
        this.addPlayers();
    }
    populateTeams() {
        let numPlayerTeams = this._config.playerTeams();
        if (typeof numPlayerTeams !== "number") {
            const players = this._humans.length + this._nations.length;
            switch (numPlayerTeams) {
                case Duos:
                    numPlayerTeams = Math.ceil(players / 2);
                    break;
                case Trios:
                    numPlayerTeams = Math.ceil(players / 3);
                    break;
                case Quads:
                    numPlayerTeams = Math.ceil(players / 4);
                    break;
                default:
                    throw new Error(`Unknown TeamCountConfig ${numPlayerTeams}`);
            }
        }
        if (numPlayerTeams < 2) {
            throw new Error(`Too few teams: ${numPlayerTeams}`);
        }
        else if (numPlayerTeams < 8) {
            this.playerTeams = [ColoredTeams.Red, ColoredTeams.Blue];
            if (numPlayerTeams >= 3)
                this.playerTeams.push(ColoredTeams.Yellow);
            if (numPlayerTeams >= 4)
                this.playerTeams.push(ColoredTeams.Green);
            if (numPlayerTeams >= 5)
                this.playerTeams.push(ColoredTeams.Purple);
            if (numPlayerTeams >= 6)
                this.playerTeams.push(ColoredTeams.Orange);
            if (numPlayerTeams >= 7)
                this.playerTeams.push(ColoredTeams.Teal);
        }
        else {
            this.playerTeams = [];
            for (let i = 1; i <= numPlayerTeams; i++) {
                this.playerTeams.push(`Team ${i}`);
            }
        }
    }
    addPlayers() {
        if (this.config().gameConfig().gameMode !== GameMode.Team) {
            this._humans.forEach((p) => this.addPlayer(p));
            this._nations.forEach((n) => this.addPlayer(n.playerInfo));
            return;
        }
        const allPlayers = [
            ...this._humans,
            ...this._nations.map((n) => n.playerInfo),
        ];
        const playerToTeam = assignTeams(allPlayers, this.playerTeams);
        for (const [playerInfo, team] of playerToTeam.entries()) {
            if (team === "kicked") {
                console.warn(`Player ${playerInfo.name} was kicked from team`);
                continue;
            }
            this.addPlayer(playerInfo, team);
        }
    }
    isOnEdgeOfMap(ref) {
        return this._map.isOnEdgeOfMap(ref);
    }
    owner(ref) {
        return this.playerBySmallID(this.ownerID(ref));
    }
    alliances() {
        return this.alliances_;
    }
    playerBySmallID(id) {
        if (id === 0) {
            return this.terraNullius();
        }
        return this._playersBySmallID[id - 1];
    }
    map() {
        return this._map;
    }
    miniMap() {
        return this.miniGameMap;
    }
    addUpdate(update) {
        this.updates[update.type].push(update);
    }
    nextUnitID() {
        const old = this._nextUnitID;
        this._nextUnitID++;
        return old;
    }
    setFallout(tile, value) {
        if (value && this.hasOwner(tile)) {
            throw Error(`cannot set fallout, tile ${tile} has owner`);
        }
        if (this._map.hasFallout(tile)) {
            return;
        }
        this._map.setFallout(tile, value);
        this.addUpdate({
            type: GameUpdateType.Tile,
            update: this.toTileUpdate(tile),
        });
    }
    units(...types) {
        return Array.from(this._players.values()).flatMap((p) => p.units(...types));
    }
    unitCount(type) {
        let total = 0;
        for (const player of this._players.values()) {
            total += player.unitCount(type);
        }
        return total;
    }
    unitInfo(type) {
        return this.config().unitInfo(type);
    }
    nations() {
        return this._nations;
    }
    createAllianceRequest(requestor, recipient) {
        if (requestor.isAlliedWith(recipient)) {
            console.log("cannot request alliance, already allied");
            return null;
        }
        if (recipient
            .incomingAllianceRequests()
            .find((ar) => ar.requestor() === requestor) !== undefined) {
            console.log(`duplicate alliance request from ${requestor.name()}`);
            return null;
        }
        const correspondingReq = requestor
            .incomingAllianceRequests()
            .find((ar) => ar.requestor() === recipient);
        if (correspondingReq !== undefined) {
            console.log(`got corresponding alliance requests, accepting`);
            correspondingReq.accept();
            return null;
        }
        const ar = new AllianceRequestImpl(requestor, recipient, this._ticks, this);
        this.allianceRequests.push(ar);
        this.addUpdate(ar.toUpdate());
        return ar;
    }
    acceptAllianceRequest(request) {
        this.allianceRequests = this.allianceRequests.filter((ar) => ar !== request);
        const requestor = request.requestor();
        const recipient = request.recipient();
        const existing = requestor.allianceWith(recipient);
        if (existing) {
            throw new Error(`cannot accept alliance request, already allied with ${recipient.name()}`);
        }
        // Create and register the new alliance
        const alliance = new AllianceImpl(this, requestor, recipient, this._ticks, this.nextAllianceID++);
        this.alliances_.push(alliance);
        request.requestor().pastOutgoingAllianceRequests.push(request);
        // Automatically remove embargoes only if they were automatically created
        if (requestor.hasEmbargoAgainst(recipient))
            requestor.endTemporaryEmbargo(recipient);
        if (recipient.hasEmbargoAgainst(requestor))
            recipient.endTemporaryEmbargo(requestor);
        this.addUpdate({
            type: GameUpdateType.AllianceRequestReply,
            request: request.toUpdate(),
            accepted: true,
        });
    }
    rejectAllianceRequest(request) {
        this.allianceRequests = this.allianceRequests.filter((ar) => ar !== request);
        request.requestor().pastOutgoingAllianceRequests.push(request);
        this.addUpdate({
            type: GameUpdateType.AllianceRequestReply,
            request: request.toUpdate(),
            accepted: false,
        });
    }
    hasPlayer(id) {
        return this._players.has(id);
    }
    config() {
        return this._config;
    }
    inSpawnPhase() {
        return this._ticks <= this.config().numSpawnPhaseTurns();
    }
    ticks() {
        return this._ticks;
    }
    executeNextTick() {
        this.updates = createGameUpdatesMap();
        this.execs.forEach((e) => {
            if ((!this.inSpawnPhase() || e.activeDuringSpawnPhase()) &&
                e.isActive()) {
                e.tick(this._ticks);
            }
        });
        const inited = [];
        const unInited = [];
        this.unInitExecs.forEach((e) => {
            if (!this.inSpawnPhase() || e.activeDuringSpawnPhase()) {
                e.init(this, this._ticks);
                inited.push(e);
            }
            else {
                unInited.push(e);
            }
        });
        this.removeInactiveExecutions();
        this.execs.push(...inited);
        this.unInitExecs = unInited;
        for (const player of this._players.values()) {
            // Players change each to so always add them
            this.addUpdate(player.toUpdate());
        }
        if (this.ticks() % 10 === 0) {
            this.addUpdate({
                type: GameUpdateType.Hash,
                tick: this.ticks(),
                hash: this.hash(),
            });
        }
        this._ticks++;
        return this.updates;
    }
    hash() {
        let hash = 1;
        this._players.forEach((p) => {
            hash += p.hash();
        });
        return hash;
    }
    terraNullius() {
        return this._terraNullius;
    }
    removeInactiveExecutions() {
        const activeExecs = [];
        for (const exec of this.execs) {
            if (this.inSpawnPhase()) {
                if (exec.activeDuringSpawnPhase()) {
                    if (exec.isActive()) {
                        activeExecs.push(exec);
                    }
                }
                else {
                    activeExecs.push(exec);
                }
            }
            else {
                if (exec.isActive()) {
                    activeExecs.push(exec);
                }
            }
        }
        this.execs = activeExecs;
    }
    players() {
        return Array.from(this._players.values()).filter((p) => p.isAlive());
    }
    allPlayers() {
        return Array.from(this._players.values());
    }
    executions() {
        return [...this.execs, ...this.unInitExecs];
    }
    addExecution(...exec) {
        this.unInitExecs.push(...exec);
    }
    removeExecution(exec) {
        this.execs = this.execs.filter((execution) => execution !== exec);
        this.unInitExecs = this.unInitExecs.filter((execution) => execution !== exec);
    }
    playerView(id) {
        return this.player(id);
    }
    addPlayer(playerInfo, team = null) {
        const player = new PlayerImpl(this, this.nextPlayerID, playerInfo, this.config().startManpower(playerInfo), team ?? this.maybeAssignTeam(playerInfo));
        this._playersBySmallID.push(player);
        this.nextPlayerID++;
        this._players.set(playerInfo.id, player);
        return player;
    }
    maybeAssignTeam(player) {
        if (this._config.gameConfig().gameMode !== GameMode.Team) {
            return null;
        }
        if (player.playerType === PlayerType.Bot) {
            return this.botTeam;
        }
        const rand = simpleHash(player.id);
        return this.playerTeams[rand % this.playerTeams.length];
    }
    player(id) {
        const player = this._players.get(id);
        if (player === undefined) {
            throw new Error(`Player with id ${id} not found`);
        }
        return player;
    }
    playerByClientID(id) {
        for (const [, player] of this._players) {
            if (player.clientID() === id) {
                return player;
            }
        }
        return null;
    }
    isOnMap(cell) {
        return (cell.x >= 0 &&
            cell.x < this._width &&
            cell.y >= 0 &&
            cell.y < this._height);
    }
    neighborsWithDiag(tile) {
        const x = this.x(tile);
        const y = this.y(tile);
        const ns = [];
        for (let dx = -1; dx <= 1; dx++) {
            for (let dy = -1; dy <= 1; dy++) {
                if (dx === 0 && dy === 0)
                    continue; // Skip the center tile
                const newX = x + dx;
                const newY = y + dy;
                if (newX >= 0 &&
                    newX < this._width &&
                    newY >= 0 &&
                    newY < this._height) {
                    ns.push(this._map.ref(newX, newY));
                }
            }
        }
        return ns;
    }
    conquer(owner, tile) {
        if (!this.isLand(tile)) {
            throw Error(`cannot conquer water`);
        }
        const previousOwner = this.owner(tile);
        if (previousOwner.isPlayer()) {
            previousOwner._lastTileChange = this._ticks;
            previousOwner._tiles.delete(tile);
            previousOwner._borderTiles.delete(tile);
        }
        this._map.setOwnerID(tile, owner.smallID());
        owner._tiles.add(tile);
        owner._lastTileChange = this._ticks;
        this.updateBorders(tile);
        this._map.setFallout(tile, false);
        this.addUpdate({
            type: GameUpdateType.Tile,
            update: this.toTileUpdate(tile),
        });
    }
    relinquish(tile) {
        if (!this.hasOwner(tile)) {
            throw new Error(`Cannot relinquish tile because it is unowned`);
        }
        if (this.isWater(tile)) {
            throw new Error("Cannot relinquish water");
        }
        const previousOwner = this.owner(tile);
        previousOwner._lastTileChange = this._ticks;
        previousOwner._tiles.delete(tile);
        previousOwner._borderTiles.delete(tile);
        this._map.setOwnerID(tile, 0);
        this.updateBorders(tile);
        this.addUpdate({
            type: GameUpdateType.Tile,
            update: this.toTileUpdate(tile),
        });
    }
    updateBorders(tile) {
        const tiles = [];
        tiles.push(tile);
        this.neighbors(tile).forEach((t) => tiles.push(t));
        for (const t of tiles) {
            if (!this.hasOwner(t)) {
                continue;
            }
            if (this.calcIsBorder(t)) {
                this.owner(t)._borderTiles.add(t);
            }
            else {
                this.owner(t)._borderTiles.delete(t);
            }
        }
    }
    calcIsBorder(tile) {
        if (!this.hasOwner(tile)) {
            return false;
        }
        for (const neighbor of this.neighbors(tile)) {
            const bordersEnemy = this.owner(tile) !== this.owner(neighbor);
            if (bordersEnemy) {
                return true;
            }
        }
        return false;
    }
    target(targeter, target) {
        this.addUpdate({
            type: GameUpdateType.TargetPlayer,
            playerID: targeter.smallID(),
            targetID: target.smallID(),
        });
    }
    breakAlliance(breaker, alliance) {
        let other;
        if (alliance.requestor() === breaker) {
            other = alliance.recipient();
        }
        else {
            other = alliance.requestor();
        }
        if (!breaker.isAlliedWith(other)) {
            throw new Error(`${breaker} not allied with ${other}, cannot break alliance`);
        }
        if (!other.isTraitor() && !other.isDisconnected()) {
            breaker.markTraitor();
        }
        const breakerSet = new Set(breaker.alliances());
        const alliances = other.alliances().filter((a) => breakerSet.has(a));
        if (alliances.length !== 1) {
            throw new Error(`must have exactly one alliance, have ${alliances.length}`);
        }
        this.alliances_ = this.alliances_.filter((a) => a !== alliances[0]);
        this.addUpdate({
            type: GameUpdateType.BrokeAlliance,
            traitorID: breaker.smallID(),
            betrayedID: other.smallID(),
        });
    }
    expireAlliance(alliance) {
        const p1Set = new Set(alliance.recipient().alliances());
        const alliances = alliance
            .requestor()
            .alliances()
            .filter((a) => p1Set.has(a));
        if (alliances.length !== 1) {
            throw new Error(`cannot expire alliance: must have exactly one alliance, have ${alliances.length}`);
        }
        this.alliances_ = this.alliances_.filter((a) => a !== alliances[0]);
        this.addUpdate({
            type: GameUpdateType.AllianceExpired,
            player1ID: alliance.requestor().smallID(),
            player2ID: alliance.recipient().smallID(),
        });
    }
    sendEmojiUpdate(msg) {
        this.addUpdate({
            type: GameUpdateType.Emoji,
            emoji: msg,
        });
    }
    setWinner(winner, allPlayersStats) {
        this.addUpdate({
            type: GameUpdateType.Win,
            winner: this.makeWinner(winner),
            allPlayersStats,
        });
    }
    makeWinner(winner) {
        if (typeof winner === "string") {
            return [
                "team",
                winner,
                ...this.players()
                    .filter((p) => p.team() === winner && p.clientID() !== null)
                    .map((p) => p.clientID()),
            ];
        }
        else {
            const clientId = winner.clientID();
            if (clientId === null)
                return;
            return [
                "player",
                clientId,
                // TODO: Assists (vote for peace)
            ];
        }
    }
    teams() {
        if (this._config.gameConfig().gameMode !== GameMode.Team) {
            return [];
        }
        return [this.botTeam, ...this.playerTeams];
    }
    displayMessage(message, type, playerID, goldAmount, params) {
        let id = null;
        if (playerID !== null) {
            id = this.player(playerID).smallID();
        }
        this.addUpdate({
            type: GameUpdateType.DisplayEvent,
            messageType: type,
            message: message,
            playerID: id,
            goldAmount: goldAmount,
            params: params,
        });
    }
    displayChat(message, category, target, playerID, isFrom, recipient) {
        let id = null;
        if (playerID !== null) {
            id = this.player(playerID).smallID();
        }
        this.addUpdate({
            type: GameUpdateType.DisplayChatEvent,
            key: message,
            category: category,
            target: target,
            playerID: id,
            isFrom,
            recipient: recipient,
        });
    }
    displayIncomingUnit(unitID, message, type, playerID) {
        const id = this.player(playerID).smallID();
        this.addUpdate({
            type: GameUpdateType.UnitIncoming,
            unitID: unitID,
            message: message,
            messageType: type,
            playerID: id,
        });
    }
    addUnit(u) {
        this.unitGrid.addUnit(u);
    }
    removeUnit(u) {
        this.unitGrid.removeUnit(u);
        if (u.hasTrainStation()) {
            this._railNetwork.removeStation(u);
        }
    }
    updateUnitTile(u) {
        this.unitGrid.updateUnitCell(u);
    }
    hasUnitNearby(tile, searchRange, type, playerId) {
        return this.unitGrid.hasUnitNearby(tile, searchRange, type, playerId);
    }
    nearbyUnits(tile, searchRange, types, predicate) {
        return this.unitGrid.nearbyUnits(tile, searchRange, types, predicate);
    }
    ref(x, y) {
        return this._map.ref(x, y);
    }
    isValidRef(ref) {
        return this._map.isValidRef(ref);
    }
    x(ref) {
        return this._map.x(ref);
    }
    y(ref) {
        return this._map.y(ref);
    }
    cell(ref) {
        return this._map.cell(ref);
    }
    width() {
        return this._map.width();
    }
    height() {
        return this._map.height();
    }
    numLandTiles() {
        return this._map.numLandTiles();
    }
    isValidCoord(x, y) {
        return this._map.isValidCoord(x, y);
    }
    isLand(ref) {
        return this._map.isLand(ref);
    }
    isOceanShore(ref) {
        return this._map.isOceanShore(ref);
    }
    isOcean(ref) {
        return this._map.isOcean(ref);
    }
    isShoreline(ref) {
        return this._map.isShoreline(ref);
    }
    magnitude(ref) {
        return this._map.magnitude(ref);
    }
    ownerID(ref) {
        return this._map.ownerID(ref);
    }
    hasOwner(ref) {
        return this._map.hasOwner(ref);
    }
    setOwnerID(ref, playerId) {
        return this._map.setOwnerID(ref, playerId);
    }
    hasFallout(ref) {
        return this._map.hasFallout(ref);
    }
    isBorder(ref) {
        return this._map.isBorder(ref);
    }
    neighbors(ref) {
        return this._map.neighbors(ref);
    }
    isWater(ref) {
        return this._map.isWater(ref);
    }
    isLake(ref) {
        return this._map.isLake(ref);
    }
    isShore(ref) {
        return this._map.isShore(ref);
    }
    cost(ref) {
        return this._map.cost(ref);
    }
    terrainType(ref) {
        return this._map.terrainType(ref);
    }
    forEachTile(fn) {
        return this._map.forEachTile(fn);
    }
    manhattanDist(c1, c2) {
        return this._map.manhattanDist(c1, c2);
    }
    euclideanDistSquared(c1, c2) {
        return this._map.euclideanDistSquared(c1, c2);
    }
    bfs(tile, filter) {
        return this._map.bfs(tile, filter);
    }
    toTileUpdate(tile) {
        return this._map.toTileUpdate(tile);
    }
    updateTile(tu) {
        return this._map.updateTile(tu);
    }
    numTilesWithFallout() {
        return this._map.numTilesWithFallout();
    }
    stats() {
        return this._stats;
    }
    railNetwork() {
        return this._railNetwork;
    }
    conquerPlayer(conqueror, conquered) {
        const gold = conquered.gold();
        this.displayMessage(`Conquered ${conquered.displayName()} received ${renderNumber(gold)} gold`, MessageType.CONQUERED_PLAYER, conqueror.id(), gold);
        conqueror.addGold(gold);
        conquered.removeGold(gold);
        this.addUpdate({
            type: GameUpdateType.ConquestEvent,
            conquerorId: conqueror.id(),
            conqueredId: conquered.id(),
            gold,
        });
        // Record stats
        this.stats().goldWar(conqueror, conquered, gold);
    }
}
// Or a more dynamic approach that will catch new enum values:
const createGameUpdatesMap = () => {
    const map = {};
    Object.values(GameUpdateType)
        .filter((key) => !isNaN(Number(key))) // Filter out reverse mappings
        .forEach((key) => {
        map[key] = [];
    });
    return map;
};
