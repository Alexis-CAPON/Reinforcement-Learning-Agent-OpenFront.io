/**
 * RLWorkerClient - Drop-in replacement for WorkerClient that connects to Python RL bridge
 *
 * This allows us to use the real GameView/GameRenderer/UI with RL model actions from Python
 */

import { GameUpdateViewData, ErrorUpdate } from '../core/game/GameUpdates';
import { ClientID, GameStartInfo, Turn } from '../core/Schemas';
import { PlayerActions, PlayerBorderTiles, PlayerID, PlayerProfile, Cell } from '../core/game/Game';
import { TileRef } from '../core/game/GameMap';

export class RLWorkerClient {
  private ws: WebSocket | null = null;
  private isInitialized = false;
  private gameUpdateCallback?: (update: GameUpdateViewData | ErrorUpdate) => void;
  private pendingRequests: Map<string, (response: any) => void> = new Map();
  private requestCounter = 0;
  private cropRegion: { x: number; y: number; width: number; height: number } | null = null;

  constructor(
    private gameStartInfo: GameStartInfo,
    private clientID: ClientID,
    private wsUrl: string = 'ws://localhost:8765',
  ) {}

  /**
   * Connect to Python RL bridge via WebSocket
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log('[RLWorkerClient] Connecting to RL bridge at', this.wsUrl);
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('[RLWorkerClient] Connected to RL bridge');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('[RLWorkerClient] WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[RLWorkerClient] Failed to parse message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('[RLWorkerClient] Connection closed');
      };
    });
  }

  private handleMessage(message: any) {
    // Handle init response (crop region info)
    if (message.type === 'init_response') {
      console.log('[RLWorkerClient] Received init_response:', message);
      if (message.crop_region) {
        this.cropRegion = message.crop_region;
        const centerX = message.crop_region.x + message.crop_region.width / 2;
        const centerY = message.crop_region.y + message.crop_region.height / 2;
        const spawnRadius = Math.min(message.crop_region.width, message.crop_region.height) / 2 - 20;
        console.log('[RLWorkerClient] Received crop region:', this.cropRegion);
        console.log(`[RLWorkerClient] Crop center: (${centerX}, ${centerY}), spawn radius: ${spawnRadius}`);

        // Dispatch event to notify RLMain about crop region
        window.dispatchEvent(new CustomEvent('rl-crop-region', {
          detail: this.cropRegion
        }));
      } else {
        console.warn('[RLWorkerClient] No crop_region in init_response');
      }
      return;
    }

    // Handle game updates (main data flow)
    if (message.type === 'game_update' && message.gameUpdate) {
      const gu = message.gameUpdate;
      console.log(`[RLWorkerClient] Received update: tick=${gu.tick}, tiles=${gu.packedTileUpdates?.length || 0}, updateTypes=${Object.keys(gu.updates || {}).length}`);

      // Debug: Check player updates
      if (gu.updates && gu.updates['1']) {
        const playerUpdates = gu.updates['1'];
        console.log(`[RLWorkerClient] ${playerUpdates.length} players:`, playerUpdates.map((p: any) => `${p.name}(tiles=${p.tilesOwned})`).join(', '));
      }

      if (this.gameUpdateCallback) {
        // Convert numbers back to BigInts for GameView
        const gameUpdate = this.convertToBigInt(message.gameUpdate);
        this.gameUpdateCallback(gameUpdate);
      }
      return;
    }

    // Handle model state updates (for RL overlay)
    if (message.type === 'model_state') {
      // Dispatch as window event for RLOverlay component
      window.dispatchEvent(new CustomEvent('rl-model-state', {
        detail: message
      }));
      return;
    }

    // Handle responses to requests (playerProfile, etc.)
    if (message.id && this.pendingRequests.has(message.id)) {
      const resolver = this.pendingRequests.get(message.id)!;
      resolver(message);
      this.pendingRequests.delete(message.id);
      return;
    }

    console.log('[RLWorkerClient] Received unknown message:', message);
  }

  /**
   * Send request to Python bridge and wait for response
   */
  private sendRequest(type: string, data: any = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const id = `req_${this.requestCounter++}`;
      this.pendingRequests.set(id, resolve);

      this.ws.send(JSON.stringify({
        type,
        id,
        ...data,
      }));

      // Timeout after 5 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`Request ${type} timed out`));
        }
      }, 5000);
    });
  }

  /**
   * Initialize the worker (called by ClientGameRunner)
   */
  async initialize(): Promise<void> {
    // Send initialization info to Python
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'init',
        gameStartInfo: this.gameStartInfo,
        clientID: this.clientID,
      }));
    }
    this.isInitialized = true;
  }

  /**
   * Start receiving game updates
   */
  start(gameUpdate: (gu: GameUpdateViewData | ErrorUpdate) => void) {
    if (!this.isInitialized) {
      throw new Error('Worker not initialized');
    }
    this.gameUpdateCallback = gameUpdate;
  }

  /**
   * Send turn to game (NO-OP for RL mode - model generates turns)
   */
  sendTurn(turn: Turn) {
    // In RL mode, turns are generated by the Python model, not the UI
    // User cannot send turns manually
    console.log('[RLWorkerClient] sendTurn called but ignored in RL mode');
  }

  /**
   * Send spawn location to Python bridge
   */
  sendSpawn(tile: number) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[RLWorkerClient] Cannot send spawn: not connected');
      return;
    }
    console.log('[RLWorkerClient] Sending spawn location:', tile);
    this.ws.send(JSON.stringify({
      type: 'spawn',
      tile: tile
    }));
  }

  /**
   * Tell Python that client is ready to receive game state
   */
  sendReady() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[RLWorkerClient] Cannot send ready: not connected');
      return;
    }
    console.log('[RLWorkerClient] Sending ready signal');
    this.ws.send(JSON.stringify({
      type: 'ready'
    }));
  }

  /**
   * Request next game tick
   */
  sendHeartbeat() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[RLWorkerClient] Cannot send heartbeat: not connected');
      return;
    }
    this.ws.send(JSON.stringify({ type: 'heartbeat' }));
  }

  /**
   * Get player profile (returns empty profile for RL mode)
   */
  async playerProfile(playerID: number): Promise<PlayerProfile> {
    // For RL visualization, we don't need full player profiles
    // Return minimal data to keep UI happy
    return {
      relations: {},
      alliances: [],
    };
  }

  /**
   * Get player border tiles (query Python if needed, or return empty)
   */
  async playerBorderTiles(playerID: PlayerID): Promise<PlayerBorderTiles> {
    try {
      const response = await this.sendRequest('player_border_tiles', { playerID });
      return response.result || { borderTiles: new Set() };
    } catch (error) {
      console.warn('[RLWorkerClient] playerBorderTiles failed:', error);
      return { borderTiles: new Set() };
    }
  }

  /**
   * Get available player actions for a tile (return empty for RL mode)
   */
  async playerInteraction(
    playerID: PlayerID,
    x: number,
    y: number,
  ): Promise<PlayerActions> {
    // In RL mode, user cannot interact with tiles
    // Return empty actions to keep UI from crashing
    return {
      canAttack: false,
      buildableUnits: [],
      canSendEmojiAllPlayers: false,
    };
  }

  /**
   * Get average position of attack
   */
  async attackAveragePosition(
    playerID: number,
    attackID: string,
  ): Promise<Cell | null> {
    try {
      const response = await this.sendRequest('attack_average_position', { playerID, attackID });
      if (response.x !== null && response.y !== null) {
        return new Cell(response.x, response.y);
      }
      return null;
    } catch (error) {
      console.warn('[RLWorkerClient] attackAveragePosition failed:', error);
      return null;
    }
  }

  /**
   * Get best transport ship spawn location
   */
  async transportShipSpawn(
    playerID: PlayerID,
    targetTile: TileRef,
  ): Promise<TileRef | false> {
    try {
      const response = await this.sendRequest('transport_ship_spawn', { playerID, targetTile });
      return response.result || false;
    } catch (error) {
      console.warn('[RLWorkerClient] transportShipSpawn failed:', error);
      return false;
    }
  }

  /**
   * Convert numbers back to BigInts in GameUpdateViewData
   * The Python bridge converts BigInts to numbers for JSON serialization
   * We need to convert them back for the TypeScript game engine
   */
  private convertToBigInt(gameUpdate: any): any {
    if (!gameUpdate) return gameUpdate;

    // Convert packedTileUpdates from numbers to BigInts
    if (gameUpdate.packedTileUpdates && Array.isArray(gameUpdate.packedTileUpdates)) {
      gameUpdate.packedTileUpdates = gameUpdate.packedTileUpdates.map((update: any) => {
        if (typeof update === 'number') {
          return BigInt(update);
        }
        return update;
      });
    }

    // Recursively convert numbers to BigInts in updates object
    if (gameUpdate.updates && typeof gameUpdate.updates === 'object') {
      gameUpdate.updates = this.recursivelyConvertBigInt(gameUpdate.updates);
    }

    // Convert playerNameViewData
    if (gameUpdate.playerNameViewData && typeof gameUpdate.playerNameViewData === 'object') {
      gameUpdate.playerNameViewData = this.recursivelyConvertBigInt(gameUpdate.playerNameViewData);
    }

    return gameUpdate;
  }

  /**
   * Recursively convert large numbers to BigInts
   * Fields that should be BigInt: id, tile indices, packed data
   */
  private recursivelyConvertBigInt(obj: any): any {
    if (obj === null || obj === undefined) return obj;

    if (Array.isArray(obj)) {
      return obj.map(item => this.recursivelyConvertBigInt(item));
    }

    if (typeof obj === 'object') {
      const result: any = {};
      for (const key in obj) {
        const value = obj[key];
        // Convert specific fields that should be BigInt
        // (id, pos, tile, etc. - but only if they're numbers that could be BigInt)
        if (typeof value === 'number' && (key === 'id' || key === 'pos' || key === 'tile')) {
          // Only convert if it's an integer (IDs and positions are integers)
          result[key] = Number.isInteger(value) ? value : value; // Keep as number for now
        } else if (typeof value === 'object') {
          result[key] = this.recursivelyConvertBigInt(value);
        } else {
          result[key] = value;
        }
      }
      return result;
    }

    return obj;
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.gameUpdateCallback = undefined;
    this.pendingRequests.clear();
  }
}
