/**
 * RLTransport - Connects to Phase 4 visual bridge instead of multiplayer server
 *
 * This replaces the normal Transport for RL visualization mode
 */

import { EventBus } from './utilities/EventBus';

interface ModelState {
  type: 'model_state';
  tick: number;
  observation: number[];
  action: {
    direction_probs: number[];
    intensity_probs: number[];
    build_prob: number;
    selected_action: number;
    direction: string;
    intensity: number;
    build: boolean;
  };
  value_estimate: number;
  reward: number;
  cumulative_reward: number;
}

interface GameStateUpdate {
  type: 'game_state';
  tick: number;
  visual_state: any;
}

interface GameUpdate {
  type: 'game_update';
  tick: number;
  visual_state: any;
  gameUpdate: any;
}

type RLMessage = ModelState | GameStateUpdate | GameUpdate;

export class RLTransport {
  private ws: WebSocket | null = null;
  private eventBus: EventBus;
  public wsUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  constructor(eventBus: EventBus, wsUrl: string = 'ws://localhost:8765') {
    this.eventBus = eventBus;
    this.wsUrl = wsUrl;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log('[RLTransport] Connecting to', this.wsUrl);

      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('[RLTransport] Connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: RLMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[RLTransport] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[RLTransport] WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('[RLTransport] Disconnected');
        this.attemptReconnect();
      };
    });
  }

  private handleMessage(message: RLMessage) {
    if (message.type === 'game_state') {
      // Emit game state update event
      this.eventBus.emit('rl-game-state', message.visual_state);
    } else if (message.type === 'game_update') {
      // Emit game update for real GameView (with full UI)
      this.eventBus.emit('rl-game-update', message.gameUpdate);
      // Also emit visual state for backward compatibility
      this.eventBus.emit('rl-game-state', message.visual_state);
    } else if (message.type === 'model_state') {
      // Emit model state for overlay visualization
      this.eventBus.emit('rl-model-state', message);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[RLTransport] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = 1000 * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[RLTransport] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[RLTransport] Reconnect failed:', error);
      });
    }, delay);
  }

  sendControl(command: string, data?: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'control',
        command,
        ...data
      }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
