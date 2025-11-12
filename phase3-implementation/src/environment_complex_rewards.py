"""
OpenFront.io Phase 3 Environment - Battle Royale

Features:
- 128×128×5 map features (spatial)
- 16 global features
- Direction-based actions (9 directions × 5 intensities × 2 build)
- Battle royale mode with 10-50 bots
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging
import os
import sys
from collections import deque

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger(__name__)


class OpenFrontEnv(gym.Env):
    """
    Phase 3 OpenFront.io Environment for battle royale training.

    Observation Space:
        Dict with:
        - 'map': Box(128, 128, 5) - Spatial features
        - 'global': Box(16,) - Global state features

    Action Space:
        Discrete(45) - 9 directions × 5 intensities
    """

    metadata = {'render_modes': []}

    def __init__(self, game_interface=None, num_bots: int = 50, map_name: str = 'plains', frame_stack: int = 4):
        """
        Initialize environment.

        Args:
            game_interface: Game wrapper/bridge interface (created if None)
            num_bots: Number of bot opponents (10-50)
            map_name: Name of map to use
            frame_stack: Number of frames to stack for temporal context (default: 4)
        """
        super().__init__()

        # Create game wrapper if not provided
        if game_interface is None:
            try:
                from game_wrapper import GameWrapper
                self.game = GameWrapper(map_name=map_name, num_players=num_bots + 1)
                logger.info("Created GameWrapper instance")
            except ImportError as e:
                logger.warning(f"Could not import GameWrapper: {e}")
                logger.warning("Environment will run in stub mode (for testing)")
                self.game = None
        else:
            self.game = game_interface

        self.num_bots = num_bots
        self.map_name = map_name
        self.frame_stack = frame_stack

        # Frame stacking for temporal context
        self.frame_buffer = deque(maxlen=frame_stack)

        # Observation space (with frame stacking)
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
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]  # Max 75% (no suicide 100% attacks)

        # State tracking
        self.previous_state = None
        self.step_count = 0
        self.episode_count = 0
        self.last_action_was_wait = False  # Track if action was WAIT
        self.recent_attack_directions = []  # Track last 10 attack directions
        self.last_direction = None  # Track previous attack direction

        logger.info(f"Environment initialized with {num_bots} bots")

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
        self.recent_attack_directions = []  # Reset attack tracking
        self.last_direction = None

        # Get initial observation
        obs = self._get_obs()

        # Fill frame buffer with initial observation
        self.frame_buffer.clear()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(obs)

        info = {}

        logger.info(f"Episode {self.episode_count} started with {self.num_bots} bots")

        return self._stack_frames(), info

    def step(
        self,
        action: int
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one environment step.

        Args:
            action: Flattened action index (0-89)

        Returns:
            observation: Next state
            reward: Reward for this step
            terminated: Episode ended (win/loss)
            truncated: Episode truncated (max steps)
            info: Additional information
        """
        # Decode action (9 directions × 5 intensities = 45 actions)
        direction = action // 5
        intensity_idx = action % 5

        # Track if this is a WAIT action
        self.last_action_was_wait = (direction == 8)  # Direction 8 is WAIT

        # Track attack directions for multi-front penalty
        if direction < 8:  # Not waiting
            self.recent_attack_directions.append(direction)
            if len(self.recent_attack_directions) > 10:
                self.recent_attack_directions.pop(0)  # Keep only last 10
            self.last_direction = direction

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

        # Add episode summary info if terminated
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

            # Log episode end with detailed stats
            result = "🏆 VICTORY" if info['episode']['won'] else "💀 ELIMINATED"
            logger.info(
                f"Episode {self.episode_count} ended: {result}\n"
                f"  Steps: {self.step_count}\n"
                f"  Tiles: {info['episode']['tiles']}\n"
                f"  Troops: {info['episode']['troops']}\n"
                f"  Territory: {info['episode']['territory_pct']*100:.1f}%\n"
                f"  Rank: {info['episode']['rank']}/{self.num_bots+1}\n"
                f"  Total Reward: {reward:.2f}"
            )

        return self._stack_frames(), reward, terminated, False, info

    def _stack_frames(self) -> Dict[str, np.ndarray]:
        """
        Stack frames from buffer for temporal context.

        Returns:
            Dict with stacked 'map' and 'global' features
        """
        # Stack all frames in buffer
        stacked_map = np.concatenate(
            [frame['map'] for frame in self.frame_buffer],
            axis=2  # Concatenate along channel dimension
        )  # [128, 128, 5*frame_stack]

        stacked_global = np.concatenate(
            [frame['global'] for frame in self.frame_buffer]
        )  # [16*frame_stack]

        return {
            'map': stacked_map,
            'global': stacked_global
        }

    def _get_obs(self) -> Dict[str, np.ndarray]:
        """
        Get current observation (single frame, NOT stacked).

        Returns:
            Dict with 'map' and 'global' features
        """
        if self.game is None:
            # Return zero observation if game not initialized
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
        Extract 128×128×5 map features from game state.

        Channels:
        0: Your territory (binary)
        1: Enemy density (aggregated, normalized)
        2: Neutral territory (binary)
        3: Your troop density (normalized)
        4: Enemy troop density (aggregated, normalized)

        Returns:
            Map array [128, 128, 5]
        """
        if state is None:
            return np.zeros((128, 128, 5), dtype=np.float32)

        map_feat = np.zeros((128, 128, 5), dtype=np.float32)

        # Get raw map data (assumed to be 512×512 or similar)
        # This would need to be implemented based on actual game interface

        # Channel 0: Your territory
        if hasattr(state, 'your_territory_mask') and state.your_territory_mask.size > 0:
            map_feat[:, :, 0] = self._downsample(state.your_territory_mask)

        # Channel 1: Enemy density (aggregate all opponents)
        if hasattr(state, 'enemy_count_map') and state.enemy_count_map.size > 0:
            max_enemies = max(self.num_bots, 1)
            map_feat[:, :, 1] = self._downsample(state.enemy_count_map / max_enemies)

        # Channel 2: Neutral territory
        if hasattr(state, 'neutral_mask') and state.neutral_mask.size > 0:
            map_feat[:, :, 2] = self._downsample(state.neutral_mask)

        # Channel 3: Your troops
        if hasattr(state, 'your_troops') and state.your_troops.size > 0:
            map_feat[:, :, 3] = self._downsample(state.your_troops / 10000.0)

        # Channel 4: Enemy troops (aggregated)
        if hasattr(state, 'enemy_troops') and state.enemy_troops.size > 0:
            map_feat[:, :, 4] = self._downsample(state.enemy_troops / 10000.0)

        return map_feat

    def _downsample(self, array_512: np.ndarray) -> np.ndarray:
        """
        Downsample from 512×512 to 128×128 using 4×4 average pooling.

        Args:
            array_512: Input array (512, 512) or (128, 128)

        Returns:
            Downsampled array (128, 128)
        """
        if array_512.shape == (128, 128):
            return array_512

        if array_512.shape[0] < 128 or array_512.shape[1] < 128:
            # Pad if too small
            padded = np.zeros((512, 512), dtype=array_512.dtype)
            padded[:array_512.shape[0], :array_512.shape[1]] = array_512
            array_512 = padded

        # Simple 4×4 average pooling
        try:
            return array_512.reshape(128, 4, 128, 4).mean(axis=(1, 3))
        except ValueError:
            # Fallback: use simple strided slicing
            return array_512[::4, ::4]

    def _extract_global(self, state) -> np.ndarray:
        """
        Extract 16 global features from game state.

        Features:
        0: Population / max_population
        1: Max population / 100000
        2: Population growth rate
        3: Territory percentage
        4: Territory change (last 10 steps)
        5: Rank / 50
        6: Border pressure / 10
        7: Troops per tile ratio (CRITICAL for consolidation!)
        8: Territory momentum (expansion/contraction rate)
        9: Time alive / max_time
        10: Game progress
        11: Nearest threat / 128
        12: Recent attack intensity (aggression level)
        13: Multi-front indicator (number of active fronts)
        14: Rank position (percentile, 1.0=winning)
        15: Overextension flag (0.0-1.0, higher=worse)

        Returns:
            Global features array [16]
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

        # Feature 7: Troops per tile ratio (CRITICAL for consolidation!)
        if hasattr(state, 'population') and hasattr(state, 'tiles_owned') and state.tiles_owned > 0:
            troops_per_tile = state.population / state.tiles_owned
            features[7] = troops_per_tile / 50.0  # Normalize (50 = strong density)

        # Feature 8: Territory momentum (rate of change)
        if hasattr(self, 'previous_state') and self.previous_state is not None:
            if hasattr(state, 'territory_pct') and hasattr(self.previous_state, 'territory_pct'):
                territory_momentum = state.territory_pct - self.previous_state.territory_pct
                features[8] = territory_momentum * 100  # Scale up small changes

        # Survival
        if hasattr(state, 'time_alive') and hasattr(state, 'max_time'):
            features[9] = state.time_alive / max(state.max_time, 1)

        # Game phase
        if hasattr(state, 'game_progress'):
            features[10] = state.game_progress

        # Threats
        if hasattr(state, 'nearest_threat'):
            features[11] = state.nearest_threat / 128.0

        # Feature 12: Recent attack intensity (how aggressive we've been)
        if hasattr(self, 'recent_attack_directions') and len(self.recent_attack_directions) > 0:
            features[12] = len(self.recent_attack_directions) / 10.0  # Normalize by max history

        # Feature 13: Multi-front indicator (fighting multiple wars?)
        if hasattr(self, 'recent_attack_directions') and len(self.recent_attack_directions) >= 5:
            unique_fronts = len(set(self.recent_attack_directions[-5:]))
            features[13] = unique_fronts / 8.0  # Normalize by max directions

        # Feature 14: Rank position indicator (winning/losing?)
        if hasattr(state, 'rank') and hasattr(state, 'total_players'):
            rank_percentile = state.rank / max(state.total_players, 1)
            features[14] = 1.0 - rank_percentile  # 1.0 = rank 1, 0.0 = last place

        # Feature 15: Overextension indicator (computed explicitly)
        if hasattr(state, 'population') and hasattr(state, 'tiles_owned') and state.tiles_owned > 0:
            troops_per_tile = state.population / state.tiles_owned
            if hasattr(state, 'territory_pct') and state.territory_pct > 0.20:
                if troops_per_tile < 15:
                    # Flag overextension
                    features[15] = (15 - troops_per_tile) / 15.0  # 0.0-1.0, higher = worse
                else:
                    features[15] = 0.0  # Not overextended
            else:
                features[15] = 0.0  # Early game, can't be overextended yet

        return features

    def _execute_action(self, direction: int, intensity_idx: int):
        """
        Execute action in game.

        Args:
            direction: Direction index (0-8)
            intensity_idx: Intensity level index (0-4)
        """
        if self.game is None:
            return

        # Get intensity percentage
        intensity = self.intensities[intensity_idx]

        # Attack in direction
        if direction < 8:  # Not waiting
            target = self._find_target_in_direction(direction)
            if target is not None:
                troops = int(self.game.get_population() * intensity)
                if troops > 0:
                    self.game.attack(target, troops)

    def _find_target_in_direction(self, direction: int):
        """
        Find target tile in given direction.

        Args:
            direction: Direction index (0-7 for N, NE, E, SE, S, SW, W, NW)

        Returns:
            Target location or None
        """
        # Direction vectors: N, NE, E, SE, S, SW, W, NW
        dx_map = [0, 1, 1, 1, 0, -1, -1, -1]
        dy_map = [-1, -1, 0, 1, 1, 1, 0, -1]

        # This would need to be implemented based on actual game interface
        # For now, return None
        return None

    def _find_safe_location(self):
        """Find safe interior location for building city"""
        # This would need to be implemented based on actual game interface
        return None

    def _compute_reward(self) -> float:
        """
        Compute reward based on state changes.

        REWARD STRUCTURE (adapted from Phase 1-2 proven design):
        =========================================================
        Focus on ACTIONS and CHANGES, not just survival.

        Per-step rewards:
        - Territory change: ±5 per 1% gained/lost
        - Action bonus: +0.5 for non-WAIT actions (encourages exploration!)
        - Kill bonus: +5000 per enemy eliminated
        - Military strength: +1.0 if stronger than average enemy
        - Time penalty: -0.1 per step (encourage efficiency)

        Terminal rewards:
        - Victory (80%+ territory): +10,000
        - Defeat (eliminated): -10,000
        - Timeout: -5,000

        Returns:
            Reward value
        """
        if self.game is None or self.previous_state is None:
            return 0.1  # Initial reward

        state = self._get_game_state()
        prev = self.previous_state

        reward = 0.0

        # 1. TERRITORY CHANGE (reduced to balance with consolidation)
        if hasattr(state, 'territory_pct') and hasattr(prev, 'territory_pct'):
            territory_change = state.territory_pct - prev.territory_pct
            # Reward per 1% territory change: ±2 (reduced from ±5)
            reward += territory_change * 100 * 2

            # CATASTROPHIC LOSS PENALTY (exponential punishment for massive losses)
            if territory_change < -0.05:  # Lost more than 5% territory
                # Additional penalty that scales with severity
                loss_magnitude = abs(territory_change)
                catastrophic_penalty = -(loss_magnitude ** 2) * 5000
                reward += catastrophic_penalty
                # Examples:
                # Lose 5%: -1250 extra
                # Lose 10%: -5000 extra
                # Lose 20%: -20000 extra (DEVASTATING!)

        # 2. ACTION BONUS (reduced to encourage patience)
        #    Only attack when very strong, otherwise waiting is better
        if not self.last_action_was_wait:
            if hasattr(state, 'population') and state.population > 5000:
                reward += 0.1  # Much smaller, only when very strong (was 0.3@3000)

        # 3. TROOP DENSITY REWARD (STRENGTHENED - consolidation is critical!)
        #    Based on real game data: Leader had 21.6 troops/tile, 2nd had 53.8
        #    Sweet spot is 15-35 troops/tile (aggressive expansion that works)
        if hasattr(state, 'population') and hasattr(state, 'tiles_owned'):
            if state.tiles_owned > 0:
                troops_per_tile = state.population / state.tiles_owned

                if 15 <= troops_per_tile <= 35:
                    reward += 5.0  # Optimal range - 2.5x stronger (was 2.0)
                elif troops_per_tile > 60:
                    reward -= 1.0  # Too defensive (like losing 2nd place)
                elif troops_per_tile < 8:
                    reward -= 10.0  # Way too thin - MUCH stronger penalty (was -3.0)

        # 4. OVEREXTENSION PENALTY (NEW - prevent expand-and-die)
        #    Heavily penalize having lots of territory but spreading too thin
        if hasattr(state, 'territory_pct') and hasattr(state, 'population') and hasattr(state, 'tiles_owned'):
            if state.tiles_owned > 0:
                troops_per_tile = state.population / state.tiles_owned

                # CRITICAL: If you have lots of territory but spread too thin
                if state.territory_pct > 0.20 and troops_per_tile < 15:
                    # Exponential penalty for being overextended
                    overextension_factor = (15 - troops_per_tile) / 15  # 0.0 to 1.0
                    overextension_penalty = -overextension_factor * 1000
                    reward += overextension_penalty
                    # Examples:
                    # 25% territory with 10 troops/tile: -333 penalty
                    # 40% territory with 8 troops/tile: -466 penalty
                    # 45% territory with 5 troops/tile: -666 penalty (disaster!)

        # 5. TROOP LOSS PENALTY (discourage reckless attacks)
        #    Penalize losing troops without gaining territory
        if hasattr(state, 'population') and hasattr(prev, 'population'):
            troop_change = state.population - prev.population

            # Heavy penalty for losing lots of troops
            if troop_change < -2000:
                reward += troop_change / 500.0  # -4.0 for losing 2000 troops

        # 5. ENEMY KILL BONUS (eliminates opponents)
        #    Significant reward for eliminating enemy players
        if hasattr(prev, 'rank') and hasattr(state, 'rank'):
            # If rank improved by more than 1, likely killed an enemy
            # (Note: This is approximate - ideally game bridge would track kills)
            if state.rank < prev.rank - 1:
                enemies_killed = prev.rank - state.rank
                reward += enemies_killed * 5000

        # 6. MILITARY STRENGTH BONUS (battle royale - stay strong!)
        #    Reward for maintaining strong army relative to enemies
        if hasattr(state, 'population') and hasattr(state, 'max_population'):
            agent_troops = state.population
            # Estimate average enemy troops
            # In battle royale, if we're rank 5/50, there are ~49 enemies
            if hasattr(state, 'rank') and hasattr(state, 'total_players'):
                num_enemies = state.total_players - 1
                # Rough estimate: assume enemies have similar populations
                # If we're top half, reward military strength
                if state.rank <= state.total_players // 2:
                    reward += 1.0

        # 7. FOCUS BONUS / MULTI-FRONT PENALTY
        #    Reward focusing on one front, penalize fighting multiple wars
        if len(self.recent_attack_directions) >= 5:  # Need at least 5 recent attacks
            unique_directions = len(set(self.recent_attack_directions[-5:]))

            if unique_directions == 1:
                reward += 1.5  # Focusing on ONE front - excellent!
            elif unique_directions == 2:
                reward += 0.5  # Two fronts - acceptable
            elif unique_directions >= 4:
                reward -= 2.0  # Fighting 4+ wars simultaneously - BAD!

        # 8. SURVIVAL BONUS (reward staying alive longer)
        #    Encourages agent to prioritize survival over reckless expansion
        if self.step_count > 0:
            survival_bonus = self.step_count / 10000.0  # +0.1 per 1000 steps
            reward += survival_bonus

            # Extra bonus for reaching milestones
            if self.step_count == 500:
                reward += 50  # Survived early game
            elif self.step_count == 1500:
                reward += 100  # Survived mid game
            elif self.step_count == 3000:
                reward += 200  # Late game master

        # 9. RANK IMPROVEMENT REWARD (stay competitive)
        #    Reward improving rank (moving up the leaderboard = survival strategy)
        if hasattr(state, 'rank') and hasattr(prev, 'rank'):
            if state.rank < prev.rank:  # Rank improved (lower = better)
                rank_improvement = prev.rank - state.rank
                reward += rank_improvement * 100  # +100 per rank gained

        # 10. RANK DEFENSE BONUS (NEW - hold winning position!)
        #     When you're winning, maintaining lead is more important than risky expansion
        if hasattr(state, 'rank') and hasattr(state, 'territory_pct'):
            if state.rank == 1 and state.territory_pct > 0.30:
                # You're in winning position - defend it!
                if hasattr(prev, 'territory_pct'):
                    if state.territory_pct >= prev.territory_pct:
                        # Holding or gaining when rank 1 = excellent
                        reward += 5.0
                    elif state.territory_pct < prev.territory_pct - 0.02:
                        # Losing >2% territory when rank 1 = BAD
                        reward -= 10.0

        # 11. DEFENSIVE WAIT BONUS (reward patience when vulnerable)
        #    If weak or under pressure, waiting is smart survival
        if self.last_action_was_wait:
            if hasattr(state, 'population'):
                # Reward waiting when army is small (rebuilding)
                if state.population < 5000:
                    reward += 1.0  # Good decision to wait and rebuild

        # 12. TERRITORY MILESTONE BONUSES (NEW - reward holding strategic thresholds)
        #     Incentivizes achieving AND maintaining key territory percentages
        if hasattr(state, 'territory_pct'):
            if state.territory_pct >= 0.30:
                reward += 2.0  # Bonus for holding 30%+ (strong position)
            if state.territory_pct >= 0.40:
                reward += 3.0  # Extra bonus for holding 40%+ (dominating)
            if state.territory_pct >= 0.50:
                reward += 5.0  # Major bonus for holding 50%+ (winning position)

        # 13. SMALL TIME PENALTY (encourage efficiency, but survival > speed)
        reward += -0.05  # Reduced from -0.1 (less pressure to rush)

        # 14. TERMINAL REWARDS (scaled to be meaningful!)
        if hasattr(state, 'territory_pct'):
            if state.territory_pct >= 0.80:
                # Victory!
                reward += 10000
            elif state.territory_pct == 0.0:
                # Eliminated
                reward += -10000

        # 15. TIMEOUT PENALTY
        if self.step_count >= 10000 and not hasattr(state, 'game_over'):
            reward += -5000

        return reward

    def _check_done(self) -> bool:
        """
        Check if episode should terminate.

        Returns:
            True if episode is done
        """
        if self.game is None:
            return False

        state = self._get_game_state()

        if state is None:
            return False

        # Win condition: 80% territory
        if hasattr(state, 'territory_pct') and state.territory_pct >= 0.80:
            logger.info("Episode ended: Victory!")
            return True

        # Loss condition: eliminated (0% territory)
        if hasattr(state, 'territory_pct') and state.territory_pct == 0.0:
            logger.info("Episode ended: Eliminated")
            return True

        # Max steps
        if self.step_count >= 10000:
            logger.info("Episode ended: Max steps reached")
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
