/**
 * Lightweight min-heap specialised for (priority:number, tile:TileRef) pairs.
 * - priorities stored in a contiguous Float32Array
 * - tiles stored in a parallel object array
 */
export class FlatBinaryHeap {
    constructor(capacity = 1024) {
        this.len = 0; // current number of elements
        this.pri = new Float32Array(capacity);
        this.tiles = new Array(capacity);
    }
    /** remove every element without reallocating */
    clear() {
        this.len = 0;
    }
    /** current heap size */
    size() {
        return this.len;
    }
    //insert tiles
    enqueue(tile, priority) {
        if (this.len === this.pri.length)
            this.grow(); // ensure space
        let i = this.len++;
        /* sift-up */
        while (i > 0) {
            const parent = (i - 1) >> 1;
            if (priority >= this.pri[parent])
                break;
            this.pri[i] = this.pri[parent];
            this.tiles[i] = this.tiles[parent];
            i = parent;
        }
        this.pri[i] = priority;
        this.tiles[i] = tile;
    }
    //remove tiles
    dequeue() {
        if (this.len === 0)
            throw new Error("heap empty");
        const topTile = this.tiles[0];
        const topPri = this.pri[0];
        const lastPri = this.pri[--this.len];
        const lastTile = this.tiles[this.len];
        /* sift-down */
        let i = 0;
        while (true) {
            const left = (i << 1) + 1;
            if (left >= this.len)
                break;
            const right = left + 1;
            const child = right < this.len && this.pri[right] < this.pri[left] ? right : left;
            if (lastPri <= this.pri[child])
                break;
            this.pri[i] = this.pri[child];
            this.tiles[i] = this.tiles[child];
            i = child;
        }
        this.pri[i] = lastPri;
        this.tiles[i] = lastTile;
        return [topTile, topPri];
    }
    /** double the underlying storage */
    grow() {
        const newCap = this.pri.length << 1;
        const newPri = new Float32Array(newCap);
        newPri.set(this.pri);
        this.pri = newPri;
        this.tiles.length = newCap;
    }
}
