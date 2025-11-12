"""
Custom callback for cleaner training progress reporting
"""
from stable_baselines3.common.callbacks import BaseCallback
import logging
import numpy as np

logger = logging.getLogger(__name__)


class CleanProgressCallback(BaseCallback):
    """
    Custom callback that provides clean, summary-based progress updates
    instead of verbose per-episode logging.
    """

    def __init__(self, report_freq: int = 5000, total_timesteps: int = 200000, verbose: int = 0):
        """
        Args:
            report_freq: Report progress every N timesteps
            total_timesteps: Total training timesteps for progress calculation
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.report_freq = report_freq
        self.total_timesteps = total_timesteps
        self.episode_count = 0
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_tiles = []  # Track final tiles owned
        self.episode_wins = 0
        self.last_report_step = 0
        self.last_eval_reward = None
        self.episodes_since_last_report = 0

    def _on_step(self) -> bool:
        """Called after each environment step"""
        # Check if episode finished
        dones = self.locals.get('dones', [False])
        if any(dones):
            # Get episode info from the infos buffer
            infos = self.locals.get('infos', [])
            for idx, info in enumerate(infos):
                if 'episode' in info:
                    self.episode_count += 1
                    episode_data = info['episode']
                    reward = episode_data['r']

                    # Debug: Check what's actually in the dicts
                    tiles_from_episode = episode_data.get('tiles_final', None)
                    tiles_from_info = info.get('tiles', 0)
                    enemy_tiles_from_info = info.get('enemy_tiles', 0)

                    # Use episode data if available, otherwise step info
                    tiles = tiles_from_episode if tiles_from_episode is not None else tiles_from_info
                    won = episode_data.get('won', False)

                    # Debug logging (first few episodes only)
                    if self.episode_count <= 3:
                        logger.info(f"DEBUG Episode {self.episode_count}: reward={reward:.0f}, tiles_episode={tiles_from_episode}, tiles_info={tiles_from_info}, enemy={enemy_tiles_from_info}")

                    # Log individual episode with step count
                    episode_length = episode_data.get('l', 0)
                    status = "WON" if won else "timeout"
                    logger.info(f"Episode {self.episode_count}: steps={episode_length:>5}, reward={reward:>10,.0f}, tiles={tiles:>3}, {status}")

                    # Track for summary
                    self.episode_rewards.append(reward)
                    self.episode_lengths.append(info['episode']['l'])
                    self.episode_tiles.append(tiles)
                    if won:
                        self.episode_wins += 1

        # Report progress at regular intervals
        if self.num_timesteps - self.last_report_step >= self.report_freq:
            self._report_progress()
            self.last_report_step = self.num_timesteps

        return True

    def _report_progress(self):
        """Print clean progress summary"""
        if len(self.episode_rewards) == 0:
            return

        # Calculate statistics since last report
        avg_reward = np.mean(self.episode_rewards)
        avg_tiles = np.mean(self.episode_tiles)
        avg_length = np.mean(self.episode_lengths)
        win_rate = (self.episode_wins / len(self.episode_rewards)) * 100

        # Calculate correct progress percentage
        progress_pct = (self.num_timesteps / self.total_timesteps) * 100

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"PROGRESS: {self.num_timesteps:,}/{self.total_timesteps:,} steps ({progress_pct:.1f}%) | "
                   f"{len(self.episode_rewards)} episodes | "
                   f"avg_steps={avg_length:.0f} | "
                   f"avg_reward={avg_reward:,.0f} | avg_tiles={avg_tiles:.0f} | wins={win_rate:.0f}%")
        logger.info("=" * 80)

        # Reset counters for next report period
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_tiles = []
        self.episode_wins = 0

    def _on_event(self, event: str) -> bool:
        """Called when specific events happen"""
        # Track evaluation results
        if hasattr(self, 'parent') and hasattr(self.parent, 'last_mean_reward'):
            self.last_eval_reward = self.parent.last_mean_reward
        return True


class EvalLogCallback(BaseCallback):
    """Callback to cleanly log evaluation results"""

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)

    def _on_step(self) -> bool:
        # This is called by EvalCallback after evaluation
        if 'eval_env' in self.locals:
            # Evaluation just completed
            pass
        return True


class CheckpointLogCallback(BaseCallback):
    """Callback to cleanly log checkpoint saves"""

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self.last_checkpoint = 0

    def _on_step(self) -> bool:
        # Log checkpoint saves every 10k steps
        if self.num_timesteps % 10000 == 0 and self.num_timesteps != self.last_checkpoint:
            logger.info(f"✓ Checkpoint saved: {self.num_timesteps:,} steps")
            self.last_checkpoint = self.num_timesteps
        return True
