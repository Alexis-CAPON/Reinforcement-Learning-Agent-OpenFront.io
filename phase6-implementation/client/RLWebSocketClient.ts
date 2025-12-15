/**
 * WebSocket client for receiving RL model state from Python
 */

import { RLMessage, GameStateUpdate, ModelStateUpdate, ControlCommand } from './RLTypes';

export class RLWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 1000;

  private onGameStateCallback?: (state: GameStateUpdate) => void;
  private onModelStateCallback?: (state: ModelStateUpdate) => void;
  private onConnectCallback?: () => void;
  private onDisconnectCallback?: () => void;
  private onErrorCallback?: (error: Error) => void;

  constructor(url: string = 'ws://localhost:8765') {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[RLWebSocket] Connected to server');
          this.reconnectAttempts = 0;
          if (this.onConnectCallback) {
            this.onConnectCallback();
          }
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: RLMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[RLWebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (event) => {
          console.error('[RLWebSocket] WebSocket error:', event);
          const error = new Error('WebSocket error');
          if (this.onErrorCallback) {
            this.onErrorCallback(error);
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[RLWebSocket] Disconnected from server');
          if (this.onDisconnectCallback) {
            this.onDisconnectCallback();
          }
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: RLMessage) {
    switch (message.type) {
      case 'game_state':
        if (this.onGameStateCallback) {
          this.onGameStateCallback(message as GameStateUpdate);
        }
        break;

      case 'model_state':
        if (this.onModelStateCallback) {
          this.onModelStateCallback(message as ModelStateUpdate);
        }
        break;

      default:
        console.warn('[RLWebSocket] Unknown message type:', message);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[RLWebSocket] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[RLWebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[RLWebSocket] Reconnect failed:', error);
      });
    }, delay);
  }

  sendControl(command: ControlCommand) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(command));
    } else {
      console.warn('[RLWebSocket] Cannot send command, not connected');
    }
  }

  onGameState(callback: (state: GameStateUpdate) => void) {
    this.onGameStateCallback = callback;
  }

  onModelState(callback: (state: ModelStateUpdate) => void) {
    this.onModelStateCallback = callback;
  }

  onConnect(callback: () => void) {
    this.onConnectCallback = callback;
  }

  onDisconnect(callback: () => void) {
    this.onDisconnectCallback = callback;
  }

  onError(callback: (error: Error) => void) {
    this.onErrorCallback = callback;
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
