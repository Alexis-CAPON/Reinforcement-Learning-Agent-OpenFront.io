"""
OpenFront.io Environment with Cluster-Aware Actions

Features:
- Agent sees disconnected territory clusters in observation
- Agent chooses which cluster to control (action masking for non-existent clusters)
- Each cluster can attack independently
- Compatible with sb3-contrib's MaskablePPO
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
from collections import deque

logger = logging.getLogger(__name__)


class OpenFrontEnvClusters(gym.Env):
    """
    Cluster-aware OpenFront environment.

    Observation Space:
        Dict with:
        - 'map': Box(128, 128, 5*frame_stack) - Spatial features
        - 'global': Box(16*frame_stack,) - Global state features
        - 'clusters': Box(5, 6) - Up to 5 clusters with 6 features each

    Action Space:
        MultiDiscrete([5, 9, 5]) - [cluster_id, direction, intensity]
        - cluster_id: 0-4 (which cluster to control)
        - direction: 0-8 (N, NE, E, SE, S, SW, W, NW, WAIT)
        - intensity: 0-4 (15%, 30%, 45%, 60%, 75%)
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
        Initialize cluster-aware environment.

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

        # Observation space with clusters
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 5 * frame_stack), dtype=np.float32),
            'global': spaces.Box(-np.inf, np.inf, (16 * frame_stack,), dtype=np.float32),
            'clusters': spaces.Box(0, 1, (5, 6), dtype=np.float32)  # NEW: 5 clusters, 6 features each
        })

        # NEW: Action space for cluster-aware actions
        # [cluster_id (0-4), direction (0-8), intensity (0-4)]
        self.action_space = spaces.MultiDiscrete([5, 9, 5])

        # Action components
        self.directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]

        # State tracking
        self.previous_state = None
        self.step_count = 0
        self.episode_count = 0
        self.current_clusters = []

        logger.info(f"Cluster environment initialized: map={map_name}, bots={num_bots}")

    def action_masks(self) -> np.ndarray:
        """
        Generate action mask for current state.

        Returns mask of shape (5, 9, 5) where True = valid, False = invalid

        This prevents agent from:
        - Selecting non-existent clusters
        - Invalid direction/intensity combinations (currently all valid)
        """
        mask = np.ones((5, 9, 5), dtype=bool)

        # Mask out non-existent clusters
        num_clusters = len(self.current_clusters)
        if num_clusters < 5:
            # Disable actions for clusters that don't exist
            mask[num_clusters:, :, :] = False

        return mask

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
        Execute one step with cluster-based action.

        Args:
            action: np.array([cluster_id, direction, intensity])
                - cluster_id: 0-4
                - direction: 0-8
                - intensity: 0-4

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

        cluster_id, direction_idx, intensity_idx = action
        cluster_id = int(cluster_id)
        direction_idx = int(direction_idx)
        intensity_idx = int(intensity_idx)

        # Validate cluster_id
        if cluster_id >= len(self.current_clusters):
            # Invalid cluster - treat as WAIT
            logger.warning(f"Invalid cluster_id {cluster_id}, have {len(self.current_clusters)} clusters. Treating as WAIT.")
            direction_idx = 8  # WAIT

        intensity = self.intensities[intensity_idx]

        # Execute action
        self._execute_cluster_action(cluster_id, direction_idx, intensity)

        # Tick game
        self.game.tick()
        self.step_count += 1

        # Get new observation
        current_state = self.game.get_state()
        obs_frame = self._get_observation()
        self.frame_buffer.append(obs_frame)
        observation = self._stack_frames()

        # Compute reward
        reward = self._compute_reward(current_state, self.previous_state)

        # Check termination
        terminated = current_state.game_over
        truncated = False

        info = {
            'step': self.step_count,
            'territory_pct': current_state.territory_pct,
            'population': current_state.population,
            'num_clusters': len(self.current_clusters),
            'cluster_action': f"Cluster {cluster_id} -> {self.directions[direction_idx]} ({intensity*100:.0f}%)"
        }

        self.previous_state = current_state

        return observation, reward, terminated, truncated, info

    def _execute_cluster_action(self, cluster_id: int, direction: int, intensity: float):
        """Execute attack from specific cluster."""
        if self.game is not None:
            self.game.attack_cluster(cluster_id=cluster_id, direction=direction, troops_pct=intensity)

    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Get current observation including cluster information."""
        if self.game is None:
            # Stub observation
            return {
                'map': np.zeros((128, 128, 5), dtype=np.float32),
                'global': np.zeros(16, dtype=np.float32),
                'clusters': np.zeros((5, 6), dtype=np.float32)
            }

        state = self.game.get_state()

        # Get spatial map (downsampled to 128×128)
        map_data = self._extract_map_features(state)

        # Get global features
        global_features = self._extract_global_features(state)

        # NEW: Get cluster features
        cluster_features = self._extract_cluster_features(state)

        return {
            'map': map_data,
            'global': global_features,
            'clusters': cluster_features
        }

    def _extract_cluster_features(self, state) -> np.ndarray:
        """
        Extract features for up to 5 territory clusters.

        Returns:
            np.array of shape (5, 6) with features:
            [exists, center_x, center_y, size_pct, troops_pct, border_tiles_pct]
        """
        clusters = np.zeros((5, 6), dtype=np.float32)

        if not hasattr(state, 'clusters') or not state.clusters:
            self.current_clusters = []
            return clusters

        self.current_clusters = state.clusters
        total_tiles = state.tiles_owned if state.tiles_owned > 0 else 1
        total_troops = state.population if state.population > 0 else 1
        total_borders = state.border_tiles if state.border_tiles > 0 else 1

        for i, cluster in enumerate(state.clusters[:5]):  # Top 5 clusters
            # Normalize features to [0, 1]
            clusters[i, 0] = 1.0  # exists
            clusters[i, 1] = cluster['center_x'] / max(state.territory_map.shape[1] if hasattr(state.territory_map, 'shape') else 512, 1)  # normalized x
            clusters[i, 2] = cluster['center_y'] / max(state.territory_map.shape[0] if hasattr(state.territory_map, 'shape') else 512, 1)  # normalized y
            clusters[i, 3] = len(cluster['tiles']) / total_tiles  # size percentage
            clusters[i, 4] = cluster['troop_count'] / total_troops  # troop percentage
            clusters[i, 5] = len(cluster['border_tiles']) / total_borders  # border percentage

        return clusters

    def _extract_map_features(self, state) -> np.ndarray:
        """Extract and downsample spatial map features to 128×128×5."""
        # Implementation same as environment.py
        # ... (keeping it simple for now, can copy from environment.py)
        return np.zeros((128, 128, 5), dtype=np.float32)

    def _extract_global_features(self, state) -> np.ndarray:
        """Extract 16 global features."""
        # Implementation same as environment.py
        return np.zeros(16, dtype=np.float32)

    def _stack_frames(self) -> Dict[str, np.ndarray]:
        """Stack frames for temporal context."""
        map_stack = np.concatenate([f['map'] for f in self.frame_buffer], axis=2)
        global_stack = np.concatenate([f['global'] for f in self.frame_buffer], axis=0)
        # Clusters: use only most recent (no stacking)
        clusters = self.frame_buffer[-1]['clusters']

        return {
            'map': map_stack,
            'global': global_stack,
            'clusters': clusters
        }

    def _compute_reward(self, current_state, previous_state) -> float:
        """Compute reward for current step."""
        if previous_state is None:
            return 0.0

        # Territory growth reward
        territory_reward = (current_state.territory_pct - previous_state.territory_pct) * 100

        # Survival reward
        survival_reward = 0.1

        # Win/loss rewards
        if current_state.has_won:
            return 100.0
        if current_state.has_lost:
            return -50.0

        return territory_reward + survival_reward

    def _stub_step(self, action):
        """Stub step for testing without game."""
        obs = {
            'map': np.zeros((128, 128, 5 * self.frame_stack), dtype=np.float32),
            'global': np.zeros(16 * self.frame_stack, dtype=np.float32),
            'clusters': np.zeros((5, 6), dtype=np.float32)
        }
        return obs, 0.0, False, False, {}

    def close(self):
        """Clean up resources."""
        if self.game is not None:
            self.game.close()
