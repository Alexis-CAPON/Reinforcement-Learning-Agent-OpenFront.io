/**
 * RL Training Configuration
 *
 * Extends DefaultConfig to allow configurable tick rate for faster training.
 * All per-tick values are automatically scaled based on tick interval.
 */

import { DefaultConfig } from '../../base-game/src/core/configuration/DefaultConfig';
import { GameEnv, ServerConfig } from '../../base-game/src/core/configuration/Config';
import { GameConfig } from '../../base-game/src/core/Schemas';
import { UserSettings } from '../../base-game/src/core/game/UserSettings';

export class RLConfig extends DefaultConfig {
  private tickIntervalMs_: number;
  private speedupFactor: number;

  constructor(
    serverConfig: ServerConfig,
    gameConfig: GameConfig,
    tickIntervalMs: number = 100
  ) {
    super(serverConfig, gameConfig, new UserSettings(), false);
    this.tickIntervalMs_ = tickIntervalMs;

    // Calculate speedup factor relative to baseline 100ms
    this.speedupFactor = 100 / tickIntervalMs;

    console.error(`[RLConfig] Tick interval: ${tickIntervalMs}ms (${this.speedupFactor}× speedup)`);
  }

  // Override turn interval
  turnIntervalMs(): number {
    return this.tickIntervalMs_;
  }

  // Environment (required abstract method)
  env(): GameEnv {
    return GameEnv.Dev;
  }

  // Number of workers (required abstract method)
  numWorkers(): number {
    return 1;
  }

  // Note: Per-tick values are defined in the base DefaultConfig
  // The game engine reads these values and they apply per tick
  // So when ticks are faster, everything happens faster proportionally
  // This is exactly what we want for RL training!

  // No need to override per-tick values because:
  // - 100ms tick: 100 gold/tick = 1000 gold/second
  // - 10ms tick: 100 gold/tick = 10,000 gold/second
  // But game duration ratios stay the same:
  // - Attack taking 50 ticks = 5s at 100ms, 0.5s at 10ms
  // - Gameplay feels the same, just faster simulation ✓
}

export default RLConfig;
