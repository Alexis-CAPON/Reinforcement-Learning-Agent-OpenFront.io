/**
 * Control panel for RL Visualizer
 * Provides playback controls and overlay toggles
 */

export class RLControlPanel {
  private container: HTMLElement;
  private callbacks: {
    onPlay?: () => void;
    onPause?: () => void;
    onStep?: () => void;
    onReset?: () => void;
    onSpeedChange?: (speed: number) => void;
    onToggleOverlay?: (name: string, enabled: boolean) => void;
  } = {};

  constructor(parentElement: HTMLElement) {
    this.container = document.createElement('div');
    this.container.id = 'rl-control-panel';
    this.container.className = 'rl-control-panel';
    parentElement.appendChild(this.container);

    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="rl-controls-container">
        <h3>RL Visualizer Controls</h3>

        <div class="playback-controls">
          <h4>Playback</h4>
          <button id="rl-play" class="rl-btn">▶️ Play</button>
          <button id="rl-pause" class="rl-btn">⏸️ Pause</button>
          <button id="rl-step" class="rl-btn">⏭️ Step</button>
          <button id="rl-reset" class="rl-btn">⏮️ Reset</button>
          <br><br>
          <label>Speed: <span id="rl-speed-label">1x</span></label>
          <input type="range" id="rl-speed" min="1" max="10" value="1" step="1">
        </div>

        <div class="overlay-controls">
          <h4>Overlays</h4>
          <label>
            <input type="checkbox" id="rl-overlay-observation" />
            Observation Heatmap
          </label>
          <label>
            <input type="checkbox" id="rl-overlay-action" checked />
            Action Probabilities
          </label>
          <label>
            <input type="checkbox" id="rl-overlay-value" checked />
            Value Estimates
          </label>
          <label>
            <input type="checkbox" id="rl-overlay-attention" />
            Attention Map
          </label>
          <label>
            <input type="checkbox" id="rl-overlay-metrics" checked />
            Metrics Display
          </label>
        </div>
      </div>

      <style>
        .rl-control-panel {
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(0, 0, 0, 0.85);
          border: 2px solid #ff4136;
          border-radius: 10px;
          padding: 20px;
          color: #fff;
          font-family: Arial, sans-serif;
          z-index: 1000;
          max-width: 300px;
        }

        .rl-controls-container h3 {
          margin-top: 0;
          color: #ff4136;
          border-bottom: 2px solid #ff4136;
          padding-bottom: 10px;
        }

        .rl-controls-container h4 {
          color: #ff851b;
          margin-top: 15px;
          margin-bottom: 10px;
        }

        .playback-controls, .overlay-controls {
          margin-bottom: 20px;
        }

        .rl-btn {
          background: linear-gradient(135deg, #ff4136 0%, #ff851b 100%);
          color: white;
          border: none;
          padding: 8px 16px;
          margin: 5px 5px 5px 0;
          border-radius: 5px;
          cursor: pointer;
          font-weight: bold;
          transition: transform 0.2s;
        }

        .rl-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 4px 15px rgba(255, 65, 54, 0.4);
        }

        .rl-btn:active {
          transform: scale(0.95);
        }

        #rl-speed {
          width: 100%;
          margin-top: 10px;
        }

        .overlay-controls label {
          display: block;
          margin: 8px 0;
          cursor: pointer;
          transition: color 0.2s;
        }

        .overlay-controls label:hover {
          color: #ff851b;
        }

        .overlay-controls input[type="checkbox"] {
          margin-right: 8px;
          cursor: pointer;
        }
      </style>
    `;

    this.attachEventListeners();
  }

  private attachEventListeners() {
    // Playback controls
    document.getElementById('rl-play')?.addEventListener('click', () => {
      if (this.callbacks.onPlay) this.callbacks.onPlay();
    });

    document.getElementById('rl-pause')?.addEventListener('click', () => {
      if (this.callbacks.onPause) this.callbacks.onPause();
    });

    document.getElementById('rl-step')?.addEventListener('click', () => {
      if (this.callbacks.onStep) this.callbacks.onStep();
    });

    document.getElementById('rl-reset')?.addEventListener('click', () => {
      if (this.callbacks.onReset) this.callbacks.onReset();
    });

    // Speed control
    const speedSlider = document.getElementById('rl-speed') as HTMLInputElement;
    const speedLabel = document.getElementById('rl-speed-label');
    speedSlider?.addEventListener('input', (e) => {
      const speed = parseInt((e.target as HTMLInputElement).value);
      if (speedLabel) speedLabel.textContent = `${speed}x`;
      if (this.callbacks.onSpeedChange) this.callbacks.onSpeedChange(speed);
    });

    // Overlay toggles
    const overlayIds = ['observation', 'action', 'value', 'attention', 'metrics'];
    overlayIds.forEach(id => {
      const checkbox = document.getElementById(`rl-overlay-${id}`) as HTMLInputElement;
      checkbox?.addEventListener('change', (e) => {
        const enabled = (e.target as HTMLInputElement).checked;
        if (this.callbacks.onToggleOverlay) {
          this.callbacks.onToggleOverlay(id, enabled);
        }
      });
    });
  }

  onPlay(callback: () => void) {
    this.callbacks.onPlay = callback;
  }

  onPause(callback: () => void) {
    this.callbacks.onPause = callback;
  }

  onStep(callback: () => void) {
    this.callbacks.onStep = callback;
  }

  onReset(callback: () => void) {
    this.callbacks.onReset = callback;
  }

  onSpeedChange(callback: (speed: number) => void) {
    this.callbacks.onSpeedChange = callback;
  }

  onToggleOverlay(callback: (name: string, enabled: boolean) => void) {
    this.callbacks.onToggleOverlay = callback;
  }

  destroy() {
    this.container.remove();
  }
}
