"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.canBuildTransportShip = canBuildTransportShip;
exports.sourceDstOceanShore = sourceDstOceanShore;
exports.targetTransportTile = targetTransportTile;
exports.closestShoreFromPlayer = closestShoreFromPlayer;
exports.bestShoreDeploymentSource = bestShoreDeploymentSource;
exports.candidateShoreTiles = candidateShoreTiles;
const AStar_1 = require("../pathfinding/AStar");
const MiniAStar_1 = require("../pathfinding/MiniAStar");
const Game_1 = require("./Game");
const GameMap_1 = require("./GameMap");
function canBuildTransportShip(game, player, tile) {
    if (player.unitCount(Game_1.UnitType.TransportShip) >= game.config().boatMaxNumber()) {
        return false;
    }
    const dst = targetTransportTile(game, tile);
    if (dst === null) {
        return false;
    }
    const other = game.owner(tile);
    if (other === player) {
        return false;
    }
    if (other.isPlayer() && player.isFriendly(other)) {
        return false;
    }
    if (game.isOceanShore(dst)) {
        let myPlayerBordersOcean = false;
        for (const bt of player.borderTiles()) {
            if (game.isOceanShore(bt)) {
                myPlayerBordersOcean = true;
                break;
            }
        }
        let otherPlayerBordersOcean = false;
        if (!game.hasOwner(tile)) {
            otherPlayerBordersOcean = true;
        }
        else {
            for (const bt of other.borderTiles()) {
                if (game.isOceanShore(bt)) {
                    otherPlayerBordersOcean = true;
                    break;
                }
            }
        }
        if (myPlayerBordersOcean && otherPlayerBordersOcean) {
            return transportShipSpawn(game, player, dst);
        }
        else {
            return false;
        }
    }
    // Now we are boating in a lake, so do a bfs from target until we find
    // a border tile owned by the player
    const tiles = game.bfs(dst, (0, GameMap_1.andFN)((0, GameMap_1.manhattanDistFN)(dst, 300), (_, t) => game.isLake(t) || game.isShore(t)));
    const sorted = Array.from(tiles).sort((a, b) => game.manhattanDist(dst, a) - game.manhattanDist(dst, b));
    for (const t of sorted) {
        if (game.owner(t) === player) {
            return transportShipSpawn(game, player, t);
        }
    }
    return false;
}
function transportShipSpawn(game, player, targetTile) {
    if (!game.isShore(targetTile)) {
        return false;
    }
    const spawn = closestShoreFromPlayer(game, player, targetTile);
    if (spawn === null) {
        return false;
    }
    return spawn;
}
function sourceDstOceanShore(gm, src, tile) {
    const dst = gm.owner(tile);
    const srcTile = closestShoreFromPlayer(gm, src, tile);
    let dstTile = null;
    if (dst.isPlayer()) {
        dstTile = closestShoreFromPlayer(gm, dst, tile);
    }
    else {
        dstTile = closestShoreTN(gm, tile, 50);
    }
    return [srcTile, dstTile];
}
function targetTransportTile(gm, tile) {
    const dst = gm.playerBySmallID(gm.ownerID(tile));
    let dstTile = null;
    if (dst.isPlayer()) {
        dstTile = closestShoreFromPlayer(gm, dst, tile);
    }
    else {
        dstTile = closestShoreTN(gm, tile, 50);
    }
    return dstTile;
}
function closestShoreFromPlayer(gm, player, target) {
    const shoreTiles = Array.from(player.borderTiles()).filter((t) => gm.isShore(t));
    if (shoreTiles.length === 0) {
        return null;
    }
    return shoreTiles.reduce((closest, current) => {
        const closestDistance = gm.manhattanDist(target, closest);
        const currentDistance = gm.manhattanDist(target, current);
        return currentDistance < closestDistance ? current : closest;
    });
}
function bestShoreDeploymentSource(gm, player, target) {
    const t = targetTransportTile(gm, target);
    if (t === null)
        return false;
    const candidates = candidateShoreTiles(gm, player, t);
    const aStar = new MiniAStar_1.MiniAStar(gm, gm.miniMap(), candidates, t, 1000000, 1);
    const result = aStar.compute();
    if (result !== AStar_1.PathFindResultType.Completed) {
        console.warn(`bestShoreDeploymentSource: path not found: ${result}`);
        return false;
    }
    const path = aStar.reconstructPath();
    if (path.length === 0) {
        return false;
    }
    const potential = path[0];
    // Since mini a* downscales the map, we need to check the neighbors
    // of the potential tile to find a valid deployment point
    const neighbors = gm
        .neighbors(potential)
        .filter((n) => gm.isShore(n) && gm.owner(n) === player);
    if (neighbors.length === 0) {
        return false;
    }
    return neighbors[0];
}
function candidateShoreTiles(gm, player, target) {
    let closestManhattanDistance = Infinity;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    let bestByManhattan = null;
    const extremumTiles = {
        minX: null,
        minY: null,
        maxX: null,
        maxY: null,
    };
    const borderShoreTiles = Array.from(player.borderTiles()).filter((t) => gm.isShore(t));
    for (const tile of borderShoreTiles) {
        const distance = gm.manhattanDist(tile, target);
        const cell = gm.cell(tile);
        // Manhattan-closest tile
        if (distance < closestManhattanDistance) {
            closestManhattanDistance = distance;
            bestByManhattan = tile;
        }
        // Extremum tiles
        if (cell.x < minX) {
            minX = cell.x;
            extremumTiles.minX = tile;
        }
        else if (cell.y < minY) {
            minY = cell.y;
            extremumTiles.minY = tile;
        }
        else if (cell.x > maxX) {
            maxX = cell.x;
            extremumTiles.maxX = tile;
        }
        else if (cell.y > maxY) {
            maxY = cell.y;
            extremumTiles.maxY = tile;
        }
    }
    // Calculate sampling interval to ensure we get at most 50 tiles
    const samplingInterval = Math.max(10, Math.ceil(borderShoreTiles.length / 50));
    const sampledTiles = borderShoreTiles.filter((_, index) => index % samplingInterval === 0);
    const candidates = [
        bestByManhattan,
        extremumTiles.minX,
        extremumTiles.minY,
        extremumTiles.maxX,
        extremumTiles.maxY,
        ...sampledTiles,
    ].filter(Boolean);
    return candidates;
}
function closestShoreTN(gm, tile, searchDist) {
    const tn = Array.from(gm.bfs(tile, (0, GameMap_1.andFN)((_, t) => !gm.hasOwner(t), (0, GameMap_1.manhattanDistFN)(tile, searchDist))))
        .filter((t) => gm.isShore(t))
        .sort((a, b) => gm.manhattanDist(tile, a) - gm.manhattanDist(tile, b));
    if (tn.length === 0) {
        return null;
    }
    return tn[0];
}
