/**
 * Phase 4 RL Visualizer - Main Entry Point
 *
 * This visualizer shows the full game with RL model overlays in real-time
 */

import * as PIXI from 'pixi.js';
import { RLWebSocketClient } from './RLWebSocketClient';
import { RLOverlayLayer } from './graphics/layers/RLOverlayLayer';
import { RLControlPanel } from './ui/RLControlPanel';
import { GameStateUpdate, ModelStateUpdate } from './RLTypes';

class RLVisualizer {
  private app: PIXI.Application | null = null;
  private wsClient: RLWebSocketClient;
  private overlayLayer: RLOverlayLayer | null = null;
  private controlPanel: RLControlPanel | null = null;

  private currentGameState: GameStateUpdate | null = null;
  private currentModelState: ModelStateUpdate | null = null;

  private isPlaying: boolean = false;
  private speed: number = 1;

  // Game rendering
  private gameContainer: PIXI.Container | null = null;
  private tileGraphics: PIXI.Graphics | null = null;
  private tileSize: number = 4;  // pixels per tile

  constructor() {
    // Connect to WebSocket server
    const wsUrl = this.getWebSocketUrl();
    this.wsClient = new RLWebSocketClient(wsUrl);

    this.setupWebSocket();
  }

  private getWebSocketUrl(): string {
    // Check URL parameters for custom WebSocket URL
    const params = new URLSearchParams(window.location.search);
    return params.get('ws') || 'ws://localhost:8765';
  }

  private setupWebSocket() {
    this.wsClient.onConnect(() => {
      console.log('[RLVisualizer] Connected to Python bridge');
      this.updateConnectionStatus(true);
      this.hideLoadingScreen();
    });

    this.wsClient.onDisconnect(() => {
      console.log('[RLVisualizer] Disconnected from Python bridge');
      this.updateConnectionStatus(false);
    });

    this.wsClient.onError((error) => {
      console.error('[RLVisualizer] WebSocket error:', error);
    });

    this.wsClient.onGameState((state) => {
      this.currentGameState = state;
      this.renderGameState(state);
    });

    this.wsClient.onModelState((state) => {
      this.currentModelState = state;
      this.renderModelState(state);
    });
  }

  async initialize() {
    console.log('[RLVisualizer] Initializing...');

    // Connect to WebSocket
    try {
      await this.wsClient.connect();
    } catch (error) {
      console.error('[RLVisualizer] Failed to connect to WebSocket:', error);
      this.showError('Failed to connect to Python bridge. Make sure the server is running.');
      return;
    }

    // Wait for first game state to determine map size
    // For now, use a default size (will be updated when first state arrives)
    await this.initializePixiApp(150, 150);

    // Create control panel
    this.createControlPanel();

    console.log('[RLVisualizer] Initialization complete');
  }

  private async initializePixiApp(mapWidth: number, mapHeight: number) {
    // Initialize Pixi.js application
    this.app = new PIXI.Application();
    await this.app.init({
      width: mapWidth * this.tileSize,
      height: mapHeight * this.tileSize,
      backgroundColor: 0x0a0a0a,
      antialias: false,  // Pixel perfect rendering
    });

    // Add canvas to container
    const canvasContainer = document.getElementById('canvas-container');
    if (canvasContainer) {
      canvasContainer.appendChild(this.app.canvas);
    }

    // Create game container for tiles
    this.gameContainer = new PIXI.Container();
    this.app.stage.addChild(this.gameContainer);

    // Create graphics for tiles
    this.tileGraphics = new PIXI.Graphics();
    this.gameContainer.addChild(this.tileGraphics);

    // Create overlay layer (on top of game tiles)
    this.overlayLayer = new RLOverlayLayer(mapWidth, mapHeight);
    this.app.stage.addChild(this.overlayLayer.getContainer());

    // Start render loop
    this.app.ticker.add(() => {
      // Render loop runs automatically
    });
  }

  private createControlPanel() {
    const gameContainer = document.getElementById('game-container');
    if (!gameContainer) return;

    this.controlPanel = new RLControlPanel(gameContainer);

    // Wire up callbacks
    this.controlPanel.onPlay(() => this.play());
    this.controlPanel.onPause(() => this.pause());
    this.controlPanel.onStep(() => this.step());
    this.controlPanel.onReset(() => this.reset());
    this.controlPanel.onSpeedChange((speed) => this.setSpeed(speed));
    this.controlPanel.onToggleOverlay((name, enabled) => this.toggleOverlay(name, enabled));
  }

