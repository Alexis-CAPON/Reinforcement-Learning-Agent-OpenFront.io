/**
 * RLMain - Entry point for RL visualization mode
 *
 * This file initializes the game in RL mode, using:
 * - RLWorkerClient instead of WorkerClient
 * - The existing GameView, GameRenderer, and full UI
 * - Python RL bridge for game updates and model actions
 */

import { EventBus } from '../core/EventBus';
import { ClientID, GameID, GameStartInfo } from '../core/Schemas';
import { getConfig } from '../core/configuration/ConfigLoader';
import { GameView } from '../core/game/GameView';
import { loadTerrainMap } from '../core/game/TerrainMapLoader';
import { UserSettings } from '../core/game/UserSettings';
import { GameType, Difficulty, GameMapType } from '../core/game/Game';
import { RLWorkerClient } from './RLWorkerClient';
import { terrainMapFileLoader } from './TerrainMapFileLoader';
import { createCanvas } from './Utils';
import { createRenderer, GameRenderer } from './graphics/GameRenderer';
import { InputHandler } from './InputHandler';
import { ClientGameRunner } from './ClientGameRunner';
import { ServerConfig } from '../core/configuration/Config';

// Import RLOverlay component
import './RLOverlay';

interface RLConfig {
  wsUrl: string;
  mapName: string;
  difficulty: string;
  clientID: ClientID;
  playerName: string;
}

class RLClient {
  private gameStop: (() => void) | null = null;

  async initialize() {
    console.log('[RLClient] Initializing RL visualization mode');

    // Get configuration from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const config: RLConfig = {
      wsUrl: urlParams.get('ws') || 'ws://localhost:8765',
      mapName: urlParams.get('map') || 'australia',  // Changed to match Python default
      difficulty: urlParams.get('difficulty') || 'Easy',
      clientID: 'rl-client' as ClientID,
      playerName: 'RL Agent',
    };

    console.log('[RLClient] Config:', config);

    // Show loading screen
    this.showLoading('Initializing RL client...');

