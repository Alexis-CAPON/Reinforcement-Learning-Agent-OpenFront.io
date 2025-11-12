"""
Action space flattening wrapper for Stable Baselines3 compatibility.

Converts Dict action space with discrete + continuous components
into a flat Box space that SB3 can handle natively.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Any


class FlattenActionWrapper(gym.Wrapper):
    """
    Flatten Dict action space into Box space for SB3 compatibility.

    Converts:
        Dict({
            'attack_target': Discrete(9),        # 0-8
            'attack_percentage': Box(0, 1, (1,)) # 0.0-1.0
        })

    Into:
        Box([-1, 0], [9, 1], (2,))  # [attack_target, attack_percentage]

    The discrete action (0-8) is represented as a continuous value
    and rounded to nearest integer during step().
    """

    def __init__(self, env):
        super().__init__(env)

        # Verify the original action space
        assert isinstance(env.action_space, spaces.Dict), \
            "FlattenActionWrapper requires Dict action space"

        original_dict = env.action_space

        # Extract bounds
        # attack_target: Discrete(9) → [0, 8] as continuous
        # attack_percentage: Box(0, 1) → [0.0, 1.0]
        n_discrete = original_dict['attack_target'].n

        # Flatten to Box space: [attack_target, attack_percentage]
        self.action_space = spaces.Box(
            low=np.array([0.0, 0.0], dtype=np.float32),
            high=np.array([float(n_discrete - 1), 1.0], dtype=np.float32),
            shape=(2,),
            dtype=np.float32
        )

        self.n_discrete = n_discrete

    def step(self, action):
        """
        Convert flat action back to dict for the environment.

        Args:
            action: np.ndarray([attack_target_continuous, attack_percentage])

        Returns:
            Standard gym step returns
        """
        # Extract components
        attack_target_continuous = action[0]
        attack_percentage = action[1]

        # Round discrete action to nearest integer and clip
        attack_target = int(np.clip(np.round(attack_target_continuous), 0, self.n_discrete - 1))

        # Clip percentage to valid range
        attack_percentage = np.clip(attack_percentage, 0.0, 1.0)

        # Convert to dict format expected by environment
        dict_action = {
            'attack_target': attack_target,
            'attack_percentage': np.array([attack_percentage], dtype=np.float32)
        }

        return self.env.step(dict_action)

    def reset(self, **kwargs):
        """Pass through reset"""
        return self.env.reset(**kwargs)
