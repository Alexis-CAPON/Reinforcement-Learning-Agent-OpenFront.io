/**
 * RL Training Configuration for Phase 3 - Battle Royale
 *
 * Extends DefaultConfig to allow configurable tick rate for faster training
 * with support for battle royale (50+ bots).
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
}

export default RLConfig;
