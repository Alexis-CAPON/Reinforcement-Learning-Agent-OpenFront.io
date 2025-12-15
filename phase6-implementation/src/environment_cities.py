"""
OpenFront.io Environment - Cities Only (Phase 6 Simplified)

Features:
- Cluster-aware actions for disconnected territories
- Building construction: Cities only
- Simplified action space: 2,500 actions (vs 38,500 in Phase 5)
- Basic action masking for economic constraints
- Compatible with sb3-contrib's MaskablePPO
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
from collections import deque

logger = logging.getLogger(__name__)


class OpenFrontEnvCities(gym.Env):
    """
    Simplified OpenFront environment - Cities only.

    Observation Space:
        Dict with:
        - 'map': Box(128, 128, 8*frame_stack) - Spatial features (simplified)
        - 'global': Box(16*frame_stack,) - Global state features (simplified)
        - 'clusters': Box(5, 4) - Up to 5 clusters with 4 features each

    Action Space:
        MultiDiscrete([5, 10, 5, 10])
        - cluster_id: 0-4 (which cluster to control)
        - action_type: 0-7=attack direction, 8=WAIT, 9=BUILD_CITY
        - intensity: 0-4 (15%, 30%, 45%, 60%, 75%) - for attacks only
        - tile: 0-9 (single tile index within cluster, normalized to x,y)

    Total actions: 5 * 10 * 5 * 10 = 2,500 actions
    Action masking reduces effective action space per step.
    """

    metadata = {'render_modes': []}

    def __init__(
        self,
        game_interface=None,
        num_bots: int = 10,
        map_name: str = 'australia_256x256',
        frame_stack: int = 4
    ):
        """
        Initialize full-game environment.

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

        # Observation space - simplified for cities only
        # 8 spatial channels (vs 16 in Phase 5)
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 8 * frame_stack), dtype=np.float32),
            'global': spaces.Box(-np.inf, np.inf, (16 * frame_stack,), dtype=np.float32),  # 16 global features
            'clusters': spaces.Box(0, 1, (5, 4), dtype=np.float32)  # 4 features per cluster
        })

        # Action space: Discrete space for [cluster, action_type, intensity, tile]
        # Total: 5 × 10 × 5 × 10 = 2,500 actions
        self.action_space = spaces.Discrete(2500)

        # Action components
        self.action_dims = (5, 10, 5, 10)  # Dimensions for decoding flat actions
        self.directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]
        # Only City building supported in Phase 6

        # State tracking
        self.previous_state = None
        self.step_count = 0
        self.episode_count = 0
        self.current_clusters = []

        logger.info(f"Cities-only environment initialized: map={map_name}, bots={num_bots}")
        logger.info(f"Action space size: {self.action_space.n:,} total actions (simplified from 38,500)")

    def action_masks(self) -> np.ndarray:
        """
        Generate action mask for current state.

        Returns mask of shape (5, 10, 5, 10) where True = valid, False = invalid

        Masking strategy:
        - Non-existent clusters: masked entirely
        - Attack actions (0-8): all intensities and tiles enabled
        - BUILD_CITY action (9): check gold availability
        """
        # Start with all actions masked (invalid)
        mask = np.zeros((5, 10, 5, 10), dtype=bool)

        if self.game is None:
            # Stub mode: allow all attacks
            mask[:, :9, :, :] = True
            return mask.flatten()

        state = self.game.get_state()
        # Use state.clusters directly instead of cached self.current_clusters
        clusters = state.clusters if hasattr(state, 'clusters') else []
        num_clusters = len(clusters)

        # For each existing cluster
        for cluster_id in range(min(num_clusters, 5)):
            # Attack actions (0-8): enable all directions/intensities/tiles
            for direction in range(9):
                for intensity in range(5):
                    for tile in range(10):
                        mask[cluster_id, direction, intensity, tile] = True

            # BUILD_CITY action (9): enable if we have gold
            if state.can_build_city:
                for tile in range(10):
                    mask[cluster_id, 9, 0, tile] = True

        return mask.flatten()

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
        self.current_clusters = []

        # Initialize frame buffer
        self.frame_buffer.clear()
        initial_obs = self._get_observation()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(initial_obs)

        obs = self._stack_frames()
        info = {'episode': self.episode_count}

        return obs, info

    def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one step with cities-only action.

        Args:
            action: Flat action index, decoded to [cluster_id, action_type, intensity, tile]

        Returns:
            observation: Next observation
            reward: Reward for this step
            terminated: Whether episode ended (win/loss)
            truncated: Whether episode was truncated (timeout)
            info: Additional information
        """
        if self.game is None:
            # Stub mode
            return self._stub_step(action)

        # Decode flat action into components
        action = int(action)
        cluster_id, action_type, intensity_idx, tile = np.unravel_index(
            action, self.action_dims
        )

        # Convert numpy int64 to Python int for JSON serialization
        cluster_id = int(cluster_id)
        action_type = int(action_type)
        intensity_idx = int(intensity_idx)
        tile = int(tile)

        # Validate cluster_id against current game state (not cached value)
        # This ensures consistency with action_masks() which uses state.clusters
        current_state = self.game.get_state()
        current_clusters = current_state.clusters if hasattr(current_state, 'clusters') else []
        if cluster_id >= len(current_clusters):
            # This can happen rarely due to mask enforcement timing or exploration
            # The action is safely converted to WAIT, so log at DEBUG level
            logger.debug(f"Invalid cluster_id {cluster_id}, have {len(current_clusters)} clusters. Converting to WAIT action.")
            action_type = 8  # WAIT

        # Execute action based on type
        action_success = False
        if action_type <= 8:
            # Attack action (0-8)
            intensity = self.intensities[intensity_idx]
            action_success = self._execute_cluster_action(cluster_id, action_type, intensity)
        elif action_type == 9:
            # BUILD_CITY action
            # Convert tile index (0-9) to 2×5 grid, then to normalized coordinates
            tile_x = tile % 2  # 0 or 1
            tile_y = tile // 2  # 0-4
            normalized_x = tile_x / 1.0  # 0.0 or 1.0
            normalized_y = tile_y / 4.0  # 0.0, 0.25, 0.5, 0.75, 1.0
            action_success = self._execute_build_action('City', normalized_x, normalized_y)

        # Update game state
        self.game.update()
        self.step_count += 1

        # Get new observation
        current_state = self.game.get_state()
        obs_frame = self._get_observation()
        self.frame_buffer.append(obs_frame)
        observation = self._stack_frames()

        # Compute reward
        reward = self._compute_reward(current_state, self.previous_state, action_success)

        # Check termination
        terminated = current_state.game_over
        truncated = False

        info = {
            'step': self.step_count,
            'territory': current_state.territory_pct,
            'population': current_state.population,
            'gold': current_state.gold,
            'action_success': action_success
        }

        self.previous_state = current_state

        return observation, reward, terminated, truncated, info

    def _execute_cluster_action(self, cluster_id: int, direction: int, intensity: float) -> bool:
        """Execute attack from specific cluster."""
        if self.game is not None:
            return self.game.attack_cluster(cluster_id=cluster_id, direction=direction, troops_pct=intensity)
        return False

    def _execute_build_action(self, building_type: str, tile_x: float, tile_y: float) -> bool:
        """Execute building construction."""
        if self.game is not None:
            try:
                return self.game.build_unit(unit_type=building_type, tile_x=tile_x, tile_y=tile_y)
            except RuntimeError as e:
                # Building failed (likely not enough gold or invalid location)
                logger.debug(f"Build action failed: {e}")
                return False
        return False

    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Get current observation for cities-only environment."""
        if self.game is None:
            # Stub observation
            return {
                'map': np.zeros((128, 128, 8), dtype=np.float32),  # 8 channels
                'global': np.zeros(16, dtype=np.float32),  # 16 global features
                'clusters': np.zeros((5, 4), dtype=np.float32)  # 4 features per cluster
            }

        state = self.game.get_state()

        # Get spatial map (downsampled to 128×128)
        map_data = self._extract_map_features(state)

        # Get expanded global features (32 features)
        global_features = self._extract_global_features(state)

        # Get cluster features
        cluster_features = self._extract_cluster_features(state)

        return {
            'map': map_data,
            'global': global_features,
            'clusters': cluster_features
        }

    def _extract_map_features(self, state) -> np.ndarray:
        """
        Extract 128×128 spatial features (8 channels, simplified for cities only).

        Channels:
        0: Our territory
        1: Enemy territory
        2: Neutral territory
        3: Border tiles
        4: Troop density
        5: Our cities
        6: Enemy cities
        7: Valid building locations (our territory, not occupied)
        """
        # Get map dimensions
        territory_map = np.array(state.territory_map, dtype=np.float32)
        h, w = territory_map.shape

        # Downsample to 128×128
        target_size = 128
        if h > target_size or w > target_size:
            from scipy.ndimage import zoom
            scale_h = target_size / h
            scale_w = target_size / w
            territory_map = zoom(territory_map, (scale_h, scale_w), order=0)

        # Pad if needed
        if territory_map.shape[0] < target_size or territory_map.shape[1] < target_size:
            padded = np.zeros((target_size, target_size), dtype=np.float32)
            padded[:territory_map.shape[0], :territory_map.shape[1]] = territory_map
            territory_map = padded

        # Create 8 channels (simplified for cities only)
        channels = np.zeros((target_size, target_size, 8), dtype=np.float32)

        # Channel 0: Our territory
        our_territory = (territory_map == 1).astype(np.float32)
        channels[:, :, 0] = our_territory

        # Channel 1: Enemy territory
        enemy_territory = (territory_map >= 2).astype(np.float32)
        channels[:, :, 1] = enemy_territory

        # Channel 2: Neutral territory
        channels[:, :, 2] = (territory_map == 0).astype(np.float32)

        # Channel 3: Border tiles
        from scipy.ndimage import sobel
        border = np.abs(sobel(territory_map, axis=0)) + np.abs(sobel(territory_map, axis=1))
        channels[:, :, 3] = np.clip(border, 0, 1)

        # Channel 4: Troop density (simplified - would need actual troop data)
        channels[:, :, 4] = our_territory * 0.5

        # Scale for building positions
        scale_x = target_size / w if w > 0 else 1
        scale_y = target_size / h if h > 0 else 1

        # Channel 5: Our cities
        for pos in state.our_cities_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 5] = 1.0

        # Channel 6: Enemy cities (if available)
        if hasattr(state, 'enemy_cities_positions'):
            for pos in state.enemy_cities_positions:
                x_scaled = int(pos['x'] * scale_x)
                y_scaled = int(pos['y'] * scale_y)
                if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                    channels[y_scaled, x_scaled, 6] = 1.0

        # Channel 7: Valid building locations (our territory)
        channels[:, :, 7] = our_territory

        return channels

    def _extract_global_features(self, state) -> np.ndarray:
        """Extract 16 global features (simplified for cities only)."""
        features = np.zeros(16, dtype=np.float32)

        # Territory features (0-4)
        features[0] = state.territory_pct
        features[1] = state.tiles_owned / max(state.total_tiles, 1)
        features[2] = state.neutral_tiles / max(state.total_tiles, 1)
        features[3] = state.border_tiles / max(state.tiles_owned, 1)
        features[4] = state.territory_change

        # Population features (5-7)
        features[5] = state.population / max(state.max_population, 1)
        features[6] = state.population_growth_rate
        features[7] = state.border_pressure

        # Game state features (8-10)
        features[8] = state.rank / max(state.total_players, 1)
        features[9] = state.alive_players / max(state.total_players, 1)
        features[10] = state.time_alive / 10000.0

        # Economic features (11-13)
        features[11] = np.log1p(state.gold) / 10.0  # Log-scaled gold
        features[12] = state.cities_count / 10.0
        features[13] = float(state.can_build_city)

        # Cluster information (14-15)
        num_clusters = len(state.clusters) if hasattr(state, 'clusters') else 0
        features[14] = num_clusters / 5.0
        if num_clusters > 0:
            features[15] = state.clusters[0]['troop_count'] / max(state.population, 1)  # Largest cluster

        return features

    def _extract_cluster_features(self, state) -> np.ndarray:
        """Extract cluster features (5 clusters × 4 features, simplified)."""
        cluster_features = np.zeros((5, 4), dtype=np.float32)

        if not hasattr(state, 'clusters'):
            self.current_clusters = []
            return cluster_features

        clusters = state.clusters
        self.current_clusters = clusters

        for i, cluster in enumerate(clusters[:5]):
            # Feature 0: Normalized tile count
            cluster_features[i, 0] = len(cluster['tiles']) / max(state.tiles_owned, 1)

            # Feature 1: Normalized troop count
            cluster_features[i, 1] = cluster['troop_count'] / max(state.population, 1)

            # Feature 2: Has city (1 if cluster has city, 0 otherwise)
            cluster_features[i, 2] = 0.0  # Would need to check if cluster has city

            # Feature 3: Can afford city
            cluster_features[i, 3] = float(state.can_build_city)

        return cluster_features

    def _stack_frames(self) -> Dict[str, np.ndarray]:
        """Stack frames for temporal context."""
        frames = list(self.frame_buffer)

        # Stack map features
        map_stack = np.concatenate([f['map'] for f in frames], axis=2)

        # Stack global features
        global_stack = np.concatenate([f['global'] for f in frames])

        # Use latest cluster features (don't stack)
        clusters = frames[-1]['clusters']

        return {
            'map': map_stack,
            'global': global_stack,
            'clusters': clusters
        }

    def _compute_reward(self, current_state, previous_state, action_success: bool) -> float:
        """
        Compute reward (simplified for cities only).

        Reward components:
        - Territory growth: +10 per tile gained
        - Population growth: +5 per increase
        - Survival: +1 per step
        - Elimination bonus: +50 per player eliminated
        - Gold accumulation: +0.1 per gold gained
        - City construction: +20 per city built
        - Win bonus: +200
        - Death penalty: -100 if eliminated
        """
        if previous_state is None:
            return 1.0  # Initial reward

        reward = 0.0

        # Territory reward
        territory_gained = current_state.tiles_owned - previous_state.tiles_owned
        reward += territory_gained * 10.0

        # Population reward
        pop_increase = current_state.population - previous_state.population
        reward += pop_increase * 5.0

        # Survival bonus
        if current_state.game_over and current_state.has_won:
            reward += 200.0
        elif current_state.game_over and current_state.has_lost:
            reward -= 100.0
        else:
            reward += 1.0

        # Elimination bonus
        players_eliminated = previous_state.alive_players - current_state.alive_players
        if players_eliminated > 0:
            reward += players_eliminated * 50.0

        # Economic rewards
        gold_gained = current_state.gold - previous_state.gold
        reward += gold_gained * 0.1

        # City construction bonus
        cities_built = current_state.cities_count - previous_state.cities_count
        if cities_built > 0:
            reward += cities_built * 20.0

        return reward

    def _stub_step(self, action):
        """Stub step for testing without game."""
        obs = {
            'map': np.random.rand(128, 128, 8 * self.frame_stack).astype(np.float32),  # 8 channels
            'global': np.random.rand(16 * self.frame_stack).astype(np.float32),  # 16 features
            'clusters': np.random.rand(5, 4).astype(np.float32)  # 4 features per cluster
        }
        reward = np.random.rand()
        terminated = False
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

    def close(self):
        """Clean up resources."""
        if self.game is not None:
            self.game.close()
