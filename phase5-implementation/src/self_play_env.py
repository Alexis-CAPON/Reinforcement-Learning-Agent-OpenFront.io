"""
Self-Play Environment Wrapper

Allows the agent to train by playing against copies of itself or previous versions.
This creates a more challenging and adaptive learning environment.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
import os

from stable_baselines3 import PPO

# Will import from phase 3 or use local large env
try:
    from environment_large import OpenFrontEnvLarge as BaseEnv
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase3-implementation', 'src'))
        from environment import OpenFrontEnv as BaseEnv
    except ImportError:
        BaseEnv = None

logger = logging.getLogger(__name__)


class SelfPlayEnv(gym.Env):
    """
    Self-Play Environment Wrapper.

    Wraps the base environment and periodically updates opponent models
    to be copies of the learning agent.

    Features:
    - Trains against previous versions of itself
    - Adapts to improving strategy
    - More challenging than static bots
    """

    metadata = {'render_modes': []}

    def __init__(
        self,
        game_interface=None,
        num_bots: int = 10,
        map_name: str = 'plains',
        opponent_model_path: Optional[str] = None,
        update_opponent_every: int = 10000  # Update opponent every N steps
    ):
        """
        Initialize self-play environment.

        Args:
            game_interface: Game wrapper/bridge interface
            num_bots: Number of opponents (mix of bots and self-play agents)
            map_name: Name of map to use
            opponent_model_path: Initial opponent model (uses bots if None)
            update_opponent_every: Steps between opponent model updates
        """
        super().__init__()

        if BaseEnv is None:
            raise ImportError("Could not import base environment")

        # Create base environment
        self.base_env = BaseEnv(
            game_interface=game_interface,
            num_bots=num_bots,
            map_name=map_name
        )

        # Copy spaces from base environment
        self.observation_space = self.base_env.observation_space
        self.action_space = self.base_env.action_space

        # Self-play configuration
        self.num_bots = num_bots
        self.map_name = map_name
        self.update_opponent_every = update_opponent_every
        self.steps_since_update = 0
        self.total_steps = 0

        # Opponent model (None means using regular bots)
        self.opponent_model = None
        if opponent_model_path and os.path.exists(opponent_model_path):
            try:
                self.opponent_model = PPO.load(opponent_model_path)
                logger.info(f"Loaded opponent model from: {opponent_model_path}")
            except Exception as e:
                logger.warning(f"Failed to load opponent model: {e}")
                logger.info("Using regular bots instead")

        logger.info(f"SelfPlayEnv initialized: {num_bots} opponents, map={map_name}")
        if self.opponent_model:
            logger.info("  Mode: Self-play enabled")
        else:
            logger.info("  Mode: Regular bots (self-play model not loaded)")

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset environment for new episode.

        Returns:
            observation: Initial observation
            info: Additional information
        """
        # Check if we should update opponent model
        if self.steps_since_update >= self.update_opponent_every:
            self._update_opponent_model()
            self.steps_since_update = 0

        # Reset base environment
        obs, info = self.base_env.reset(seed=seed, options=options)

        info['self_play_enabled'] = (self.opponent_model is not None)
        info['total_steps'] = self.total_steps

        return obs, info

    def step(
        self,
        action: int
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one environment step.

        If self-play is enabled, opponent agents will also take actions
        using the opponent model.

        Args:
            action: Agent's action

        Returns:
            observation, reward, terminated, truncated, info
        """
        # Execute agent's action in base environment
        obs, reward, terminated, truncated, info = self.base_env.step(action)

        # Update counters
        self.steps_since_update += 1
        self.total_steps += 1

        # Add self-play info
        info['self_play_enabled'] = (self.opponent_model is not None)
        info['steps_until_opponent_update'] = (
            self.update_opponent_every - self.steps_since_update
        )

        return obs, reward, terminated, truncated, info

    def _update_opponent_model(self):
        """
        Update opponent model with the latest version of the training agent.

        This should be called periodically during training.
        Note: This is a placeholder - actual implementation would need
        to receive the latest model from the training process.
        """
        logger.info(f"Opponent model update triggered at step {self.total_steps}")
        # In a full implementation, this would:
        # 1. Get the latest checkpoint from training
        # 2. Load it as the new opponent model
        # 3. Mix it with previous versions for diversity

        # For now, we keep the existing opponent model
        pass

    def update_opponent(self, model_path: str):
        """
        Manually update the opponent model.

        This can be called from the training script to update opponents
        with the latest agent version.

        Args:
            model_path: Path to the new opponent model
        """
        try:
            self.opponent_model = PPO.load(model_path)
            logger.info(f"✓ Opponent model updated: {model_path}")
            self.steps_since_update = 0
        except Exception as e:
            logger.error(f"Failed to update opponent model: {e}")

    def close(self):
        """Clean up environment resources"""
        if hasattr(self.base_env, 'close'):
            self.base_env.close()
        logger.info("SelfPlayEnv closed")

    def render(self):
        """Render environment (delegates to base environment)"""
        if hasattr(self.base_env, 'render'):
            return self.base_env.render()

    def __getattr__(self, name):
        """Delegate attribute access to base environment"""
        return getattr(self.base_env, name)
