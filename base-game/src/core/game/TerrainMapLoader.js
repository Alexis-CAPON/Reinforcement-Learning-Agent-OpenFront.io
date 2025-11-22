import { GameMapImpl } from "./GameMap";
const loadedMaps = new Map();
export async function loadTerrainMap(map, terrainMapFileLoader) {
    const cached = loadedMaps.get(map);
    if (cached !== undefined)
        return cached;
    const mapFiles = terrainMapFileLoader.getMapData(map);
    const manifest = await mapFiles.manifest();
    const gameMap = await genTerrainFromBin(manifest.map, await mapFiles.mapBin());
    const miniGameMap = await genTerrainFromBin(manifest.mini_map, await mapFiles.miniMapBin());
    const result = {
        manifest: await mapFiles.manifest(),
        gameMap: gameMap,
        miniGameMap: miniGameMap,
    };
    loadedMaps.set(map, result);
    return result;
}
export async function genTerrainFromBin(mapData, data) {
    if (data.length !== mapData.width * mapData.height) {
        throw new Error(`Invalid data: buffer size ${data.length} incorrect for ${mapData.width}x${mapData.height} terrain plus 4 bytes for dimensions.`);
    }
    return new GameMapImpl(mapData.width, mapData.height, data, mapData.num_land_tiles);
}
