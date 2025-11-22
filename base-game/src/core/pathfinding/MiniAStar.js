import { Cell } from "../game/Game";
import { SerialAStar } from "./SerialAStar";
export class GameMapAdapter {
    constructor(gameMap, waterPath) {
        this.gameMap = gameMap;
        this.waterPath = waterPath;
        this.waterPenalty = 3;
    }
    neighbors(node) {
        return this.gameMap.neighbors(node);
    }
    cost(node) {
        let base = this.gameMap.cost(node);
        // Avoid crossing water when possible
        if (!this.waterPath && this.gameMap.isWater(node)) {
            base += this.waterPenalty;
        }
        return base;
    }
    position(node) {
        return { x: this.gameMap.x(node), y: this.gameMap.y(node) };
    }
    isTraversable(from, to) {
        const toWater = this.gameMap.isWater(to);
        if (this.waterPath) {
            return toWater;
        }
        // Allow water access from/to shore
        const fromShore = this.gameMap.isShoreline(from);
        const toShore = this.gameMap.isShoreline(to);
        return !toWater || fromShore || toShore;
    }
}
export class MiniAStar {
    constructor(gameMap, miniMap, src, dst, iterations, maxTries, waterPath = true, directionChangePenalty = 0) {
        this.gameMap = gameMap;
        this.miniMap = miniMap;
        this.src = src;
        this.dst = dst;
        const srcArray = Array.isArray(src) ? src : [src];
        const miniSrc = srcArray.map((srcPoint) => this.miniMap.ref(Math.floor(gameMap.x(srcPoint) / 2), Math.floor(gameMap.y(srcPoint) / 2)));
        const miniDst = this.miniMap.ref(Math.floor(gameMap.x(dst) / 2), Math.floor(gameMap.y(dst) / 2));
        this.aStar = new SerialAStar(miniSrc, miniDst, iterations, maxTries, new GameMapAdapter(miniMap, waterPath), directionChangePenalty);
    }
    compute() {
        return this.aStar.compute();
    }
    reconstructPath() {
        let cellSrc;
        if (!Array.isArray(this.src)) {
            cellSrc = new Cell(this.gameMap.x(this.src), this.gameMap.y(this.src));
        }
        const cellDst = new Cell(this.gameMap.x(this.dst), this.gameMap.y(this.dst));
        const upscaled = fixExtremes(upscalePath(this.aStar
            .reconstructPath()
            .map((tr) => new Cell(this.miniMap.x(tr), this.miniMap.y(tr)))), cellDst, cellSrc);
        return upscaled.map((c) => this.gameMap.ref(c.x, c.y));
    }
}
function fixExtremes(upscaled, cellDst, cellSrc) {
    if (cellSrc !== undefined) {
        const srcIndex = findCell(upscaled, cellSrc);
        if (srcIndex === -1) {
            // didnt find the start tile in the path
            upscaled.unshift(cellSrc);
        }
        else if (srcIndex !== 0) {
            // found start tile but not at the start
            // remove all tiles before the start tile
            upscaled = upscaled.slice(srcIndex);
        }
    }
    const dstIndex = findCell(upscaled, cellDst);
    if (dstIndex === -1) {
        // didnt find the dst tile in the path
        upscaled.push(cellDst);
    }
    else if (dstIndex !== upscaled.length - 1) {
        // found dst tile but not at the end
        // remove all tiles after the dst tile
        upscaled = upscaled.slice(0, dstIndex + 1);
    }
    return upscaled;
}
function upscalePath(path, scaleFactor = 2) {
    // Scale up each point
    const scaledPath = path.map((point) => new Cell(point.x * scaleFactor, point.y * scaleFactor));
    const smoothPath = [];
    for (let i = 0; i < scaledPath.length - 1; i++) {
        const current = scaledPath[i];
        const next = scaledPath[i + 1];
        // Add the current point
        smoothPath.push(current);
        // Always interpolate between scaled points
        const dx = next.x - current.x;
        const dy = next.y - current.y;
        // Calculate number of steps needed
        const distance = Math.max(Math.abs(dx), Math.abs(dy));
        const steps = distance;
        // Add intermediate points
        for (let step = 1; step < steps; step++) {
            smoothPath.push(new Cell(Math.round(current.x + (dx * step) / steps), Math.round(current.y + (dy * step) / steps)));
        }
    }
    // Add the last point
    if (scaledPath.length > 0) {
        smoothPath.push(scaledPath[scaledPath.length - 1]);
    }
    return smoothPath;
}
function findCell(upscaled, cellDst) {
    for (let i = 0; i < upscaled.length; i++) {
        if (upscaled[i].x === cellDst.x && upscaled[i].y === cellDst.y) {
            return i;
        }
    }
    return -1;
}
