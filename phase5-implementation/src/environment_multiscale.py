"""
OpenFront.io Phase 5 Environment - Multi-Scale Observations

Designed for large maps (1024×1024+) where single-scale downsampling loses too much information.

Observation scales:
- Global (128×128): Entire map overview (strategic)
- Local (128×128): Region around player (tactical awareness)
- Tactical (64×64): Immediate borders (precise control)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
from collections import deque

logger = logging.getLogger(__name__)


class OpenFrontEnvMultiScale(gym.Env):
    """
    Multi-scale observation environment for large maps.

    Observation Space:
        Dict with:
        - 'global_map': Box(128, 128, 5*frame_stack) - Full map downsampled
        - 'local_map': Box(128, 128, 5*frame_stack) - Your region
        - 'tactical_map': Box(64, 64, 5*frame_stack) - Border region
        - 'global': Box(16*frame_stack,) - Global features

    Action Space:
        Discrete(45) - 9 directions × 5 intensities
    """

    metadata = {'render_modes': []}

    def __init__(
        self,
        game_interface=None,
        num_bots: int = 10,
        map_name: str = 'plains',
        frame_stack: int = 4,
        local_view_size: int = 256,  # Size of local view in actual tiles
    ):
        """
        Initialize multi-scale environment.

        Args:
            game_interface: Game wrapper/bridge interface
            num_bots: Number of bot opponents
            map_name: Name of map to use
            frame_stack: Number of frames to stack
            local_view_size: Size of local view region in tiles (default: 256)
        """
        super().__init__()

        # Create game wrapper
        if game_interface is None:
            try:
                from game_wrapper import GameWrapper
                self.game = GameWrapper(
                    map_name=map_name,
                    num_players=num_bots + 1
                )
                logger.info(f"Created GameWrapper: map={map_name}, bots={num_bots}")
            except ImportError as e:
                logger.warning(f"Could not import GameWrapper: {e}")
                self.game = None
        else:
            self.game = game_interface

        self.num_bots = num_bots
        self.map_name = map_name
        self.frame_stack = frame_stack
        self.local_view_size = local_view_size

        # Frame buffers for each scale
        self.global_buffer = deque(maxlen=frame_stack)
        self.local_buffer = deque(maxlen=frame_stack)
        self.tactical_buffer = deque(maxlen=frame_stack)
        self.feature_buffer = deque(maxlen=frame_stack)

        # Multi-scale observation space
        self.observation_space = spaces.Dict({
            'global_map': spaces.Box(0, 1, (128, 128, 5 * frame_stack), dtype=np.float32),
            'local_map': spaces.Box(0, 1, (128, 128, 5 * frame_stack), dtype=np.float32),
            'tactical_map': spaces.Box(0, 1, (64, 64, 5 * frame_stack), dtype=np.float32),
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

        logger.info(f"Multi-scale environment initialized:")
        logger.info(f"  Map: {map_name}")
        logger.info(f"  Bots: {num_bots}")
        logger.info(f"  Local view: {local_view_size}×{local_view_size}")
        logger.info(f"  Frame stack: {frame_stack}")

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """Reset environment for new episode."""
        super().reset(seed=seed)

        if self.game is not None:
            self.game.start_new_game(num_bots=self.num_bots)

        self.previous_state = None
        self.step_count = 0
        self.episode_count += 1
        self.recent_attack_directions = []

        # Get initial observation
        obs = self._get_obs()

        # Fill all buffers with initial observation
        self.global_buffer.clear()
        self.local_buffer.clear()
        self.tactical_buffer.clear()
        self.feature_buffer.clear()

        for _ in range(self.frame_stack):
            self.global_buffer.append(obs['global_map'])
            self.local_buffer.append(obs['local_map'])
            self.tactical_buffer.append(obs['tactical_map'])
            self.feature_buffer.append(obs['global'])

        info = {
            'map_name': self.map_name,
            'num_bots': self.num_bots
        }

        logger.info(f"Episode {self.episode_count} started")

        return self._stack_observations(), info

    def step(
        self,
        action: int
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """Execute one environment step."""
        # Decode action
        direction = action // 5
        intensity_idx = action % 5

        # Track attacks
        if direction < 8:
            self.recent_attack_directions.append(direction)
            if len(self.recent_attack_directions) > 10:
                self.recent_attack_directions.pop(0)

        # Execute action
        self._execute_action(direction, intensity_idx)

        # Update game
        if self.game is not None:
            self.game.update()

        # Get observation
        obs = self._get_obs()
        reward = self._compute_reward()
        terminated = self._check_done()

        # Add to buffers
        self.global_buffer.append(obs['global_map'])
        self.local_buffer.append(obs['local_map'])
        self.tactical_buffer.append(obs['tactical_map'])
        self.feature_buffer.append(obs['global'])

        self.step_count += 1
        self.previous_state = self._get_game_state()

        # Build info
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

        if terminated:
            info['episode'] = {
                'r': reward,
                'l': self.step_count,
                'tiles': getattr(current_state, 'tiles_owned', 0) if current_state else 0,
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

        return self._stack_observations(), reward, terminated, False, info

    def _stack_observations(self) -> Dict[str, np.ndarray]:
        """Stack all multi-scale observations."""
        return {
            'global_map': np.concatenate(list(self.global_buffer), axis=2),
            'local_map': np.concatenate(list(self.local_buffer), axis=2),
            'tactical_map': np.concatenate(list(self.tactical_buffer), axis=2),
            'global': np.concatenate(list(self.feature_buffer))
        }

    def _get_obs(self) -> Dict[str, np.ndarray]:
        """Get multi-scale observation."""
        if self.game is None:
            return {
                'global_map': np.zeros((128, 128, 5), dtype=np.float32),
                'local_map': np.zeros((128, 128, 5), dtype=np.float32),
                'tactical_map': np.zeros((64, 64, 5), dtype=np.float32),
                'global': np.zeros(16, dtype=np.float32)
            }

        state = self._get_game_state()

        return {
            'global_map': self._extract_global_map(state),
            'local_map': self._extract_local_map(state),
            'tactical_map': self._extract_tactical_map(state),
            'global': self._extract_global_features(state)
        }

    def _get_game_state(self):
        """Get raw game state."""
        if self.game is None:
            return None
        try:
            return self.game.get_state()
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return None

    def _extract_global_map(self, state) -> np.ndarray:
        """
        Extract global map: entire map downsampled to 128×128.
        Provides strategic overview of entire game.
        """
        if state is None:
            return np.zeros((128, 128, 5), dtype=np.float32)

        # Get full territory map and downsample
        if not hasattr(state, 'territory_map') or len(state.territory_map) == 0:
            return np.zeros((128, 128, 5), dtype=np.float32)

        territory_map = np.array(state.territory_map)

        # Extract 5 channels
        global_map = np.zeros((128, 128, 5), dtype=np.float32)

        # Channel 0: Your territory
        your_mask = (territory_map == 1).astype(np.float32)
        global_map[:, :, 0] = self._downsample_to_size(your_mask, 128, 128)

        # Channel 1: Enemy density
        enemy_mask = (territory_map > 1).astype(np.float32)
        global_map[:, :, 1] = self._downsample_to_size(enemy_mask, 128, 128)

        # Channel 2: Neutral territory
        neutral_mask = (territory_map == 0).astype(np.float32)
        global_map[:, :, 2] = self._downsample_to_size(neutral_mask, 128, 128)

        # Channels 3-4: Troop densities (if available)
        # For now, leave as zeros (would need troop map from game state)

        return global_map

    def _extract_local_map(self, state) -> np.ndarray:
        """
        Extract local map: region around player's territory center.
        Size: local_view_size×local_view_size → 128×128
        Provides tactical awareness of nearby area.
        """
        if state is None:
            return np.zeros((128, 128, 5), dtype=np.float32)

        if not hasattr(state, 'territory_map') or len(state.territory_map) == 0:
            return np.zeros((128, 128, 5), dtype=np.float32)

        territory_map = np.array(state.territory_map)
        map_h, map_w = territory_map.shape

        # Find player's territory center
        your_tiles = np.argwhere(territory_map == 1)
        if len(your_tiles) == 0:
            # No territory - use map center
            center_y, center_x = map_h // 2, map_w // 2
        else:
            center_y, center_x = your_tiles.mean(axis=0).astype(int)

        # Extract local region
        half_size = self.local_view_size // 2
        y_start = max(0, center_y - half_size)
        y_end = min(map_h, center_y + half_size)
        x_start = max(0, center_x - half_size)
        x_end = min(map_w, center_x + half_size)

        local_region = territory_map[y_start:y_end, x_start:x_end]

        # Extract channels
        local_map = np.zeros((128, 128, 5), dtype=np.float32)

        your_mask = (local_region == 1).astype(np.float32)
        local_map[:, :, 0] = self._downsample_to_size(your_mask, 128, 128)

        enemy_mask = (local_region > 1).astype(np.float32)
        local_map[:, :, 1] = self._downsample_to_size(enemy_mask, 128, 128)

        neutral_mask = (local_region == 0).astype(np.float32)
        local_map[:, :, 2] = self._downsample_to_size(neutral_mask, 128, 128)

        return local_map

    def _extract_tactical_map(self, state) -> np.ndarray:
        """
        Extract tactical map: immediate border region at full/high resolution.
        Size: 64×64 tiles around borders
        Provides precise control for attacks.
        """
        if state is None:
            return np.zeros((64, 64, 5), dtype=np.float32)

        if not hasattr(state, 'territory_map') or len(state.territory_map) == 0:
            return np.zeros((64, 64, 5), dtype=np.float32)

        territory_map = np.array(state.territory_map)
        map_h, map_w = territory_map.shape

        # Find player's border tiles (tiles adjacent to non-player tiles)
        your_tiles = (territory_map == 1)

        # Find borders using convolution
        from scipy.ndimage import binary_dilation
        expanded = binary_dilation(your_tiles)
        border_mask = expanded & ~your_tiles

        border_tiles = np.argwhere(your_tiles)

        if len(border_tiles) == 0:
            # No borders - use territory center
            your_tile_coords = np.argwhere(territory_map == 1)
            if len(your_tile_coords) == 0:
                center_y, center_x = map_h // 2, map_w // 2
            else:
                center_y, center_x = your_tile_coords.mean(axis=0).astype(int)
        else:
            # Use border center
            center_y, center_x = border_tiles.mean(axis=0).astype(int)

        # Extract 64×64 region around border center
        half_size = 32
        y_start = max(0, center_y - half_size)
        y_end = min(map_h, center_y + half_size)
        x_start = max(0, center_x - half_size)
        x_end = min(map_w, center_x + half_size)

        tactical_region = territory_map[y_start:y_end, x_start:x_end]

        # Extract channels
        tactical_map = np.zeros((64, 64, 5), dtype=np.float32)

        your_mask = (tactical_region == 1).astype(np.float32)
        tactical_map[:, :, 0] = self._downsample_to_size(your_mask, 64, 64)

        enemy_mask = (tactical_region > 1).astype(np.float32)
        tactical_map[:, :, 1] = self._downsample_to_size(enemy_mask, 64, 64)

        neutral_mask = (tactical_region == 0).astype(np.float32)
        tactical_map[:, :, 2] = self._downsample_to_size(neutral_mask, 64, 64)

        return tactical_map

    def _downsample_to_size(self, array: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
        """Downsample or upsample array to target size."""
        h, w = array.shape

        if h == target_h and w == target_w:
            return array

        # Upsample if too small
        if h < target_h or w < target_w:
            result = np.zeros((target_h, target_w), dtype=array.dtype)
            result[:min(h, target_h), :min(w, target_w)] = array[:min(h, target_h), :min(w, target_w)]
            return result

        # Downsample if too large
        scale_h = h / target_h
        scale_w = w / target_w
        scale = max(scale_h, scale_w)

        if scale <= 2:
            stride = 2
        elif scale <= 4:
            stride = 4
        elif scale <= 8:
            stride = 8
        else:
            stride = int(scale)

        downsampled = array[::stride, ::stride]
        result = np.zeros((target_h, target_w), dtype=array.dtype)
        result[:min(downsampled.shape[0], target_h), :min(downsampled.shape[1], target_w)] = \
            downsampled[:min(downsampled.shape[0], target_h), :min(downsampled.shape[1], target_w)]

        return result

    def _extract_global_features(self, state) -> np.ndarray:
        """Extract 16 global features (same as single-scale)."""
        if state is None:
            return np.zeros(16, dtype=np.float32)

        features = np.zeros(16, dtype=np.float32)

        # Same as single-scale environment
        # Population, territory, rank, etc.
        if hasattr(state, 'population') and hasattr(state, 'max_population'):
            features[0] = state.population / max(state.max_population, 1)
            features[1] = state.max_population / 100000.0

        if hasattr(state, 'territory_pct'):
            features[3] = state.territory_pct

        if hasattr(state, 'rank'):
            features[5] = state.rank / 50.0

        if hasattr(state, 'population') and hasattr(state, 'tiles_owned') and state.tiles_owned > 0:
            troops_per_tile = state.population / state.tiles_owned
            features[7] = troops_per_tile / 50.0

        # Add more features as in single-scale environment...

        return features

    def _execute_action(self, direction: int, intensity_idx: int):
        """Execute action in game."""
        if self.game is None:
            return

        intensity = self.intensities[intensity_idx]
        if self.game is not None:
            self.game.attack(direction=direction, troops_pct=intensity)

    def _compute_reward(self) -> float:
        """Compute reward (same as single-scale)."""
        if self.game is None:
            return 0.1

        state = self._get_game_state()
        reward = 0.0

        if hasattr(state, 'rank') and hasattr(state, 'total_players'):
            if state.total_players > 0:
                rank_percentile = 1.0 - (state.rank / state.total_players)

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

        if hasattr(state, 'territory_pct'):
            if state.territory_pct >= 0.80:
                reward += 10000

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

        if hasattr(state, 'territory_pct') and state.territory_pct >= 0.80:
            return True

        if hasattr(state, 'territory_pct') and state.territory_pct == 0.0:
            return True

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
        logger.info("Multi-scale environment closed")
