"""
Callback to save the best model based on maximum episode length (survival time).
"""

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback
import logging

logger = logging.getLogger(__name__)


class SaveBestModelCallback(BaseCallback):
    """
    Callback to save the best model based on MAXIMUM episode length (survival time).

    Tracks the longest episode (most steps survived) seen so far and saves
    the model whenever a new best is achieved.

    This captures breakthrough policies that achieve exceptional survival,
    which is the primary objective in battle royale games.
    """

    def __init__(self, save_path: str, verbose: int = 1):
        """
        Args:
            save_path: Path to save the best model
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.save_path = save_path
        self.best_episode_length = 0  # Track MAXIMUM episode length
        self.best_episode_reward = -np.inf
        self.episode_count = 0

    def _init_callback(self) -> None:
        # Create save directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        logger.info(f"SaveBestModelCallback initialized (MAX episode length)")
        logger.info(f"Will save to: {self.save_path}")

    def _on_step(self) -> bool:
        # Check if any episodes finished in the vectorized environments
        if len(self.locals.get('infos', [])) > 0:
            for info in self.locals['infos']:
                if 'episode' in info:
                    # Episode finished
                    episode_length = info['episode']['l']
                    episode_reward = info['episode']['r']
                    self.episode_count += 1

                    # Save if this is a new MAXIMUM length (longest survival)
                    if episode_length > self.best_episode_length:
                        self.best_episode_length = episode_length
                        self.best_episode_reward = episode_reward

                        # Save the model
                        self.model.save(self.save_path)

                        if self.verbose > 0:
                            logger.info(f"🏆 NEW BEST MODEL! Episode length: {episode_length} steps")
                            logger.info(f"   Episode reward: {episode_reward:.2f}")
                            logger.info(f"   Saved to: {self.save_path}")
                            logger.info(f"   Total episodes: {self.episode_count}")

        return True
