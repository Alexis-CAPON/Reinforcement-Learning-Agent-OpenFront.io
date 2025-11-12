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
exports.loadTerrainMap = loadTerrainMap;
exports.genTerrainFromBin = genTerrainFromBin;
const GameMap_1 = require("./GameMap");
const loadedMaps = new Map();
function loadTerrainMap(map, terrainMapFileLoader) {
    return __awaiter(this, void 0, void 0, function* () {
        const cached = loadedMaps.get(map);
        if (cached !== undefined)
            return cached;
        const mapFiles = terrainMapFileLoader.getMapData(map);
        const manifest = yield mapFiles.manifest();
        const gameMap = yield genTerrainFromBin(manifest.map, yield mapFiles.mapBin());
        const miniGameMap = yield genTerrainFromBin(manifest.mini_map, yield mapFiles.miniMapBin());
        const result = {
            manifest: yield mapFiles.manifest(),
            gameMap: gameMap,
            miniGameMap: miniGameMap,
        };
        loadedMaps.set(map, result);
        return result;
    });
}
function genTerrainFromBin(mapData, data) {
    return __awaiter(this, void 0, void 0, function* () {
        if (data.length !== mapData.width * mapData.height) {
            throw new Error(`Invalid data: buffer size ${data.length} incorrect for ${mapData.width}x${mapData.height} terrain plus 4 bytes for dimensions.`);
        }
        return new GameMap_1.GameMapImpl(mapData.width, mapData.height, data, mapData.num_land_tiles);
    });
}