    try {
      // Start the RL game
      await this.startRLGame(config);
    } catch (error) {
      console.error('[RLClient] Failed to initialize:', error);
      this.showError(`Failed to initialize: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async startRLGame(config: RLConfig) {
    this.showLoading('Connecting to Python bridge...');

    const eventBus = new EventBus();
    const userSettings = new UserSettings();

    // Create minimal server config (cast to any - not needed in RL mode)
    const serverConfig = {
      turnIntervalMs: () => 100,
      gameCreationRate: () => 1,
      lobbyMaxPlayers: () => 50,
      numWorkers: () => 1,
      workerIndex: () => 0,
      workerPath: () => '',
      allowedFlares: () => undefined,
    } as any as ServerConfig;

    // Create GameStartInfo (mimicking a singleplayer game)
    const gameID = 'rl-game' as GameID;

    // Map URL param to actual game map name
    // URL uses lowercase (australia), game uses titlecase (Australia)
    // For custom maps (like australia_100x100), pass through as-is
    const mapNameMapping: Record<string, GameMapType> = {
      'australia': 'Australia' as GameMapType,
      'world': 'World' as GameMapType,
      'europe': 'Europe' as GameMapType,
      'halkidiki': 'Halkidiki' as GameMapType,
    };
    const mapLower = config.mapName.toLowerCase();
    const actualMapName = mapNameMapping[mapLower] || config.mapName as GameMapType;
    console.log(`[RLClient] Using map: ${actualMapName} (from URL param: ${config.mapName})`);

    const gameStartInfo: GameStartInfo = {
      gameID,
      config: {
        gameType: GameType.Singleplayer,
        difficulty: Difficulty.Easy,
        gameMap: actualMapName,
        gameMode: 'Free For All' as any,
        bots: 1,
        donateGold: false,
        donateTroops: false,
        disableNPCs: false,
        infiniteGold: false,
        infiniteTroops: false,
        instantBuild: false,
      },
      players: [
        {
          username: config.playerName,
          clientID: config.clientID,
          flag: '',
          pattern: undefined,
        },
      ],
    };

    // Create RLWorkerClient
    this.showLoading('Creating RL worker...');
    const worker = new RLWorkerClient(gameStartInfo, config.clientID, config.wsUrl);

    // Connect to Python bridge
    this.showLoading('Connecting to WebSocket...');
    await worker.connect();

    // Set up crop region listener BEFORE initialize (so we catch the init_response)
    let cropRegionReceived: ((cropRegion: any) => void) | null = null;
    const cropRegionPromise = new Promise<any>((resolve) => {
      cropRegionReceived = resolve;
    });

    window.addEventListener('rl-crop-region', ((event: CustomEvent) => {
      const cropRegion = event.detail;
      console.log('[RLClient] Received crop region event:', cropRegion);
      if (cropRegionReceived) {
        cropRegionReceived(cropRegion);
      }
    }) as EventListener);

    // Initialize worker (this will trigger init_response with crop_region)
    this.showLoading('Initializing worker...');
    await worker.initialize();

    // Load game map
    this.showLoading('Loading game map...');
    const gameMap = await loadTerrainMap(gameStartInfo.config.gameMap, terrainMapFileLoader);

    // Get game config (use default for RL mode - no server fetch needed)
    this.showLoading('Loading game config...');
    const gameConfig = await getConfig(gameStartInfo.config, userSettings, false, true); // true = skipServerFetch for RL mode

    // Create GameView
    this.showLoading('Creating game view...');
    const gameView = new GameView(
      worker as any, // RLWorkerClient duck-types as WorkerClient
      gameConfig,
      gameMap,
      config.clientID,
      gameID,
      gameStartInfo.players,
    );

    // Create canvas and renderer
    this.showLoading('Creating renderer...');
    const canvas = createCanvas();
    const gameRenderer = createRenderer(canvas, gameView, eventBus);

    // Create input handler (won't be used for turns, but needed for camera/UI)
    const inputHandler = new InputHandler(canvas, eventBus);

    // Create fake transport (RL doesn't use transport)
    const fakeTransport = {
      joinGame: () => {},
      leaveGame: () => {},
      sendTurn: () => {},
      sendHash: () => {},
      connect: () => {},
      disconnect: () => {},
      reconnect: () => {}, // Required by connection check
      turnComplete: () => {}, // Required by ClientGameRunner
    };

    // Create lobby config
    const lobbyConfig = {
      serverConfig,
      patternName: undefined,
      flag: '',
      playerName: config.playerName,
      clientID: config.clientID,
      gameID,
      token: '',
      gameStartInfo,
    };

    // Create ClientGameRunner
    this.showLoading('Creating game runner...');
    const runner = new ClientGameRunner(
      lobbyConfig,
      eventBus,
      gameRenderer,
      inputHandler,
      fakeTransport as any,
      worker as any, // RLWorkerClient acts as WorkerClient
      gameView,
    );

    // Hide loading, show game
    this.hideLoading();
    this.showGame();

    // Wait for and apply crop region (if we received one)
    setTimeout(async () => {
      try {
        const cropRegion = await Promise.race([
          cropRegionPromise,
          new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
        ]);
        console.log('[RLClient] Applying crop region to camera:', cropRegion);
        this.applyCropRegion(gameRenderer, cropRegion);
      } catch (err) {
        console.log('[RLClient] No crop region received or timeout');
      }
    }, 100);

    // Start the game
    console.log('[RLClient] Starting game runner...');
    runner.start();

    // Auto-spawn at random location for RL mode
    this.autoSpawn(gameView, worker);

    // Tell Python we're ready to receive game state
    console.log('[RLClient] Sending ready signal to Python...');
    worker.sendReady();

    // Setup cleanup
    this.gameStop = () => {
      console.log('[RLClient] Stopping game');
      worker.cleanup();
      // runner doesn't have a stop method, but cleanup is handled
    };

    console.log('[RLClient] ✅ RL visualization ready!');
  }

  private showLoading(message: string) {
    const loading = document.getElementById('loading-screen');
    if (loading) {
      loading.style.display = 'flex';
      const messageEl = loading.querySelector('.loading-message');
      if (messageEl) {
        messageEl.textContent = message;
      }
    }
  }

  private hideLoading() {
    const loading = document.getElementById('loading-screen');
    if (loading) {
      loading.style.display = 'none';
    }
  }

  private showGame() {
    const app = document.getElementById('app');
    if (app) {
      app.style.display = 'block';
    }
  }

  private showError(message: string) {
    const loading = document.getElementById('loading-screen');
    if (loading) {
      loading.innerHTML = `
        <div style="text-align: center; color: white; padding: 40px;">
          <h1 style="color: #ff4136; margin-bottom: 20px;">Error</h1>
          <p style="font-size: 18px; margin-bottom: 20px;">${message}</p>
          <p style="color: #aaa;">Check the console for more details.</p>
          <button
            onclick="location.reload()"
            style="margin-top: 30px; padding: 10px 20px; font-size: 16px; cursor: pointer;"
          >
            Retry
          </button>
        </div>
      `;
    }
  }

  /**
   * Apply crop region to camera - zoom and center on the specified region
   */
  private applyCropRegion(gameRenderer: GameRenderer, cropRegion: { x: number; y: number; width: number; height: number }) {
    console.log('[RLClient] applyCropRegion() called with:', cropRegion);

    // Access the transform handler from the renderer
    const transformHandler = (gameRenderer as any).transformHandler;
    if (!transformHandler) {
      console.warn('[RLClient] Could not access transformHandler');
      return;
    }

    // Calculate center of crop region
    const centerX = cropRegion.x + cropRegion.width / 2;
    const centerY = cropRegion.y + cropRegion.height / 2;
    const spawnRadius = Math.min(cropRegion.width, cropRegion.height) / 2 - 20;
    console.log(`[RLClient] Calculated crop center: (${centerX}, ${centerY}), spawn radius: ${spawnRadius}`);

    // Get viewport dimensions
    const canvas = document.querySelector('canvas');
    if (!canvas) {
      console.warn('[RLClient] Could not find canvas');
      return;
    }

    const vpWidth = canvas.width;
    const vpHeight = canvas.height;

    // Calculate zoom to fit crop region in viewport (with 90% fit to leave some padding)
    const scaleX = (vpWidth / cropRegion.width) * 0.9;
    const scaleY = (vpHeight / cropRegion.height) * 0.9;
    const scale = Math.min(scaleX, scaleY);

    // Calculate offset to center the crop region
    // The transform handler uses offsetX/offsetY to pan the view
    // offset represents the world coordinate at the center of the screen
    const offsetX = centerX;
    const offsetY = centerY;

    console.log(`[RLClient] Setting camera: center=(${centerX}, ${centerY}), scale=${scale.toFixed(2)}`);
    transformHandler.override(offsetX, offsetY, scale);

    // Crop region visualization disabled
    // this.drawCropRegionBoundary(gameRenderer, cropRegion);
  }

  /**
   * Draw a rectangle showing the crop region boundaries (DISABLED)
   */
  private drawCropRegionBoundary(gameRenderer: GameRenderer, cropRegion: { x: number; y: number; width: number; height: number }) {
    // Visualization disabled per user request
    console.log('[RLClient] Crop region visualization disabled');
  }

  /**
   * Setup coordinate debugger - shows mouse position in world coordinates
   */
  private setupCoordinateDebugger(canvas: HTMLCanvasElement, gameRenderer: GameRenderer) {
    // Create debug overlay div
    const debugDiv = document.createElement('div');
    debugDiv.id = 'coordinate-debugger';
    debugDiv.style.cssText = `
      position: fixed;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 14px;
      pointer-events: none;
      z-index: 2000;
      white-space: pre;
    `;
    debugDiv.textContent = 'Move mouse over map to see coordinates';
    document.body.appendChild(debugDiv);

    // Add mouse move listener
    canvas.addEventListener('mousemove', (event) => {
      const rect = canvas.getBoundingClientRect();
      const canvasX = event.clientX - rect.left;
      const canvasY = event.clientY - rect.top;

      // Convert canvas coordinates to world coordinates
      const transformHandler = (gameRenderer as any).transformHandler;
      if (!transformHandler || !transformHandler.transform) {
        debugDiv.textContent = `Canvas: (${Math.floor(canvasX)}, ${Math.floor(canvasY)})  |  Waiting for transform...`;
        return;
      }

      // Get current transform
      const transform = transformHandler.transform;
      const scale = transform.k || 1;
      const offsetX = transform.x || 0;
      const offsetY = transform.y || 0;

      // Convert to world coordinates
      // The transform formula is: screen = (world - offset) * scale + canvas_center
      // So: world = (screen - canvas_center) / scale + offset
      const worldX = Math.floor((canvasX - canvas.width / 2) / scale + offsetX);
      const worldY = Math.floor((canvasY - canvas.height / 2) / scale + offsetY);

      // Update debug display
      debugDiv.textContent = `Map Coordinates: (${worldX}, ${worldY})  |  Canvas: (${Math.floor(canvasX)}, ${Math.floor(canvasY)})  |  Zoom: ${scale.toFixed(2)}x`;
    });

    console.log('[RLClient] Coordinate debugger enabled');
  }

  /**
   * Auto-spawn at a random valid location for RL mode
   * DISABLED - spawn is handled by the Python/TypeScript bridge
   */
  private autoSpawn(gameView: GameView, worker: RLWorkerClient) {
    console.log('[RLClient] Auto-spawn disabled - spawn handled by game bridge');
    // The TypeScript game bridge already spawned all players including the RL agent
    // We don't need to send a spawn command from the client
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('[RLClient] DOM loaded, initializing RL client');
  new RLClient().initialize();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  console.log('[RLClient] Page unloading');
});
