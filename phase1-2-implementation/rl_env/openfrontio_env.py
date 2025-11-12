"""
OpenFront.io Gymnasium Environment - Phase 1

Features:
- Action masking for dynamic neighbor-based attacks
- Small map (50x50 or existing small map)
- Minimal observation space (5 features)
- Discrete action space (IDLE + 8 neighbor attacks)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Optional, Any, List
import logging
import json
import os

from game_wrapper import GameWrapper

logger = logging.getLogger(__name__)


class OpenFrontIOEnv(gym.Env):
    """
    Phase 1 OpenFront.io Environment with action masking.

    Observation Space:
        Dict with:
        - 'features': Box(5) - [tiles, troops, gold, enemy_tiles, tick]
        - 'action_mask': Box(9) - Binary mask for valid actions

    Action Space:
        Dict with:
        - 'attack_target': Discrete(9) - IDLE (0) or attack neighbor 1-8
        - 'attack_percentage': Box(0, 1) - Percentage of troops to send (0.0-1.0)
    """

    metadata = {'render_modes': []}

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize environment.

        Args:
            config_path: Path to configuration JSON file
        """
        super().__init__()

        # Load configuration
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                '../configs/phase1_config.json'
            )

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Extract config values
        game_config = self.config['game']
        env_config = self.config['environment']
        reward_config = self.config['reward']

        self.map_name = game_config['map_name']
        self.difficulty = game_config['opponent_difficulty']
        self.max_steps = env_config['max_steps']
        self.tick_interval_ms = game_config.get('tick_interval_ms', 100)  # Read from config
        self.num_players = game_config.get('num_players', 6)  # Total players including RL agent

        # Simplified reward config (v1.0.3 - with exploration bonus)
        self.reward_per_tile_change = reward_config.get('per_tile_change', 100)
        self.reward_per_step = reward_config.get('per_step', -0.1)
        self.reward_action_bonus = reward_config.get('action_bonus', 0.5)  # Small bonus for non-IDLE actions
        self.reward_enemy_kill = reward_config.get('enemy_kill_bonus', 5000)
        self.reward_military_strength = reward_config.get('military_strength_bonus', 0.0)  # Bonus for being stronger than enemies
        self.reward_neighbor_strength = reward_config.get('neighbor_strength_bonus', 0.0)  # Bonus for being stronger than neighbors (MOST IMPORTANT)
        self.reward_win = reward_config.get('win_bonus', 10000)
        self.reward_loss = reward_config.get('loss_penalty', -10000)
        self.reward_timeout = reward_config.get('timeout_penalty', -5000)

        # Define spaces
        self.observation_space = spaces.Dict({
            'features': spaces.Box(
                low=-1.0,  # Allow negative for change rates
                high=1.0,
                shape=(12,),  # Expanded: base[5] + strategic[5] + temporal[2]
                dtype=np.float32
            ),
            'action_mask': spaces.Box(
                low=0,
                high=1,
                shape=(9,),
                dtype=np.int8
            ),
            'neighbor_info': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(8, 2),  # 8 neighbors × 2 features (troops, tiles)
                dtype=np.float32
            ),
            'player_info': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(8, 3),  # Max 8 players × 3 features (tiles, troops, is_neighbor)
                dtype=np.float32
            )
        })

        self.action_space = spaces.Dict({
            'attack_target': spaces.Discrete(9),  # 0=IDLE, 1-8=neighbors
            'attack_percentage': spaces.Box(
                low=0.0,
                high=1.0,
                shape=(1,),
                dtype=np.float32
            )
        })

        # Initialize game wrapper
        self.game: Optional[GameWrapper] = None
        self.current_neighbors: List[Dict] = []
        self.step_count = 0
        self.previous_tiles = 0
        self.episode_count = 0

        # Temporal tracking (for change rate features)
        self.history_length = 10  # Track last 10 steps
        self.tiles_history: List[int] = []
        self.troops_history: List[int] = []

        logger.info(f"Environment initialized: map={self.map_name}, difficulty={self.difficulty}, tick_interval={self.tick_interval_ms}ms")

    def _initialize_game(self):
        """Lazy initialization of game wrapper"""
        if self.game is None:
            logger.info("Initializing game wrapper...")
            self.game = GameWrapper(
                map_name=self.map_name,
                difficulty=self.difficulty,
                tick_interval_ms=self.tick_interval_ms,
                num_players=self.num_players
            )

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset environment to initial state.

        Returns:
            observation: Dict with 'features' and 'action_mask'
            info: Additional information
        """
        super().reset(seed=seed)

        # Initialize game if needed
        self._initialize_game()

        # Reset game
        state = self.game.reset()

        # Reset counters
        self.step_count = 0
        self.previous_tiles = state['tiles_owned']
        self.episode_count += 1

        # Reset temporal history
        self.tiles_history = [state['tiles_owned']]
        self.troops_history = [state['troops']]

        logger.debug(f"Episode {self.episode_count} started")

        # Get initial observation
        observation = self._get_observation(state)
        info = self._get_info(state)

        return observation, info

    def step(self, action: int) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        Args:
            action: Dict with 'attack_target' (0-8) and 'attack_percentage' (0.0-1.0)

        Returns:
            observation: New observation
            reward: Reward for this step
            terminated: Whether episode ended (win/loss)
            truncated: Whether episode was truncated (timeout)
            info: Additional information
        """
        if self.game is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        self.step_count += 1

        # Get current state and neighbors
        state_before = self.game.get_state(player_id=1)
        neighbors = self.game.get_attackable_neighbors(player_id=1)
        self.current_neighbors = neighbors

        # Parse action
        attack_target = int(action['attack_target'])
        attack_percentage = float(action['attack_percentage'][0])  # Extract scalar from array

        # Clip percentage to valid range
        attack_percentage = np.clip(attack_percentage, 0.0, 1.0)

        # Validate action target
        action_mask = self._create_action_mask(neighbors)

        if action_mask[attack_target] == 0:
            # Suppress warning - this is expected when model doesn't use action masking
            # The action is safely handled by treating it as IDLE
            logger.debug(f"Invalid action target {attack_target} chosen. Treating as IDLE.")
            attack_target = 0

        # Execute action and track if action was taken
        action_taken = False
        if attack_target == 0 or attack_percentage < 0.01:  # IDLE or negligible percentage
            # IDLE - do nothing
            pass
        else:
            # Attack neighbor with specified percentage
            action_taken = True
            neighbor_idx = attack_target - 1
            if neighbor_idx < len(neighbors):
                neighbor = neighbors[neighbor_idx]
                self.game.attack_tile(
                    player_id=1,
                    tile_x=neighbor['tile_x'],
                    tile_y=neighbor['tile_y'],
                    attack_percentage=attack_percentage
                )
                logger.debug(
                    f"Action: Attack tile ({neighbor['tile_x']}, {neighbor['tile_y']}) "
                    f"with {attack_percentage*100:.1f}% of troops"
                )

        # Let AI take its turn (AI acts automatically during tick)
        # self.game.ai_step(player_id=2)

        # Advance game
        state_after = self.game.tick()

        # Update temporal history
        self.tiles_history.append(state_after['tiles_owned'])
        self.troops_history.append(state_after['troops'])
        if len(self.tiles_history) > self.history_length:
            self.tiles_history.pop(0)
        if len(self.troops_history) > self.history_length:
            self.troops_history.pop(0)

        # Calculate reward
        reward = self._calculate_reward(state_before, state_after, action_taken)

        # Check termination
        terminated = state_after['game_over'] or state_after['has_won'] or state_after['has_lost']

        # Check for stalemate: agent has tiles but no valid attack targets (surrounded/blocked)
        # This prevents episodes from running indefinitely when agent is stuck
        if not terminated and len(neighbors) == 0 and state_after['tiles_owned'] > 0:
            logger.info(f"Stalemate detected at step {self.step_count}: agent has {state_after['tiles_owned']} tiles but no valid neighbors")
            terminated = True
            state_after['has_lost'] = True  # Mark as loss since agent is blocked

        truncated = self.step_count >= self.max_steps and not terminated

        # Debug logging for loss detection (only when tiles hit exactly 0)
        if state_after['tiles_owned'] == 0:
            logger.debug(
                f"Loss detected: tiles=0, has_lost={state_after.get('has_lost')}, "
                f"terminated={terminated}, step={self.step_count}"
            )

        # Get observation
        observation = self._get_observation(state_after)
        info = self._get_info(state_after)

        # Add terminal info
        if terminated or truncated:
            info['episode'] = {
                'r': reward,
                'l': self.step_count,
                'tiles_final': state_after['tiles_owned'],
                'won': state_after['has_won'],
                'lost': state_after.get('has_lost', False),
                'truncated': truncated
            }

            # Determine episode outcome
            if truncated:
                outcome = "TIMEOUT"
            elif state_after['has_won']:
                outcome = "WIN"
            elif state_after.get('has_lost'):
                outcome = "LOSS"
            else:
                outcome = "END"

            # Log episode endings: always log wins, or every 10th episode
            if state_after['has_won'] or self.episode_count % 10 == 0:
                logger.info(
                    f"Episode {self.episode_count} {outcome}: "
                    f"steps={self.step_count}, "
                    f"tiles={state_after['tiles_owned']}, "
                    f"troops={state_after['troops']}, "
                    f"tick={state_after['tick']}, "
                    f"reward={reward:.1f}"
                )

        return observation, reward, terminated, truncated, info

    def _get_observation(self, state: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Extract observation from game state.

        Args:
            state: Game state dictionary

        Returns:
            Observation dict with 'features', 'action_mask', 'neighbor_info', and 'player_info'
        """
        # Get attackable neighbors
        neighbors = self.game.get_attackable_neighbors(player_id=1)

        # Extract base features (normalized to [0, 1])
        base_features = [
            state['tiles_owned'] / 100.0,        # Tiles owned
            state['troops'] / 100000.0,          # Total troops
            state['gold'] / 500000.0,            # Gold
            state['enemy_tiles'] / 100.0,        # Enemy territory
            state['tick'] / self.max_steps       # Time progress
        ]

        # Extract strategic features
        strategic_features = [
            min(state.get('troops_per_tile', 0) / 1000.0, 1.0),         # Our troop density
            min(state.get('avg_enemy_troops_per_tile', 0) / 1000.0, 1.0),  # Enemy troop density
            state.get('border_tile_ratio', 0),                           # Exposure (already 0-1)
            state.get('rank_by_tiles', 0.5),                             # Tile rank (0-1)
            state.get('rank_by_troops', 0.5)                             # Troop rank (0-1)
        ]

        # Extract temporal features (change rates)
        temporal_features = []
        if len(self.tiles_history) >= 2:
            # Calculate change rate over history window
            tiles_change = (self.tiles_history[-1] - self.tiles_history[0]) / max(len(self.tiles_history) - 1, 1)
            troops_change = (self.troops_history[-1] - self.troops_history[0]) / max(len(self.troops_history) - 1, 1)
            # Normalize: assume max change of ±10 tiles or ±10,000 troops per step
            temporal_features = [
                np.clip(tiles_change / 10.0, -1.0, 1.0),
                np.clip(troops_change / 10000.0, -1.0, 1.0)
            ]
        else:
            temporal_features = [0.0, 0.0]  # No history yet

        features = np.array(base_features + strategic_features + temporal_features, dtype=np.float32)
        features = np.clip(features, -1.0, 1.0)

        # Create action mask
        action_mask = self._create_action_mask(neighbors)

        # Extract neighbor info (troops + tiles) aligned with action space 1-8
        neighbor_info = np.zeros((8, 2), dtype=np.float32)
        for i, neighbor in enumerate(neighbors[:8]):  # Max 8 neighbors
            # Column 0: Normalized enemy troops (max ~100,000)
            neighbor_info[i, 0] = min(neighbor.get('enemy_troops', 0) / 100000.0, 1.0)
            # Column 1: Normalized enemy tiles (max ~100)
            neighbor_info[i, 1] = min(neighbor.get('enemy_tiles', 0) / 100.0, 1.0)

        # Extract per-player information (max 8 players)
        player_tiles = state.get('player_tiles', [])
        player_troops = state.get('player_troops', [])
        player_is_neighbor = state.get('player_is_neighbor', [])

        # Create player info matrix (8 players × 3 features)
        player_info = np.zeros((8, 3), dtype=np.float32)
        for i in range(min(len(player_tiles), 8)):
            player_info[i, 0] = min(player_tiles[i] / 100.0, 1.0)      # Tiles (normalized)
            player_info[i, 1] = min(player_troops[i] / 100000.0, 1.0)  # Troops (normalized)
            player_info[i, 2] = float(player_is_neighbor[i]) if i < len(player_is_neighbor) else 0.0

        return {
            'features': features,
            'action_mask': action_mask,
            'neighbor_info': neighbor_info,
            'player_info': player_info
        }

    def _create_action_mask(self, neighbors: List[Dict]) -> np.ndarray:
        """
        Create action mask based on available neighbors.

        Args:
            neighbors: List of attackable neighbors

        Returns:
            Binary mask of shape (9,)
        """
        mask = np.zeros(9, dtype=np.int8)

        # Action 0 (IDLE) is always valid
        mask[0] = 1

        # Mark neighbor attacks as valid (up to 8)
        for i in range(min(len(neighbors), 8)):
            mask[i + 1] = 1

        return mask

    def _calculate_reward(
        self,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        action_taken: bool = False
    ) -> float:
        """
        Calculate reward for this step.

        REWARD STRUCTURE (Phase 1 v1.0.3 / Phase 2):
        =============================================
        Focus on CHANGES (agent's actions) not STATES (accumulated history)

        Per-step rewards (changes only):
        - Tile gained/lost: ±50-100 per tile (Phase 2: 50 to prevent overextension)
        - Action taken: +0.5 (small bonus to encourage exploration)
        - Enemy eliminated: +5000-8000 per player killed (Phase 2: 8000)
        - Military strength (global): +1.0 per step when troops > avg ALL enemy troops (Phase 2)
        - **NEIGHBOR strength: +5.0 per step when troops > neighbor enemy troops / 2** (Phase 2, MOST CRITICAL!)
        - Small time penalty: -0.05 to -0.1 per step

        Terminal rewards:
        - Victory: +10,000-15,000 (Phase 2: 15,000)
        - Defeat: -10,000
        - Timeout: -5,000 to -7,500 (Phase 2: -7,500)

        WHY THESE BONUSES HELP:
        - Action bonus: Encourages exploration, breaks IDLE-only trap
        - Kill bonus: Rewards aggressive play, teaches eliminating opponents
        - Military strength (global): Rewards being stronger than average enemy (strategic overview)
        - **Neighbor strength: CRITICAL - your immediate threat comes from neighbors, not distant players!**
          This is 5x more valuable than global strength to prioritize local defense

        Args:
            state_before: Game state before action
            state_after: Game state after action
            action_taken: Whether a non-IDLE action was taken

        Returns:
            Reward value
        """
        reward = 0.0

        # 1. TILE CHANGES (what the agent directly controls)
        #    Strong immediate feedback for expansion/contraction
        tile_change = state_after['tiles_owned'] - state_before['tiles_owned']
        reward += tile_change * self.reward_per_tile_change

        # 2. ACTION BONUS (encourages exploration)
        #    Small positive reward for taking action (not IDLE)
        if action_taken:
            reward += self.reward_action_bonus

        # 3. ENEMY KILL BONUS (eliminates players)
        #    Significant reward for eliminating enemy players entirely
        enemies_killed = state_after.get('enemies_killed_this_tick', 0)
        if enemies_killed > 0:
            reward += enemies_killed * self.reward_enemy_kill

        # 4. MILITARY STRENGTH BONUS (Phase 2 multi-player - global)
        #    Reward for maintaining strong army relative to ALL enemies
        #    Prevents overextension by encouraging balanced expansion + military power
        if self.reward_military_strength > 0:
            agent_troops = state_after.get('troops', 0)
            enemy_troops = state_after.get('enemy_troops', 0)
            num_enemies = self.num_players - 1  # Total players minus RL agent

            # Reward if agent has more troops than average enemy
            if num_enemies > 0 and enemy_troops > 0:
                avg_enemy_troops = enemy_troops / num_enemies
                if agent_troops > avg_enemy_troops:
                    reward += self.reward_military_strength

        # 5. NEIGHBOR STRENGTH BONUS (Phase 2 multi-player - LOCAL, MOST IMPORTANT!)
        #    Reward for being stronger than NEIGHBORING enemies
        #    This is the CRITICAL reward - your main threat is neighbors, not distant enemies
        if self.reward_neighbor_strength > 0:
            agent_troops = state_after.get('troops', 0)
            neighbor_enemy_troops = state_after.get('neighbor_enemy_troops', 0)

            # Count number of neighboring enemies
            # If we have neighbors, reward being stronger than their average
            if neighbor_enemy_troops > 0:
                # For simplicity, assume we typically have 2-3 neighbors in 8-player game
                # Reward if agent has more troops than the neighbor total divided by reasonable neighbor count
                if agent_troops > neighbor_enemy_troops / 2:  # Stronger than avg of 2 neighbors
                    reward += self.reward_neighbor_strength

        # 6. SMALL TIME PENALTY
        #    Encourages efficiency without dominating the signal
        reward += self.reward_per_step

        # 7. TERMINAL REWARDS (scaled to be meaningful!)
        #    These should be the dominant signal for win/loss
        if state_after['has_won']:
            reward += self.reward_win
        elif state_after['has_lost']:
            reward += self.reward_loss
        elif self.step_count >= self.max_steps and not state_after['game_over']:
            reward += self.reward_timeout

        return reward

    def _get_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get additional info dictionary.

        Args:
            state: Game state

        Returns:
            Info dictionary
        """
        return {
            'step': self.step_count,
            'tiles': state['tiles_owned'],
            'troops': state['troops'],
            'gold': state['gold'],
            'enemy_tiles': state['enemy_tiles'],
            'num_neighbors': len(self.current_neighbors)
        }

    def close(self):
        """Close environment and cleanup resources"""
        if self.game is not None:
            self.game.close()
            self.game = None
        logger.info("Environment closed")


# Test the environment
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Testing OpenFrontIOEnv...")

    env = OpenFrontIOEnv()

    print("\n1. Resetting environment...")
    obs, info = env.reset()
    print(f"Observation features: {obs['features']}")
    print(f"Action mask: {obs['action_mask']}")
    print(f"Valid actions: {np.where(obs['action_mask'] == 1)[0]}")

    print("\n2. Running 10 steps...")
    for i in range(10):
        # Sample random valid action
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)

        obs, reward, terminated, truncated, info = env.step(action)

        print(f"Step {i+1}: action={action}, reward={reward:.1f}, "
              f"tiles={info['tiles']}, terminated={terminated}")

        if terminated or truncated:
            print("Episode ended!")
            break

    print("\n3. Closing environment...")
    env.close()

    print("Test complete!")
