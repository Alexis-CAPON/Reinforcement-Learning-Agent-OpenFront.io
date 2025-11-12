/**
 * RLGameRunner - Runs the game in RL visualization mode
 *
 * Uses SimpleTileRenderer with colored terrain tiles
 */

import { EventBus } from './utilities/EventBus';
import { RLTransport } from './RLTransport';
import { SimpleTileRenderer } from './graphics/SimpleTileRenderer';
import * as PIXI from 'pixi.js';

export class RLGameRunner {
  private app: PIXI.Application | null = null;
  private tileRenderer: SimpleTileRenderer | null = null;
  public transport: RLTransport;
  public eventBus: EventBus;
  private gameContainer: PIXI.Container | null = null;

  constructor() {
    this.eventBus = new EventBus();

    // Get WebSocket URL from query params or use default
    const urlParams = new URLSearchParams(window.location.search);
    const wsUrl = urlParams.get('ws') || 'ws://localhost:8765';

    this.transport = new RLTransport(this.eventBus, wsUrl);
  }

  async start() {
    console.log('[RLGameRunner] Starting RL visualization mode');

    // Show loading
    this.showLoadingScreen();

    try {
      // Connect to Python bridge
      console.log('[RLGameRunner] Step 1: Connecting to Python bridge...');
      await this.transport.connect();
      console.log('[RLGameRunner] ✅ Connected to Python bridge');

      // Wait for first game state
      console.log('[RLGameRunner] Step 2: Waiting for initial game state...');
      const initialState = await this.waitForGameState();
      console.log('[RLGameRunner] ✅ Received initial game state:', initialState);

      // Initialize renderer with game state
      console.log('[RLGameRunner] Step 3: Initializing renderer...');
      await this.initializeRenderer(initialState);
      console.log('[RLGameRunner] ✅ Renderer initialized');

      // Hide loading screen
      this.hideLoadingScreen();

      console.log('[RLGameRunner] ✅ RL visualization ready!');
    } catch (error) {
      console.error('[RLGameRunner] ❌ Failed to start:', error);
      console.error('[RLGameRunner] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
      this.showError(`Failed to initialize: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async waitForGameState(): Promise<any> {
    return new Promise((resolve) => {
      const handler = (state: any) => {
        this.eventBus.off('rl-game-state', handler);
        resolve(state);
      };
      this.eventBus.on('rl-game-state', handler);
    });
  }

  private async initializeRenderer(initialState: any) {
    const container = document.getElementById('game-canvas-container')!;

    // Create Pixi.js application
    this.app = new PIXI.Application();
    await this.app.init({
      width: initialState.map_width * 4,
      height: initialState.map_height * 4,
      backgroundColor: 0x000000,
      antialias: false,
    });

    container.appendChild(this.app.canvas as HTMLCanvasElement);

    // Create game container
    this.gameContainer = new PIXI.Container();
    this.app.stage.addChild(this.gameContainer);

    // Create tile renderer
    this.tileRenderer = new SimpleTileRenderer(this.gameContainer);

    // Render initial state
    this.renderGameState(initialState);

    // Listen for game state updates
    this.eventBus.on('rl-game-state', (state: any) => {
      this.renderGameState(state);
    });
  }

  private renderGameState(state: any) {
    if (!this.tileRenderer || !state) return;

    // Render tiles with terrain colors
    this.tileRenderer.render(
      state.tiles,
      state.players,
      state.map_width,
      state.map_height
    );
  }

  private showLoadingScreen() {
    const loading = document.getElementById('loading-screen');
    if (loading) {
      loading.style.display = 'flex';
    }
  }

  private hideLoadingScreen() {
    const loading = document.getElementById('loading-screen');
    const gameContainer = document.getElementById('game-container');

    if (loading) {
      loading.style.display = 'none';
    }
    if (gameContainer) {
      gameContainer.style.display = 'block';
    }
  }

  private showError(message: string) {
    const loading = document.getElementById('loading-screen');
    if (loading) {
      loading.innerHTML = `
        <div style="text-align: center; color: white;">
          <h1 style="color: #ff4136;">Error</h1>
          <p>${message}</p>
          <p style="margin-top: 20px; color: #aaa;">
            Check the console for more details.
          </p>
        </div>
      `;
    }
  }

  stop() {
    if (this.app) {
      this.app.destroy(true);
    }
    this.transport.disconnect();
  }
}
