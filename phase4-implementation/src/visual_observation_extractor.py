"""
Visual Observation Extractor for Phase 4
Converts VisualState from visual game bridge to model observation format
"""

import numpy as np
from typing import Dict


class VisualObservationExtractor:
    """Extract observations from visual game state"""

    def __init__(self):
        self.map_size = 128
        self.cached_downsample_indices = None

    def extract_observation(self, visual_state: Dict) -> Dict[str, np.ndarray]:
        """
        Convert VisualState to observation format.

        Args:
            visual_state: Dict with tiles, players, rl_player, etc.

        Returns:
            Dict with 'map' (128x128x5) and 'global' (16,) arrays
        """
        if not visual_state:
            # Return zero observation if no state
            return {
                'map': np.zeros((self.map_size, self.map_size, 5), dtype=np.float32),
                'global': np.zeros(16, dtype=np.float32)
            }

        map_features = self._extract_map(visual_state)
        global_features = self._extract_global(visual_state)

        return {
            'map': map_features,
            'global': global_features
        }

    def _extract_map(self, visual_state: Dict) -> np.ndarray:
        """
        Extract 128×128×5 map features.

        Channels:
        0: Your territory (binary)
        1: Enemy density (aggregated, normalized)
        2: Neutral territory (binary)
        3: Your troop density (normalized)
        4: Terrain (water=0, land=1)
        """
        tiles = visual_state.get('tiles', [])
        map_width = visual_state.get('map_width', 2000)
        map_height = visual_state.get('map_height', 1500)
        rl_player_id = visual_state.get('rl_player', {}).get('id', 1)

        # Initialize channels
        your_territory = np.zeros((map_height, map_width), dtype=np.float32)
        enemy_density = np.zeros((map_height, map_width), dtype=np.float32)
        neutral_territory = np.zeros((map_height, map_width), dtype=np.float32)
        your_troops = np.zeros((map_height, map_width), dtype=np.float32)
        terrain = np.zeros((map_height, map_width), dtype=np.float32)

        # Process tiles
        max_troops = 1.0
        for tile in tiles:
            x = tile.get('x', 0)
            y = tile.get('y', 0)
            owner_id = tile.get('owner', 0)
            troops = tile.get('troops', 0)
            is_water = tile.get('terrain', '') == 'water'

            # Ensure coordinates are within bounds
            if x < 0 or x >= map_width or y < 0 or y >= map_height:
                continue

            # Terrain
            terrain[y, x] = 0.0 if is_water else 1.0

            # Territory and troops
            if owner_id == rl_player_id:
                your_territory[y, x] = 1.0
                your_troops[y, x] = troops
                max_troops = max(max_troops, troops)
            elif owner_id == 0:
                neutral_territory[y, x] = 1.0
            else:
                enemy_density[y, x] = troops
                max_troops = max(max_troops, troops)

        # Normalize troop densities
        if max_troops > 0:
            your_troops = your_troops / max_troops
            enemy_density = enemy_density / max_troops

        # Downsample to 128x128 using vectorized operations (MUCH faster)
        from scipy.ndimage import zoom

        scale_y = self.map_size / map_height
        scale_x = self.map_size / map_width

        # Stack all channels
        full_map = np.stack([your_territory, enemy_density, neutral_territory, your_troops, terrain], axis=-1)

        # Downsample all channels at once
        if map_height == self.map_size and map_width == self.map_size:
            downsampled = full_map
        else:
            downsampled = zoom(full_map, (scale_y, scale_x, 1), order=1)  # Linear interpolation

        # Ensure output shape is exactly 128x128x5
        if downsampled.shape[0] != self.map_size or downsampled.shape[1] != self.map_size:
            # Crop or pad to exact size
            downsampled = downsampled[:self.map_size, :self.map_size, :]

        return downsampled.astype(np.float32)

    def _extract_global(self, visual_state: Dict) -> np.ndarray:
        """
        Extract 16 global features.

        Features:
        0: Population (normalized by 100k)
        1: Tiles owned (normalized by map size)
        2: Territory percentage (0-1)
        3: Rank (normalized by num players)
        4-7: Reserved for future use
        8-15: Enemy stats (top 3 enemies + aggregate)
        """
        rl_player = visual_state.get('rl_player', {})
        players = visual_state.get('players', [])
        map_width = visual_state.get('map_width', 2000)
        map_height = visual_state.get('map_height', 1500)
        total_tiles = map_width * map_height

        features = np.zeros(16, dtype=np.float32)

        # Your stats
        features[0] = rl_player.get('troops', 0) / 100000.0  # Normalize population
        features[1] = rl_player.get('tiles_owned', 0) / total_tiles  # Normalize tiles
        features[2] = rl_player.get('territory_pct', 0.0) / 100.0  # Territory %
        features[3] = rl_player.get('rank', len(players)) / len(players) if len(players) > 0 else 1.0  # Rank

        # Enemy stats (top 3)
        enemy_players = [p for p in players if p.get('id') != rl_player.get('id', 1) and p.get('is_alive', False)]
        enemy_players.sort(key=lambda p: p.get('tiles_owned', 0), reverse=True)

        for i, enemy in enumerate(enemy_players[:3]):
            features[8 + i * 2] = enemy.get('troops', 0) / 100000.0
            features[8 + i * 2 + 1] = enemy.get('tiles_owned', 0) / total_tiles

        # Aggregate enemy stats
        if len(enemy_players) > 0:
            features[14] = sum(p.get('troops', 0) for p in enemy_players) / 100000.0
            features[15] = sum(p.get('tiles_owned', 0) for p in enemy_players) / total_tiles

        return features