  private renderGameState(state: GameStateUpdate) {
    // Initialize Pixi app if not already done (with correct map size)
    if (!this.app && state.visual_state) {
      const { map_width, map_height } = state.visual_state;
      this.initializePixiApp(map_width, map_height);
    }

    // Render game tiles
    if (this.tileGraphics && state.visual_state) {
      this.drawGameTiles(state.visual_state);
    }
  }

  private drawGameTiles(visualState: any) {
    if (!this.tileGraphics) return;

    // Clear previous frame
    this.tileGraphics.clear();

    // Draw each tile
    for (const tile of visualState.tiles) {
      let color: number;

      if (tile.is_mountain) {
        // Mountains are gray
        color = 0x505050;
      } else if (tile.owner_id === 0) {
        // Neutral territory is dark
        color = 0x1a1a1a;
      } else {
        // Player territory - find player color
        const player = visualState.players.find((p: any) => p.id === tile.owner_id);
        if (player) {
          // Convert hex color string to number
          color = parseInt(player.color.replace('#', ''), 16);
        } else {
          color = 0xffffff;
        }
      }

      // Draw tile
      this.tileGraphics.rect(
        tile.x * this.tileSize,
        tile.y * this.tileSize,
        this.tileSize,
        this.tileSize
      );
      this.tileGraphics.fill(color);

      // Draw city marker (white center)
      if (tile.is_city) {
        this.tileGraphics.rect(
          tile.x * this.tileSize + 1,
          tile.y * this.tileSize + 1,
          this.tileSize - 2,
          this.tileSize - 2
        );
        this.tileGraphics.fill(0xffffff);
      }
    }
  }

  private renderModelState(state: ModelStateUpdate) {
    if (this.overlayLayer) {
      this.overlayLayer.updateModelState(state);
    }

    // Update metrics panel
    this.updateMetrics(state);
  }

  private updateMetrics(state: ModelStateUpdate) {
    const elements = {
      step: document.getElementById('metric-step'),
      reward: document.getElementById('metric-reward'),
      cumulative: document.getElementById('metric-cumulative'),
      value: document.getElementById('metric-value'),
      action: document.getElementById('metric-action'),
    };

    if (elements.step) elements.step.textContent = state.tick.toString();
    if (elements.reward) elements.reward.textContent = state.reward.toFixed(2);
    if (elements.cumulative) elements.cumulative.textContent = state.cumulative_reward.toFixed(2);
    if (elements.value) elements.value.textContent = state.value_estimate.toFixed(2);
    if (elements.action) {
      const action = state.action;
      elements.action.textContent = `${action.direction} ${(action.intensity * 100).toFixed(0)}%${action.build ? ' 🏗️' : ''}`;
    }
  }

  private updateConnectionStatus(connected: boolean) {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    if (statusIndicator && statusText) {
      if (connected) {
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected';
      } else {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Disconnected';
      }
    }
  }

  private hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    const gameContainer = document.getElementById('game-container');

    if (loadingScreen) {
      loadingScreen.style.display = 'none';
    }
    if (gameContainer) {
      gameContainer.style.display = 'block';
    }
  }

  private showError(message: string) {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.innerHTML = `
        <h1>Error</h1>
        <p>${message}</p>
        <p style="margin-top: 20px; color: #aaa;">Please check the console for more details.</p>
      `;
    }
  }

  // Control methods
  private play() {
    this.isPlaying = true;
    this.wsClient.sendControl({ type: 'control', command: 'play' });
  }

  private pause() {
    this.isPlaying = false;
    this.wsClient.sendControl({ type: 'control', command: 'pause' });
  }

  private step() {
    this.wsClient.sendControl({ type: 'control', command: 'step' });
  }

  private reset() {
    this.wsClient.sendControl({ type: 'control', command: 'reset' });
  }

  private setSpeed(speed: number) {
    this.speed = speed;
    this.wsClient.sendControl({ type: 'control', command: 'speed', speed });
  }

  private toggleOverlay(name: string, enabled: boolean) {
    if (this.overlayLayer) {
      const overlayMap: { [key: string]: any } = {
        'observation': 'showObservation',
        'action': 'showActionProbs',
        'value': 'showValue',
        'attention': 'showAttention',
        'metrics': 'showMetrics',
      };

      const overlayKey = overlayMap[name];
      if (overlayKey) {
        this.overlayLayer.toggleOverlay(overlayKey, enabled);
      }
    }

    // Toggle metrics panel visibility
    if (name === 'metrics') {
      const metricsPanel = document.getElementById('metrics-panel');
      if (metricsPanel) {
        metricsPanel.style.display = enabled ? 'block' : 'none';
      }
    }
  }
}

// Initialize visualizer when page loads
window.addEventListener('DOMContentLoaded', async () => {
  const visualizer = new RLVisualizer();
  await visualizer.initialize();
});
