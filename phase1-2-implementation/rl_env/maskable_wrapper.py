"""
Wrapper to make OpenFrontIOEnv compatible with MaskablePPO.

MaskablePPO requires:
1. action_masks() method that returns the mask
2. Action mask NOT in the observation space
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Any


class MaskableActionWrapper(gym.Wrapper):
    """
    Wrapper that extracts action_mask from observations and provides it via action_masks() method.
    This makes the environment compatible with sb3-contrib's MaskablePPO.

    Changes:
    - Removes 'action_mask' from observation space
    - Stores the mask internally
    - Provides action_masks() method for MaskablePPO
    """

    def __init__(self, env):
        super().__init__(env)

        # Store the original observation space
        original_obs_space = env.observation_space

        # Create new observation space without action_mask
        new_spaces = {}
        for key, space in original_obs_space.spaces.items():
            if key != 'action_mask':
                new_spaces[key] = space

        self.observation_space = spaces.Dict(new_spaces)

        # Store current action mask
        self.current_mask = None

    def reset(self, **kwargs):
        """Reset environment and extract action mask"""
        obs, info = self.env.reset(**kwargs)

        # Extract and store action mask
        self.current_mask = obs.pop('action_mask')

        return obs, info

    def step(self, action):
        """Step environment and extract action mask"""
        obs, reward, terminated, truncated, info = self.env.step(action)

        # Extract and store action mask
        self.current_mask = obs.pop('action_mask')

        return obs, reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        """
        Return the current action mask.
        Required by MaskablePPO.

        Returns:
            np.ndarray: Boolean mask where True = valid action
        """
        if self.current_mask is None:
            # Fallback: allow all actions
            return np.ones(self.env.action_space['attack_target'].n, dtype=np.bool_)

        return self.current_mask.astype(np.bool_)
