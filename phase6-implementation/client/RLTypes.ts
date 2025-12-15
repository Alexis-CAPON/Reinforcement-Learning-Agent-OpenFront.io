/**
 * Type definitions for Phase 4 RL Visualizer
 */

export interface GameStateUpdate {
  type: 'game_state';
  tick: number;
  visual_state: VisualState;
}

export interface ModelStateUpdate {
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
  attention_weights?: number[][];
}

export interface ControlCommand {
  type: 'control';
  command: 'play' | 'pause' | 'step' | 'speed' | 'reset';
  speed?: number;
}

export interface VisualState {
  tick: number;
  map_width: number;
  map_height: number;
  tiles: TileState[];
  players: PlayerState[];
  rl_player: RLPlayerState;
  game_over: boolean;
  winner_id: number | null;
}

export interface TileState {
  x: number;
  y: number;
  owner_id: number;
  troops: number;
  is_city: boolean;
  is_mountain: boolean;
}

export interface PlayerState {
  id: number;
  name: string;
  is_alive: boolean;
  tiles_owned: number;
  total_troops: number;
  gold: number;
  color: string;
  rank: number;
}

export interface RLPlayerState {
  id: number;
  tiles_owned: number;
  troops: number;
  territory_pct: number;
  rank: number;
  is_alive: boolean;
  gold: number;
  num_cities: number;
}

export interface OverlayConfig {
  showObservation: boolean;
  showActionProbs: boolean;
  showValue: boolean;
  showAttention: boolean;
  showMetrics: boolean;
}

export type RLMessage = GameStateUpdate | ModelStateUpdate | ControlCommand;
