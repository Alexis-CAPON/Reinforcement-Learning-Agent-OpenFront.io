"""
OpenFront.io Environment with Full Game Features (Buildings + Nukes)

Features:
- Cluster-aware actions for disconnected territories
- Building construction: Cities, Ports, Silos, SAM Launchers, Defense Posts, Factories
- Nuclear weapons: Atom Bombs, Hydrogen Bombs
- Advanced action masking for economic/military constraints
- Compatible with sb3-contrib's MaskablePPO
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
from collections import deque

logger = logging.getLogger(__name__)


class OpenFrontEnvFullGame(gym.Env):
    """
    Full-featured OpenFront environment with buildings and nukes.

    Observation Space:
        Dict with:
        - 'map': Box(128, 128, 5*frame_stack) - Spatial features
        - 'global': Box(32*frame_stack,) - Global state features (expanded)
        - 'clusters': Box(5, 6) - Up to 5 clusters with 6 features each

    Action Space:
        MultiDiscrete([5, 11, 5, 7, 2, 10, 10])
        - cluster_id: 0-4 (which cluster to control)
        - action_type: 0-8=attack direction, 9=build, 10=launch nuke
        - intensity: 0-4 (15%, 30%, 45%, 60%, 75%) - for attacks only
        - building_type: 0=none, 1=City, 2=Port, 3=Silo, 4=SAM, 5=Defense, 6=Factory
        - nuke_type: 0=Atom Bomb, 1=Hydrogen Bomb
        - tile_x: 0-9 (10 discrete positions across map width, normalized)
        - tile_y: 0-9 (10 discrete positions across map height, normalized)

    Total actions: 5 * 11 * 5 * 7 * 2 * 10 * 10 = 38,500 actions
    Heavy action masking reduces effective action space per step.
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

        # Observation space with expanded spatial features for buildings/nukes
        # Increased from 5 to 16 spatial channels to show building locations
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 16 * frame_stack), dtype=np.float32),  # Expanded to 16 channels
            'global': spaces.Box(-np.inf, np.inf, (32 * frame_stack,), dtype=np.float32),  # 32 global features
            'clusters': spaces.Box(0, 1, (5, 6), dtype=np.float32)
        })

        # Action space: Discrete space for all combinations of [cluster, action_type, intensity, building, nuke, tile]
        # Total: 5 × 11 × 5 × 7 × 2 × 10 = 38,500 actions
        # tile represents 10 possible tile positions within cluster (encoded as single index)
        self.action_space = spaces.Discrete(38500)

        # Action components
        self.action_dims = (5, 11, 5, 7, 2, 10)  # Dimensions for decoding flat actions
        self.directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]
        self.building_types = ['None', 'City', 'Port', 'Missile Silo', 'SAM Launcher', 'Defense Post', 'Factory']
        self.nuke_types = ['Atom Bomb', 'Hydrogen Bomb']

        # State tracking
        self.previous_state = None
        self.step_count = 0
        self.episode_count = 0
        self.current_clusters = []

        logger.info(f"Full-game environment initialized: map={map_name}, bots={num_bots}")
        logger.info(f"Action space size: {self.action_space.n:,} total actions")

    def action_masks(self) -> np.ndarray:
        """
        Generate action mask for current state.

        Returns mask of shape (5, 11, 5, 7, 2, 10) where True = valid, False = invalid

        Masking strategy:
        - Non-existent clusters: masked entirely
        - Attack actions (0-8): mask building/nuke params
        - Build actions (9): mask intensity/nuke params, check affordability
        - Nuke actions (10): mask intensity/building params, check availability
        """
        # Start with all actions masked (invalid)
        mask = np.zeros((5, 11, 5, 7, 2, 10), dtype=bool)

        if self.game is None:
            # Stub mode: allow all attacks
            mask[:, :9, :, 0, 0, :] = True
            return mask.flatten()

        state = self.game.get_state()
        num_clusters = len(self.current_clusters)

        # For each existing cluster
        for cluster_id in range(min(num_clusters, 5)):
            # Attack actions (0-8): enable all directions/intensities
            for direction in range(9):
                for intensity in range(5):
                    # Mask out building_type[0], nuke_type[0], tile[0]
                    mask[cluster_id, direction, intensity, 0, 0, 0] = True

            # Build actions (9): enable if we have gold
            if state.can_build_city:
                for tile in range(10):
                    mask[cluster_id, 9, 0, 1, 0, tile] = True  # City

            if state.can_build_port:
                for tile in range(10):
                    mask[cluster_id, 9, 0, 2, 0, tile] = True  # Port

            if state.can_build_silo:
                for tile in range(10):
                    mask[cluster_id, 9, 0, 3, 0, tile] = True  # Silo

            if state.can_build_sam:
                for tile in range(10):
                    mask[cluster_id, 9, 0, 4, 0, tile] = True  # SAM

            # Defense Post and Factory (assuming same cost as SAM for now)
            if state.can_build_sam:
                for tile in range(10):
                    mask[cluster_id, 9, 0, 5, 0, tile] = True  # Defense
                    mask[cluster_id, 9, 0, 6, 0, tile] = True  # Factory

            # Nuke actions (10): enable if we have nukes and silos
            if state.can_launch_nuke:
                atom_bombs = state.atom_bombs_available
                hydrogen_bombs = state.hydrogen_bombs_available

                for tile in range(10):
                    if atom_bombs > 0:
                        mask[cluster_id, 10, 0, 0, 0, tile] = True  # Atom
                    if hydrogen_bombs > 0:
                        mask[cluster_id, 10, 0, 0, 1, tile] = True  # Hydrogen

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
        Execute one step with full-game action.

        Args:
            action: np.array([cluster_id, action_type, intensity, building_type, nuke_type, tile_x, tile_y])

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
        cluster_id, action_type, intensity_idx, building_idx, nuke_idx, tile = np.unravel_index(
            action, self.action_dims
        )

        # Convert numpy int64 to Python int for JSON serialization
        cluster_id = int(cluster_id)
        action_type = int(action_type)
        intensity_idx = int(intensity_idx)
        building_idx = int(building_idx)
        nuke_idx = int(nuke_idx)
        tile = int(tile)

        # Validate cluster_id
        if cluster_id >= len(self.current_clusters):
            logger.warning(f"Invalid cluster_id {cluster_id}, have {len(self.current_clusters)} clusters. Skipping action.")
            action_type = 8  # WAIT

        # Execute action based on type
        action_success = False
        if action_type <= 8:
            # Attack action
            intensity = self.intensities[intensity_idx]
            action_success = self._execute_cluster_action(cluster_id, action_type, intensity)
        elif action_type == 9:
            # Build action
            if building_idx > 0:
                building_type = self.building_types[building_idx]
                # Convert tile index (0-9) to 2×5 grid, then to normalized coordinates
                tile_x = tile % 2  # 0 or 1
                tile_y = tile // 2  # 0-4
                normalized_x = tile_x / 1.0  # 0.0 or 1.0
                normalized_y = tile_y / 4.0  # 0.0, 0.25, 0.5, 0.75, 1.0
                action_success = self._execute_build_action(building_type, normalized_x, normalized_y)
        elif action_type == 10:
            # Nuke action
            nuke_type = self.nuke_types[nuke_idx]
            # Convert tile index (0-9) to 2×5 grid, then to normalized coordinates
            tile_x = tile % 2  # 0 or 1
            tile_y = tile // 2  # 0-4
            normalized_x = tile_x / 1.0  # 0.0 or 1.0
            normalized_y = tile_y / 4.0  # 0.0, 0.25, 0.5, 0.75, 1.0
            action_success = self._execute_nuke_action(nuke_type, normalized_x, normalized_y)

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

    def _execute_nuke_action(self, nuke_type: str, tile_x: float, tile_y: float) -> bool:
        """Execute nuke launch."""
        if self.game is not None:
            try:
                return self.game.launch_nuke(nuke_type=nuke_type, tile_x=tile_x, tile_y=tile_y)
            except RuntimeError as e:
                # Nuke launch failed (likely no nukes available or invalid location)
                logger.debug(f"Nuke action failed: {e}")
                return False
        return False

    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Get current observation including cluster and economic/military information."""
        if self.game is None:
            # Stub observation
            return {
                'map': np.zeros((128, 128, 16), dtype=np.float32),  # Updated to 16 channels
                'global': np.zeros(32, dtype=np.float32),
                'clusters': np.zeros((5, 6), dtype=np.float32)
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
        Extract 128×128 spatial features (16 channels).

        Channels:
        0: Our territory
        1: Enemy territory
        2: Neutral territory
        3: Border tiles
        4: Troop density
        5: Our cities
        6: Our ports
        7: Our missile silos
        8: Our SAM launchers
        9: Our defense posts
        10: Our factories
        11: Enemy buildings (all types)
        12: Valid building locations (our territory, not occupied)
        13: High-value targets (enemy clusters)
        14: Defensive coverage (SAM range)
        15: Strategic importance (chokepoints, borders)
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

        # Create 16 channels
        channels = np.zeros((target_size, target_size, 16), dtype=np.float32)

        # Channel 0: Our territory
        our_territory = (territory_map == 1).astype(np.float32)
        channels[:, :, 0] = our_territory

        # Channel 1: Enemy territory
        enemy_territory = (territory_map >= 2).astype(np.float32)
        channels[:, :, 1] = enemy_territory

        # Channel 2: Neutral territory
        channels[:, :, 2] = (territory_map == 0).astype(np.float32)

        # Channel 3: Border tiles
        from scipy.ndimage import sobel, binary_dilation
        border = np.abs(sobel(territory_map, axis=0)) + np.abs(sobel(territory_map, axis=1))
        channels[:, :, 3] = np.clip(border, 0, 1)

        # Channel 4: Troop density (simplified - would need actual troop data)
        channels[:, :, 4] = our_territory * 0.5

        # Channels 5-10: Our buildings (EXACT positions)
        # Plot each building at its actual location
        scale_x = target_size / w if w > 0 else 1
        scale_y = target_size / h if h > 0 else 1

        # Channel 5: Our cities
        for pos in state.our_cities_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 5] = 1.0

        # Channel 6: Our ports
        for pos in state.our_ports_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 6] = 1.0

        # Channel 7: Our missile silos
        for pos in state.our_silos_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 7] = 1.0

        # Channel 8: Our SAM launchers
        for pos in state.our_sam_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 8] = 1.0

        # Channel 9: Our defense posts
        for pos in state.our_defense_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 9] = 1.0

        # Channel 10: Our factories
        for pos in state.our_factories_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 10] = 1.0

        # Channel 11: Enemy buildings (EXACT positions)
        for pos in state.enemy_buildings_positions:
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 11] = 1.0

        # Channel 12: Valid building locations (our territory)
        channels[:, :, 12] = our_territory

        # Channel 13: High-value targets (enemy territory near borders)
        enemy_near_border = enemy_territory * channels[:, :, 3]
        channels[:, :, 13] = enemy_near_border

        # Channel 14: Defensive coverage (SAM range - dilated SAM positions)
        if state.sam_launchers_count > 0:
            sam_coverage = binary_dilation(channels[:, :, 8] > 0, iterations=3).astype(np.float32)
            channels[:, :, 14] = sam_coverage

        # Channel 15: Strategic importance (border regions + chokepoints)
        # Dilate borders to show strategically important areas
        strategic = binary_dilation(channels[:, :, 3] > 0, iterations=2).astype(np.float32)
        channels[:, :, 15] = strategic * our_territory

        return channels

    def _extract_global_features(self, state) -> np.ndarray:
        """Extract 32 global features including economic/military."""
        features = np.zeros(32, dtype=np.float32)

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

        # Game state features (8-11)
        features[8] = state.rank / max(state.total_players, 1)
        features[9] = state.alive_players / max(state.total_players, 1)
        features[10] = state.time_alive / 10000.0
        features[11] = state.nearest_threat / 500.0

        # Economic features (12-19)
        features[12] = np.log1p(state.gold) / 10.0  # Log-scaled gold
        features[13] = state.cities_count / 10.0
        features[14] = state.ports_count / 10.0
        features[15] = state.silos_count / 5.0
        features[16] = state.sam_launchers_count / 5.0
        features[17] = state.defense_posts_count / 10.0
        features[18] = state.factories_count / 5.0
        features[19] = state.num_cities / 10.0

        # Military features (20-23)
        features[20] = state.atom_bombs_available / 5.0
        features[21] = state.hydrogen_bombs_available / 3.0
        features[22] = float(state.can_launch_nuke)
        features[23] = float(state.silos_count > 0)

        # Building capabilities (24-27)
        features[24] = float(state.can_build_city)
        features[25] = float(state.can_build_port)
        features[26] = float(state.can_build_silo)
        features[27] = float(state.can_build_sam)

        # Cluster information (28-31)
        num_clusters = len(state.clusters) if hasattr(state, 'clusters') else 0
        features[28] = num_clusters / 5.0
        if num_clusters > 0:
            features[29] = state.clusters[0]['troop_count'] / max(state.population, 1)  # Largest cluster
            features[30] = len(state.clusters[0]['tiles']) / max(state.tiles_owned, 1)
            features[31] = len(state.clusters[0]['border_tiles']) / max(len(state.clusters[0]['tiles']), 1)

        return features

    def _extract_cluster_features(self, state) -> np.ndarray:
        """Extract cluster features (5 clusters × 6 features)."""
        cluster_features = np.zeros((5, 6), dtype=np.float32)

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

            # Feature 2: Border ratio
            cluster_features[i, 2] = len(cluster['border_tiles']) / max(len(cluster['tiles']), 1)

            # Feature 3-4: Normalized center position
            cluster_features[i, 3] = cluster['center_x'] / state.total_tiles ** 0.5
            cluster_features[i, 4] = cluster['center_y'] / state.total_tiles ** 0.5

            # Feature 5: Cluster ID (normalized)
            cluster_features[i, 5] = i / 5.0

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
        Compute reward with economic and military bonuses.

        Reward components:
        - Territory growth: +10 per % gained
        - Population growth: +5 per increase
        - Survival: +1 per step
        - Elimination bonus: +50 per player eliminated
        - Economic growth: +0.1 per gold gained
        - Building bonus: +20 for constructing buildings
        - Nuke bonus: +100 for successful nuke launch
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

        # Building rewards
        buildings_built = (
            (current_state.cities_count - previous_state.cities_count) +
            (current_state.ports_count - previous_state.ports_count) +
            (current_state.silos_count - previous_state.silos_count) +
            (current_state.sam_launchers_count - previous_state.sam_launchers_count) +
            (current_state.defense_posts_count - previous_state.defense_posts_count) +
            (current_state.factories_count - previous_state.factories_count)
        )
        if buildings_built > 0:
            reward += buildings_built * 20.0

        # Nuke rewards (if nukes were used)
        nukes_used = (
            (previous_state.atom_bombs_available - current_state.atom_bombs_available) +
            (previous_state.hydrogen_bombs_available - current_state.hydrogen_bombs_available)
        )
        if nukes_used > 0 and action_success:
            reward += nukes_used * 100.0

        return reward

    def _stub_step(self, action):
        """Stub step for testing without game."""
        obs = {
            'map': np.random.rand(128, 128, 16 * self.frame_stack).astype(np.float32),  # Updated to 16 channels
            'global': np.random.rand(32 * self.frame_stack).astype(np.float32),
            'clusters': np.random.rand(5, 6).astype(np.float32)
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
