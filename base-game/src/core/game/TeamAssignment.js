"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.assignTeams = assignTeams;
const PseudoRandom_1 = require("../PseudoRandom");
const Util_1 = require("../Util");
const Game_1 = require("./Game");
function assignTeams(players, teams) {
    var _a, _b;
    const result = new Map();
    const teamPlayerCount = new Map();
    // Group players by clan
    const clanGroups = new Map();
    const noClanPlayers = [];
    // Sort players into clan groups or no-clan list
    for (const player of players) {
        if (player.clan) {
            if (!clanGroups.has(player.clan)) {
                clanGroups.set(player.clan, []);
            }
            clanGroups.get(player.clan).push(player);
        }
        else {
            noClanPlayers.push(player);
        }
    }
    const maxTeamSize = Math.ceil(players.length / teams.length);
    // Sort clans by size (largest first)
    const sortedClans = Array.from(clanGroups.entries()).sort((a, b) => b[1].length - a[1].length);
    // First, assign clan players
    for (const [_, clanPlayers] of sortedClans) {
        // Try to keep the clan together on the team with fewer players
        let team = null;
        let teamSize = 0;
        for (const t of teams) {
            const p = (_a = teamPlayerCount.get(t)) !== null && _a !== void 0 ? _a : 0;
            if (team !== null && teamSize <= p)
                continue;
            teamSize = p;
            team = t;
        }
        if (team === null)
            continue;
        for (const player of clanPlayers) {
            if (teamSize < maxTeamSize) {
                teamSize++;
                result.set(player, team);
            }
            else {
                result.set(player, "kicked");
            }
        }
        teamPlayerCount.set(team, teamSize);
    }
    // Then, assign non-clan players to balance teams
    let nationPlayers = noClanPlayers.filter((player) => player.playerType === Game_1.PlayerType.FakeHuman);
    if (nationPlayers.length > 0) {
        // Shuffle only nations to randomize their team assignment
        const random = new PseudoRandom_1.PseudoRandom((0, Util_1.simpleHash)(nationPlayers[0].id));
        nationPlayers = random.shuffleArray(nationPlayers);
    }
    const otherPlayers = noClanPlayers.filter((player) => player.playerType !== Game_1.PlayerType.FakeHuman);
    for (const player of otherPlayers.concat(nationPlayers)) {
        let team = null;
        let teamSize = 0;
        for (const t of teams) {
            const p = (_b = teamPlayerCount.get(t)) !== null && _b !== void 0 ? _b : 0;
            if (team !== null && teamSize <= p)
                continue;
            teamSize = p;
            team = t;
        }
        if (team === null)
            continue;
        teamPlayerCount.set(team, teamSize + 1);
        result.set(player, team);
    }
    return result;
}
