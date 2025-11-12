"""
Compatibility wrappers for models trained with different observation spaces.

Phase 1 models:
  - features: [5] (tiles_owned, troops, gold, enemy_tiles, tick)
  - action_mask: [9]

Phase 2 models (early):
  - features: [5]
  - action_mask: [9]
  - neighbor_troops: [8]

Phase 2 models (v2 - strategic):
  - features: [10] (added 5 strategic features)
  - action_mask: [9]
  - neighbor_troops: [8]
  - player_info: [8, 3]

Phase 2 models (v3 - full):
  - features: [12] (added 2 temporal features)
  - action_mask: [9]
  - neighbor_info: [8, 2] (changed from neighbor_troops)
  - player_info: [8, 3]

This module provides wrappers to maintain backward compatibility.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np


class Phase1CompatWrapper(gym.Wrapper):
    """
    Phase 1 compatibility: Remove neighbor_troops and player_info.

    Converts Phase 2+ observation space back to Phase 1 format.
    Also truncates features from [10] to [5] if needed.
    """

    def __init__(self, env):
        super().__init__(env)

        # Create Phase 1 observation space (minimal)
        self.observation_space = spaces.Dict({
            'features': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(5,),
                dtype=np.float32
            ),
            'action_mask': env.observation_space['action_mask']
        })

    def reset(self, **kwargs):
        """Remove extra fields from observation"""
        obs, info = self.env.reset(**kwargs)
        return self._convert_obs(obs), info

    def step(self, action):
        """Remove extra fields from observation"""
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._convert_obs(obs), reward, terminated, truncated, info

    def _convert_obs(self, obs):
        """Convert Phase 2+ obs to Phase 1 format"""
        # Truncate features to first 5 if needed
        features = obs['features'][:5]

        return {
            'features': features,
            'action_mask': obs['action_mask']
            # neighbor_troops and player_info are dropped
        }


class Phase2EarlyCompatWrapper(gym.Wrapper):
    """
    Phase 2 (early) compatibility: Keep neighbor_troops[8], remove player_info and temporal.

    Converts Phase 2 v3 observation space back to Phase 2 early format.
    Truncates features from [12] to [5], neighbor_info[8,2] to neighbor_troops[8].
    """

    def __init__(self, env):
        super().__init__(env)

        # Create Phase 2 early observation space
        self.observation_space = spaces.Dict({
            'features': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(5,),
                dtype=np.float32
            ),
            'action_mask': env.observation_space['action_mask'],
            'neighbor_troops': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(8,),
                dtype=np.float32
            )
        })

    def reset(self, **kwargs):
        """Remove player_info and temporal features from observation"""
        obs, info = self.env.reset(**kwargs)
        return self._convert_obs(obs), info

    def step(self, action):
        """Remove player_info and temporal features from observation"""
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._convert_obs(obs), reward, terminated, truncated, info

    def _convert_obs(self, obs):
        """Convert Phase 2 v3 obs to Phase 2 early format"""
        # Truncate features to first 5 (remove strategic + temporal)
        features = obs['features'][:5]

        # Convert neighbor_info[8, 2] to neighbor_troops[8] (just first column)
        neighbor_troops = obs['neighbor_info'][:, 0] if 'neighbor_info' in obs else obs.get('neighbor_troops', np.zeros(8))

        return {
            'features': features,
            'action_mask': obs['action_mask'],
            'neighbor_troops': neighbor_troops
            # player_info is dropped
        }


class Phase2V2CompatWrapper(gym.Wrapper):
    """
    Phase 2 v2 compatibility: Keep strategic features, remove temporal.

    Converts Phase 2 v3 to v2 format (with neighbor_troops instead of neighbor_info).
    Truncates features from [12] to [10], neighbor_info[8,2] to neighbor_troops[8].
    """

    def __init__(self, env):
        super().__init__(env)

        # Create Phase 2 v2 observation space
        self.observation_space = spaces.Dict({
            'features': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(10,),
                dtype=np.float32
            ),
            'action_mask': env.observation_space['action_mask'],
            'neighbor_troops': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(8,),
                dtype=np.float32
            ),
            'player_info': env.observation_space['player_info']
        })

    def reset(self, **kwargs):
        """Remove temporal features from observation"""
        obs, info = self.env.reset(**kwargs)
        return self._convert_obs(obs), info

    def step(self, action):
        """Remove temporal features from observation"""
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._convert_obs(obs), reward, terminated, truncated, info

    def _convert_obs(self, obs):
        """Convert Phase 2 v3 obs to v2 format"""
        # Truncate features to first 10 (remove temporal)
        features = obs['features'][:10]

        # Convert neighbor_info[8, 2] to neighbor_troops[8]
        neighbor_troops = obs['neighbor_info'][:, 0] if 'neighbor_info' in obs else obs.get('neighbor_troops', np.zeros(8))

        return {
            'features': features,
            'action_mask': obs['action_mask'],
            'neighbor_troops': neighbor_troops,
            'player_info': obs['player_info']
        }
