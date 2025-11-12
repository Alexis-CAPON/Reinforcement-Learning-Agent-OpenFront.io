"""
OpenFront.io Phase 5 Environment - Clean Implementation

Features:
- Clean implementation with working attack execution
- Support for any map size (automatically detected)
- Configurable number of bots
- Frame stacking for temporal context
- Compatible with Phase 3 models (same observation space)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
import os
import sys
from collections import deque

logger = logging.getLogger(__name__)


class OpenFrontEnv(gym.Env):
    """
    Phase 5 OpenFront.io Environment.

    Observation Space:
        Dict with:
        - 'map': Box(128, 128, 5*frame_stack) - Spatial features
        - 'global': Box(16*frame_stack,) - Global state features

    Action Space:
        Discrete(45) - 9 directions × 5 intensities
    """

    metadata = {'render_modes': []}

    def __init__(
        self,
        game_interface=None,
        num_bots: int = 10,
        map_name: str = 'plains',
        frame_stack: int = 4
    ):
        """
        Initialize environment.

        Args:
            game_interface: Game wrapper/bridge interface
            num_bots: Number of bot opponents (1-50)
            map_name: Name of map to use
            frame_stack: Number of frames to stack for temporal context
        """
        super().__init__()

        # Create game wrapper if not provided
        if game_interface is None:
            try:
                from game_wrapper import GameWrapper
                self.game = GameWrapper(
                    map_name=map_name,
                    num_players=num_bots + 1  # +1 for RL agent
                )
                logger.info(f"Created GameWrapper: map={map_name}, bots={num_bots}")
            except ImportError as e:
                logger.warning(f"Could not import GameWrapper: {e}")
                logger.warning("Environment will run in stub mode")
                self.game = None
        else:
            self.game = game_interface

        self.num_bots = num_bots
        self.map_name = map_name
        self.frame_stack = frame_stack

        # Frame stacking for temporal context
        self.frame_buffer = deque(maxlen=frame_stack)

        # Observation space (compatible with Phase 3)
        # Map: 128×128×(5*frame_stack) channels
        # Global: (16*frame_stack) features
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 5 * frame_stack), dtype=np.float32),
            'global': spaces.Box(-np.inf, np.inf, (16 * frame_stack,), dtype=np.float32)
        })

        # Action space: 9 directions × 5 intensities = 45
        self.action_space = spaces.Discrete(45)

        # Action components
        self.directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]

        # State tracking
        self.previous_state = None
        self.step_count = 0
        self.episode_count = 0
        self.recent_attack_directions = []

        logger.info(f"Environment initialized: map={map_name}, bots={num_bots}, frame_stack={frame_stack}")

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset environment for new episode.

        Returns:
            observation: Dict with 'map' and 'global' arrays (frame-stacked)
            info: Additional information dict
        """
        super().reset(seed=seed)

        if self.game is not None:
            self.game.start_new_game(num_bots=self.num_bots)

        self.previous_state = None
        self.step_count = 0
        self.episode_count += 1
        self.recent_attack_directions = []

        # Get initial observation
        obs = self._get_obs()

        # Fill frame buffer with initial observation
        self.frame_buffer.clear()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(obs)

        info = {
            'map_name': self.map_name,
            'num_bots': self.num_bots
        }

        logger.info(f"Episode {self.episode_count} started")

        return self._stack_frames(), info

    def step(
        self,
        action: int
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one environment step.

        Args:
            action: Flattened action index (0-44)

        Returns:
            observation, reward, terminated, truncated, info
        """
        # Decode action (9 directions × 5 intensities = 45 actions)
        direction = action // 5
        intensity_idx = action % 5

        # Track attack directions
        if direction < 8:  # Not waiting
            self.recent_attack_directions.append(direction)
            if len(self.recent_attack_directions) > 10:
                self.recent_attack_directions.pop(0)

        # Execute action
        self._execute_action(direction, intensity_idx)

        # Update game state
        if self.game is not None:
            self.game.update()

        # Get results
        obs = self._get_obs()
        reward = self._compute_reward()
        terminated = self._check_done()

        # Add observation to frame buffer
        self.frame_buffer.append(obs)

        self.step_count += 1
        self.previous_state = self._get_game_state()

        # Get current state for info
        current_state = self._get_game_state()

        info = {
            'step': self.step_count,
            'direction': self.directions[direction],
            'intensity': self.intensities[intensity_idx],
            'tiles': getattr(current_state, 'tiles_owned', 0) if current_state else 0,
            'troops': getattr(current_state, 'population', 0) if current_state else 0,
            'territory_pct': getattr(current_state, 'territory_pct', 0) if current_state else 0,
            'rank': getattr(current_state, 'rank', 0) if current_state else 0,
        }

        # Add episode summary if terminated
        if terminated:
            info['episode'] = {
                'r': reward,
                'l': self.step_count,
                'tiles': getattr(current_state, 'tiles_owned', 0) if current_state else 0,
                'troops': getattr(current_state, 'population', 0) if current_state else 0,
                'territory_pct': getattr(current_state, 'territory_pct', 0) if current_state else 0,
                'rank': getattr(current_state, 'rank', 0) if current_state else 0,
                'won': (getattr(current_state, 'territory_pct', 0) >= 0.80) if current_state else False,
            }

            result = "🏆 VICTORY" if info['episode']['won'] else "💀 ELIMINATED"
            logger.info(
                f"Episode {self.episode_count} ended: {result}\n"
                f"  Steps: {self.step_count}\n"
                f"  Territory: {info['episode']['territory_pct']*100:.1f}%\n"
                f"  Rank: {info['episode']['rank']}/{self.num_bots+1}"
            )

        return self._stack_frames(), reward, terminated, False, info

    def _stack_frames(self) -> Dict[str, np.ndarray]:
        """Stack frames from buffer for temporal context."""
        stacked_map = np.concatenate(
            [frame['map'] for frame in self.frame_buffer],
            axis=2
        )
        stacked_global = np.concatenate(
            [frame['global'] for frame in self.frame_buffer]
        )
        return {
            'map': stacked_map,
            'global': stacked_global
        }

    def _get_obs(self) -> Dict[str, np.ndarray]:
        """Get current observation (single frame)."""
        if self.game is None:
            return {
                'map': np.zeros((128, 128, 5), dtype=np.float32),
                'global': np.zeros(16, dtype=np.float32)
            }

        state = self._get_game_state()

        return {
            'map': self._extract_map(state),
            'global': self._extract_global(state)
        }

    def _get_game_state(self):
        """Get raw game state from game interface"""
        if self.game is None:
            return None
        try:
            return self.game.get_state()
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return None

    def _extract_map(self, state) -> np.ndarray:
        """
        Extract 128×128×5 map features with adaptive downsampling.

        Channels:
        0: Your territory (binary)
        1: Enemy density (aggregated, normalized)
        2: Neutral territory (binary)
        3: Your troop density (normalized)
        4: Enemy troop density (aggregated, normalized)
        """
        if state is None:
            return np.zeros((128, 128, 5), dtype=np.float32)

        map_feat = np.zeros((128, 128, 5), dtype=np.float32)

        # Channel 0: Your territory
        if hasattr(state, 'your_territory_mask') and state.your_territory_mask.size > 0:
            map_feat[:, :, 0] = self._adaptive_downsample(state.your_territory_mask)

        # Channel 1: Enemy density
        if hasattr(state, 'enemy_count_map') and state.enemy_count_map.size > 0:
            max_enemies = max(self.num_bots, 1)
            map_feat[:, :, 1] = self._adaptive_downsample(state.enemy_count_map / max_enemies)

        # Channel 2: Neutral territory
        if hasattr(state, 'neutral_mask') and state.neutral_mask.size > 0:
            map_feat[:, :, 2] = self._adaptive_downsample(state.neutral_mask)

        # Channel 3: Your troops
        if hasattr(state, 'your_troops') and state.your_troops.size > 0:
            map_feat[:, :, 3] = self._adaptive_downsample(state.your_troops / 10000.0)

        # Channel 4: Enemy troops
        if hasattr(state, 'enemy_troops') and state.enemy_troops.size > 0:
            map_feat[:, :, 4] = self._adaptive_downsample(state.enemy_troops / 10000.0)

        return map_feat

    def _adaptive_downsample(self, array: np.ndarray) -> np.ndarray:
        """
        Adaptively downsample array to 128×128 based on input size.
        """
        h, w = array.shape[:2]

        # Already correct size
        if h == 128 and w == 128:
            return array

        # Need to upsample (smaller than 128)
        if h < 128 or w < 128:
            result = np.zeros((128, 128), dtype=array.dtype)
            result[:min(h, 128), :min(w, 128)] = array[:min(h, 128), :min(w, 128)]
            return result

        # Need to downsample (larger than 128)
        scale = max(h / 128, w / 128)

        if scale <= 2:
            # 2×2 average pooling
            h_out, w_out = h // 2, w // 2
            return array.reshape(h_out, 2, w_out, 2).mean(axis=(1, 3))[:128, :128]
        elif scale <= 4:
            # 4×4 average pooling
            h_out, w_out = h // 4, w // 4
            return array.reshape(h_out, 4, w_out, 4).mean(axis=(1, 3))[:128, :128]
        elif scale <= 8:
            # 8×8 average pooling
            h_out, w_out = h // 8, w // 8
            return array.reshape(h_out, 8, w_out, 8).mean(axis=(1, 3))[:128, :128]
        else:
            # Very large map - use simple strided slicing
            stride = int(scale)
            return array[::stride, ::stride][:128, :128]

    def _extract_global(self, state) -> np.ndarray:
        """
        Extract 16 global features.

        Features:
        0: Population / max_population
        1: Max population / 100000
        2: Population growth rate
        3: Territory percentage
        4: Territory change
        5: Rank / 50
        6: Border pressure / 10
        7: Troops per tile ratio
        8: Territory momentum
        9: Time alive / max_time
        10: Game progress
        11: Nearest threat / 128
        12: Recent attack intensity
        13: Multi-front indicator
        14: Rank position (percentile)
        15: Overextension flag
        """
        if state is None:
            return np.zeros(16, dtype=np.float32)

        features = np.zeros(16, dtype=np.float32)

        # Population metrics
        if hasattr(state, 'population') and hasattr(state, 'max_population'):
            features[0] = state.population / max(state.max_population, 1)
            features[1] = state.max_population / 100000.0

        if hasattr(state, 'population_growth_rate'):
            features[2] = state.population_growth_rate

        # Territory metrics
        if hasattr(state, 'territory_pct'):
            features[3] = state.territory_pct

        if hasattr(state, 'territory_change'):
            features[4] = state.territory_change

        # Position
        if hasattr(state, 'rank'):
            features[5] = state.rank / 50.0

        if hasattr(state, 'border_pressure'):
            features[6] = state.border_pressure / 10.0

        # Troops per tile ratio
        if hasattr(state, 'population') and hasattr(state, 'tiles_owned') and state.tiles_owned > 0:
            troops_per_tile = state.population / state.tiles_owned
            features[7] = troops_per_tile / 50.0

        # Territory momentum
        if hasattr(self, 'previous_state') and self.previous_state is not None:
            if hasattr(state, 'territory_pct') and hasattr(self.previous_state, 'territory_pct'):
                territory_momentum = state.territory_pct - self.previous_state.territory_pct
                features[8] = territory_momentum * 100

        # Survival
        if hasattr(state, 'time_alive'):
            features[9] = state.time_alive / 10000.0

        # Game phase
        if hasattr(state, 'time_alive'):
            features[10] = min(state.time_alive / 10000.0, 1.0)

        # Threats
        if hasattr(state, 'nearest_threat_distance'):
            features[11] = state.nearest_threat_distance / 128.0

        # Attack intensity
        if len(self.recent_attack_directions) > 0:
            features[12] = len(self.recent_attack_directions) / 10.0

        # Multi-front indicator
        if len(self.recent_attack_directions) >= 5:
            unique_fronts = len(set(self.recent_attack_directions[-5:]))
            features[13] = unique_fronts / 8.0

        # Rank position
        if hasattr(state, 'rank') and hasattr(state, 'total_players'):
            rank_percentile = state.rank / max(state.total_players, 1)
            features[14] = 1.0 - rank_percentile

        # Overextension indicator
        if hasattr(state, 'population') and hasattr(state, 'tiles_owned') and state.tiles_owned > 0:
            troops_per_tile = state.population / state.tiles_owned
            if hasattr(state, 'territory_pct') and state.territory_pct > 0.20:
                if troops_per_tile < 15:
                    features[15] = (15 - troops_per_tile) / 15.0
                else:
                    features[15] = 0.0
            else:
                features[15] = 0.0

        return features

    def _execute_action(self, direction: int, intensity_idx: int):
        """Execute action in game."""
        if self.game is None:
            return

        intensity = self.intensities[intensity_idx]

        # Attack with direction and intensity
        # The game bridge will handle finding valid targets
        if self.game is not None:
            self.game.attack(direction=direction, troops_pct=intensity)

    def _compute_reward(self) -> float:
        """
        Compute reward using logarithmic survival + rank strategy.

        Rewards increase exponentially with survival time to encourage
        reaching late game.
        """
        if self.game is None:
            return 0.1

        state = self._get_game_state()
        reward = 0.0

        # Logarithmic survival reward (every step)
        if hasattr(state, 'rank') and hasattr(state, 'total_players'):
            if state.total_players > 0:
                rank_percentile = 1.0 - (state.rank / state.total_players)

                # Logarithmic multiplier (increases with survival time)
                if self.step_count < 1000:
                    multiplier = 1.0
                elif self.step_count < 2500:
                    multiplier = 2.0
                elif self.step_count < 5000:
                    multiplier = 4.0
                else:
                    multiplier = 8.0

                rank_reward = rank_percentile * multiplier
                reward += rank_reward

        # Terminal rewards
        if hasattr(state, 'territory_pct'):
            if state.territory_pct >= 0.80:
                reward += 10000  # Victory bonus

        # Timeout penalty
        if self.step_count >= 10000:
            reward += -5000

        return reward

    def _check_done(self) -> bool:
        """Check if episode should terminate."""
        if self.game is None:
            return False

        state = self._get_game_state()
        if state is None:
            return False

        # Win condition
        if hasattr(state, 'territory_pct') and state.territory_pct >= 0.80:
            return True

        # Loss condition
        if hasattr(state, 'territory_pct') and state.territory_pct == 0.0:
            return True

        # Max steps
        if self.step_count >= 10000:
            return True

        return False

    def close(self):
        """Clean up environment resources"""
        if self.game is not None and hasattr(self.game, 'close'):
            try:
                self.game.close()
            except Exception as e:
                logger.warning(f"Error closing game: {e}")
        logger.info("Environment closed")
