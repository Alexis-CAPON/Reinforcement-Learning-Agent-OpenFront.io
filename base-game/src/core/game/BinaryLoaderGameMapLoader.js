import { GameMapType } from "./Game";
export class BinaryLoaderGameMapLoader {
    constructor() {
        this.maps = new Map();
    }
    createLazyLoader(importFn) {
        let cache = null;
        return () => {
            cache ?? (cache = importFn());
            return cache;
        };
    }
    getMapData(map) {
        const cachedMap = this.maps.get(map);
        if (cachedMap) {
            return cachedMap;
        }
        const key = Object.keys(GameMapType).find((k) => GameMapType[k] === map);
        const fileName = key?.toLowerCase();
        const mapData = {
            mapBin: this.createLazyLoader(() => import(`!!binary-loader!../../../resources/maps/${fileName}/map.bin`).then((m) => this.toUInt8Array(m.default))),
            miniMapBin: this.createLazyLoader(() => import(`!!binary-loader!../../../resources/maps/${fileName}/mini_map.bin`).then((m) => this.toUInt8Array(m.default))),
            manifest: this.createLazyLoader(() => import(`../../../resources/maps/${fileName}/manifest.json`).then((m) => m.default)),
            webpPath: this.createLazyLoader(() => import(`../../../resources/maps/${fileName}/thumbnail.webp`).then((m) => m.default)),
        };
        this.maps.set(map, mapData);
        return mapData;
    }
    /**
     * Converts a given string into a UInt8Array where each character in the string
     * is represented as an 8-bit unsigned integer.
     */
    toUInt8Array(data) {
        const rawData = new Uint8Array(data.length);
        for (let i = 0; i < data.length; i++) {
            rawData[i] = data.charCodeAt(i);
        }
        return rawData;
    }
}
