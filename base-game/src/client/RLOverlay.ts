/**
 * RLOverlay - Simple overlay component to display RL model decisions
 *
 * Shows:
 * - Current action probabilities
 * - Value estimate
 * - Reward
 * - Cumulative reward
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface ModelState {
  tick: number;
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

@customElement('rl-overlay')
export class RLOverlay extends LitElement {
  @state() private modelState: ModelState | null = null;
  @state() private visible: boolean = true;

  static styles = css`
    :host {
      position: fixed;
      bottom: 10px;
      left: 10px;
      z-index: 1000;
      pointer-events: none;
    }

    .overlay-container {
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 15px;
      border-radius: 8px;
      font-family: monospace;
      font-size: 12px;
      min-width: 250px;
      border: 2px solid #0075ff;
      pointer-events: auto;
    }

    .overlay-container.hidden {
      display: none;
    }

    .overlay-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      border-bottom: 1px solid #0075ff;
      padding-bottom: 8px;
    }

    .overlay-title {
      font-weight: bold;
      color: #0075ff;
      font-size: 14px;
    }

    .toggle-button {
      background: #0075ff;
      color: white;
      border: none;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 11px;
    }

    .toggle-button:hover {
      background: #0060d0;
    }

    .section {
      margin-bottom: 12px;
    }

    .section-title {
      color: #00d0ff;
      font-weight: bold;
      margin-bottom: 4px;
    }

    .value-row {
      display: flex;
      justify-content: space-between;
      margin: 2px 0;
    }

    .value-label {
      color: #aaa;
    }

    .value-data {
      color: #fff;
      font-weight: bold;
    }

    .action-highlight {
      color: #00ff00;
      font-weight: bold;
    }

    .prob-bar {
      height: 4px;
      background: #333;
      border-radius: 2px;
      overflow: hidden;
      margin-top: 2px;
    }

    .prob-bar-fill {
      height: 100%;
      background: #0075ff;
      transition: width 0.2s ease;
    }

    .direction-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2px;
      margin-top: 4px;
    }

    .direction-cell {
      background: #222;
      padding: 4px;
      text-align: center;
      border-radius: 2px;
      font-size: 10px;
    }

    .direction-cell.selected {
      background: #00ff00;
      color: #000;
      font-weight: bold;
    }
  `;

  connectedCallback() {
    super.connectedCallback();

    // Listen for model state updates
    window.addEventListener('rl-model-state', this.handleModelState.bind(this) as EventListener);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('rl-model-state', this.handleModelState.bind(this) as EventListener);
  }

  private handleModelState(event: CustomEvent) {
    this.modelState = event.detail;
  }

  private toggleVisibility() {
    this.visible = !this.visible;
  }

  render() {
    if (!this.modelState) {
      return html`
        <div class="overlay-container">
          <div class="overlay-header">
            <span class="overlay-title">RL Model</span>
          </div>
          <div style="color: #aaa;">Waiting for model data...</div>
        </div>
      `;
    }

    const { action, value_estimate, reward, cumulative_reward } = this.modelState;

    return html`
      <div class="overlay-container ${this.visible ? '' : 'hidden'}">
        <div class="overlay-header">
          <span class="overlay-title">RL Model</span>
          <button class="toggle-button" @click=${this.toggleVisibility}>
            ${this.visible ? 'Hide' : 'Show'}
          </button>
        </div>

        ${this.visible ? html`
          <!-- Current Action -->
          <div class="section">
            <div class="section-title">Current Action</div>
            <div class="value-row">
              <span class="value-label">Direction:</span>
              <span class="action-highlight">${action.direction}</span>
            </div>
            <div class="value-row">
              <span class="value-label">Intensity:</span>
              <span class="action-highlight">${(action.intensity * 100).toFixed(0)}%</span>
            </div>
            <div class="value-row">
              <span class="value-label">Build:</span>
              <span class="action-highlight">${action.build ? 'YES' : 'NO'}</span>
            </div>
          </div>

          <!-- Value & Rewards -->
          <div class="section">
            <div class="section-title">Value & Rewards</div>
            <div class="value-row">
              <span class="value-label">Value Estimate:</span>
              <span class="value-data">${value_estimate.toFixed(3)}</span>
            </div>
            <div class="value-row">
              <span class="value-label">Reward:</span>
              <span class="value-data">${reward.toFixed(2)}</span>
            </div>
            <div class="value-row">
              <span class="value-label">Cumulative:</span>
              <span class="value-data">${cumulative_reward.toFixed(0)}</span>
            </div>
          </div>

          <!-- Action Probabilities -->
          <div class="section">
            <div class="section-title">Direction Probs</div>
            ${this.renderDirectionGrid(action.direction_probs, action.direction)}
          </div>

          <div class="section">
            <div class="section-title">Intensity Probs</div>
            ${action.intensity_probs.slice(0, 5).map((prob, i) => html`
              <div class="value-row">
                <span class="value-label">${(i * 25)}%:</span>
                <span class="value-data">${(prob * 100).toFixed(1)}%</span>
              </div>
              <div class="prob-bar">
                <div class="prob-bar-fill" style="width: ${prob * 100}%"></div>
              </div>
            `)}
          </div>

          <div class="section">
            <div class="value-row">
              <span class="value-label">Build Prob:</span>
              <span class="value-data">${(action.build_prob * 100).toFixed(1)}%</span>
            </div>
            <div class="prob-bar">
              <div class="prob-bar-fill" style="width: ${action.build_prob * 100}%"></div>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  private renderDirectionGrid(probs: number[], selectedDirection: string) {
    const directions = ['NW', 'N', 'NE', 'W', 'IDLE', 'E', 'SW', 'S', 'SE'];

    return html`
      <div class="direction-grid">
        ${directions.map((dir, i) => html`
          <div class="direction-cell ${dir === selectedDirection ? 'selected' : ''}">
            ${dir}<br>
            ${(probs[i] * 100).toFixed(0)}%
          </div>
        `)}
      </div>
    `;
  }
}
