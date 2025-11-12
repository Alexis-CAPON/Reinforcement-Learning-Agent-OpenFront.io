"""
Training Callback - Enhanced logging for Phase 3
"""
import logging
from typing import Dict, Any
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)


class DetailedLoggingCallback(BaseCallback):
    """
    Custom callback for detailed episode logging during training.

    Logs detailed statistics at the end of each episode:
    - Episode length and reward
    - Final tiles, troops, territory %
    - Final rank
    - Win/loss outcome
    """

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_tiles = []
        self.episode_troops = []
        self.episode_ranks = []
        self.episode_territory = []
        self.wins = 0
        self.losses = 0
        self.episodes_completed = 0

    def _on_step(self) -> bool:
        """
        Called after each environment step.
        Check for episode end and log statistics.
        """
        # Check if any environment finished an episode
        for idx, done in enumerate(self.locals['dones']):
            if done:
                # Get info from the environment that just finished
                info = self.locals['infos'][idx]

                # Check if episode info is available
                if 'episode' in info:
                    ep_info = info['episode']

                    # Track statistics
                    self.episode_rewards.append(ep_info.get('r', 0))
                    self.episode_lengths.append(ep_info.get('l', 0))
                    self.episode_tiles.append(ep_info.get('tiles', 0))
                    self.episode_troops.append(ep_info.get('troops', 0))
                    self.episode_ranks.append(ep_info.get('rank', 0))
                    self.episode_territory.append(ep_info.get('territory_pct', 0))

                    if ep_info.get('won', False):
                        self.wins += 1
                    else:
                        self.losses += 1

                    self.episodes_completed += 1

                    # Log every episode with details
                    result = "🏆 WIN" if ep_info.get('won', False) else "💀 LOSS"
                    logger.info(
                        f"[Env {idx}] Episode {self.episodes_completed} complete: {result} | "
                        f"Steps: {ep_info.get('l', 0)} | "
                        f"Reward: {ep_info.get('r', 0):.1f} | "
                        f"Tiles: {ep_info.get('tiles', 0)} | "
                        f"Troops: {ep_info.get('troops', 0)} | "
                        f"Territory: {ep_info.get('territory_pct', 0)*100:.1f}% | "
                        f"Rank: {ep_info.get('rank', 0)}"
                    )

                    # Log aggregate stats every 10 episodes
                    if self.episodes_completed % 10 == 0:
                        self._log_aggregates()

        return True

    def _log_aggregates(self):
        """Log aggregate statistics over recent episodes"""
        if len(self.episode_rewards) == 0:
            return

        # Last 10 episodes stats
        n = min(10, len(self.episode_rewards))
        recent_rewards = self.episode_rewards[-n:]
        recent_lengths = self.episode_lengths[-n:]
        recent_tiles = self.episode_tiles[-n:]
        recent_troops = self.episode_troops[-n:]
        recent_ranks = self.episode_ranks[-n:]
        recent_territory = self.episode_territory[-n:]

        logger.info("=" * 80)
        logger.info(f"TRAINING SUMMARY (Last {n} episodes)")
        logger.info("=" * 80)
        logger.info(f"Total Episodes: {self.episodes_completed}")
        logger.info(f"Win Rate: {self.wins}/{self.episodes_completed} ({100*self.wins/max(self.episodes_completed,1):.1f}%)")
        logger.info(f"")
        logger.info(f"Recent Performance:")
        logger.info(f"  Avg Reward:     {np.mean(recent_rewards):+.1f}")
        logger.info(f"  Avg Length:     {np.mean(recent_lengths):.0f} steps")
        logger.info(f"  Avg Tiles:      {np.mean(recent_tiles):.0f}")
        logger.info(f"  Avg Troops:     {np.mean(recent_troops):.0f}")
        logger.info(f"  Avg Territory:  {np.mean(recent_territory)*100:.1f}%")
        logger.info(f"  Avg Rank:       {np.mean(recent_ranks):.1f}")
        logger.info(f"  Best Tile:      {max(recent_tiles)}")
        logger.info(f"  Best Territory: {max(recent_territory)*100:.1f}%")
        logger.info(f"  Best Rank:      {min(recent_ranks)}")
        logger.info("=" * 80)

    def _on_training_end(self) -> None:
        """Called at the end of training"""
        if self.episodes_completed > 0:
            logger.info("\n" + "=" * 80)
            logger.info("TRAINING COMPLETE - FINAL STATISTICS")
            logger.info("=" * 80)
            logger.info(f"Total Episodes: {self.episodes_completed}")
            logger.info(f"Total Wins: {self.wins}")
            logger.info(f"Total Losses: {self.losses}")
            logger.info(f"Win Rate: {100*self.wins/max(self.episodes_completed,1):.1f}%")
            logger.info(f"")
            logger.info(f"Overall Averages:")
            logger.info(f"  Avg Reward:     {np.mean(self.episode_rewards):+.1f}")
            logger.info(f"  Avg Length:     {np.mean(self.episode_lengths):.0f} steps")
            logger.info(f"  Avg Tiles:      {np.mean(self.episode_tiles):.0f}")
            logger.info(f"  Avg Troops:     {np.mean(self.episode_troops):.0f}")
            logger.info(f"  Avg Territory:  {np.mean(self.episode_territory)*100:.1f}%")
            logger.info(f"  Avg Rank:       {np.mean(self.episode_ranks):.1f}")
            logger.info(f"")
            logger.info(f"Best Performance:")
            logger.info(f"  Best Reward:    {max(self.episode_rewards):+.1f}")
            logger.info(f"  Longest Run:    {max(self.episode_lengths)} steps")
            logger.info(f"  Most Tiles:     {max(self.episode_tiles)}")
            logger.info(f"  Most Territory: {max(self.episode_territory)*100:.1f}%")
            logger.info(f"  Best Rank:      {min(self.episode_ranks)}")
            logger.info("=" * 80 + "\n")
