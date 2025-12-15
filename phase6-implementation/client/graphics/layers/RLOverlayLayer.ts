/**
 * Master overlay layer for RL visualizations
 * Renders on top of all game layers to show model internals
 */

import * as PIXI from 'pixi.js';
import { ModelStateUpdate, OverlayConfig } from '../../RLTypes';

export class RLOverlayLayer {
  private container: PIXI.Container;
  private modelState: ModelStateUpdate | null = null;
  private config: OverlayConfig;

  // Sub-components
  private actionArrows: PIXI.Graphics;
  private heatmapSprite: PIXI.Sprite | null = null;
  private valueText: PIXI.Text;

  private mapWidth: number;
  private mapHeight: number;

  constructor(mapWidth: number, mapHeight: number) {
    this.mapWidth = mapWidth;
    this.mapHeight = mapHeight;

    this.container = new PIXI.Container();
    this.container.name = 'RLOverlayLayer';

    // Initialize config (all enabled by default)
    this.config = {
      showObservation: false,
      showActionProbs: true,
      showValue: true,
      showAttention: false,
      showMetrics: true,
    };

    // Initialize graphics objects
    this.actionArrows = new PIXI.Graphics();
    this.container.addChild(this.actionArrows);

    this.valueText = new PIXI.Text('', {
      fontFamily: 'Arial',
      fontSize: 14,
      fill: 0xffffff,
      stroke: 0x000000,
      strokeThickness: 3,
    });
    this.valueText.position.set(10, 10);
    this.container.addChild(this.valueText);
  }

  updateModelState(state: ModelStateUpdate) {
    this.modelState = state;
    this.render();
  }

  private render() {
    if (!this.modelState) return;

    // Clear previous render
    this.actionArrows.clear();

    // Render action probabilities
    if (this.config.showActionProbs) {
      this.renderActionProbabilities();
    }

    // Render value estimate
    if (this.config.showValue) {
      this.renderValueEstimate();
    }

    // Render observation heatmap
    if (this.config.showObservation) {
      this.renderObservationHeatmap();
    }
  }

  private renderActionProbabilities() {
    if (!this.modelState) return;

    const action = this.modelState.action;
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT'];
    const angles = [270, 315, 0, 45, 90, 135, 180, 225, 0]; // Degrees

    // Draw from center of map
    const centerX = this.mapWidth * 16 / 2;  // Assuming 16px tile size
    const centerY = this.mapHeight * 16 / 2;
    const radius = 80;

    directions.forEach((dir, idx) => {
      if (dir === 'WAIT') return;

      const prob = action.direction_probs[idx];
      const angle = angles[idx] * Math.PI / 180;
      const isSelected = idx === Math.floor(action.selected_action / 10);

      // Arrow end position
      const endX = centerX + Math.cos(angle) * radius;
      const endY = centerY + Math.sin(angle) * radius;

      // Color based on selection and probability
      const color = isSelected ? 0x00ff00 : 0xffffff;
      const alpha = Math.max(0.2, prob);
      const width = 2 + prob * 6;

      // Draw arrow
      this.actionArrows.lineStyle(width, color, alpha);
      this.actionArrows.moveTo(centerX, centerY);
      this.actionArrows.lineTo(endX, endY);

      // Draw arrowhead
      const arrowSize = 10 + prob * 10;
      const arrowAngle = Math.PI / 6;
      this.actionArrows.lineTo(
        endX - arrowSize * Math.cos(angle - arrowAngle),
        endY - arrowSize * Math.sin(angle - arrowAngle)
      );
      this.actionArrows.moveTo(endX, endY);
      this.actionArrows.lineTo(
        endX - arrowSize * Math.cos(angle + arrowAngle),
        endY - arrowSize * Math.sin(angle + arrowAngle)
      );

      // Draw probability text
      const textX = centerX + Math.cos(angle) * (radius + 20);
      const textY = centerY + Math.sin(angle) * (radius + 20);

      const probText = new PIXI.Text(`${(prob * 100).toFixed(0)}%`, {
        fontFamily: 'Arial',
        fontSize: 12,
        fill: color,
        stroke: 0x000000,
        strokeThickness: 2,
      });
      probText.anchor.set(0.5);
      probText.position.set(textX, textY);
      this.container.addChild(probText);
    });

    // Draw intensity indicator
    const intensityText = new PIXI.Text(
      `Intensity: ${(action.intensity * 100).toFixed(0)}%`,
      {
        fontFamily: 'Arial',
        fontSize: 14,
        fill: 0xffff00,
        stroke: 0x000000,
        strokeThickness: 3,
      }
    );
    intensityText.position.set(centerX - 50, centerY + radius + 40);
    this.container.addChild(intensityText);

    // Draw build indicator
    if (action.build) {
      const buildText = new PIXI.Text('🏗️ BUILD', {
        fontFamily: 'Arial',
        fontSize: 14,
        fill: 0xff0000,
        stroke: 0x000000,
        strokeThickness: 3,
      });
      buildText.position.set(centerX - 30, centerY + radius + 60);
      this.container.addChild(buildText);
    }
  }

  private renderValueEstimate() {
    if (!this.modelState) return;

    const value = this.modelState.value_estimate;
    const reward = this.modelState.reward;
    const cumReward = this.modelState.cumulative_reward;

    this.valueText.text = [
      `Value: ${value.toFixed(2)}`,
      `Reward: ${reward.toFixed(2)}`,
      `Cumulative: ${cumReward.toFixed(2)}`,
    ].join('\n');
  }

  private renderObservationHeatmap() {
    // TODO: Implement observation heatmap
    // This requires converting the observation array to a texture
    // and rendering it as a semi-transparent overlay
  }

  toggleOverlay(name: keyof OverlayConfig, enabled: boolean) {
    this.config[name] = enabled;
    this.render();
  }

  getContainer(): PIXI.Container {
    return this.container;
  }

  destroy() {
    this.container.destroy({ children: true });
  }
}
