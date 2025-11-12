"""
Game Wrapper for Phase 3 - Python interface to TypeScript game bridge

Handles IPC communication between Python and Node.js game engine.
"""

import subprocess
import json
import logging
import os
import signal
import time
from typing import Optional, Dict, Any, Tuple
import numpy as np
import atexit

logger = logging.getLogger(__name__)


class GameState:
    """Container for game state"""

    def __init__(self, data: Dict[str, Any]):
        # Core state
        self.tick = data.get('tick', 0)
        self.game_over = data.get('game_over', False)
        self.has_won = data.get('has_won', False)
        self.has_lost = data.get('has_lost', False)

        # Territory
        self.tiles_owned = data.get('tiles_owned', 0)
        self.total_tiles = data.get('total_tiles', 1)
        self.territory_pct = data.get('territory_pct', 0.0)
        self.neutral_tiles = data.get('neutral_tiles', 0)

        # Population
        self.population = data.get('population', 0)
        self.max_population = data.get('max_population', 1)
        self.population_growth_rate = data.get('population_growth_rate', 0.0)

        # Resources
        self.gold = data.get('gold', 0)
        self.num_cities = data.get('num_cities', 0)

        # Position
        self.rank = data.get('rank', 1)
        self.total_players = data.get('total_players', 1)
        self.alive_players = data.get('alive_players', 1)

        # Spatial data (512×512)
        self.territory_map = np.array(data.get('territory_map', []), dtype=np.int32)
        self.troop_map = np.array(data.get('troop_map', []), dtype=np.float32)

        # Global features
        self.border_tiles = data.get('border_tiles', 0)
        self.border_pressure = data.get('border_pressure', 0.0)
        self.time_alive = data.get('time_alive', 0)
        self.nearest_threat = data.get('nearest_threat_distance', 999.0)
        self.territory_change = data.get('territory_change', 0.0)

        # Compute derived features
        self._compute_derived_features()

    def _compute_derived_features(self):
        """Compute features for RL observation"""
        # Create masks from territory map
        if self.territory_map.size > 0:
            self.your_territory_mask = (self.territory_map == 1).astype(np.float32)
            self.enemy_count_map = (self.territory_map > 1).astype(np.float32)
            self.neutral_mask = (self.territory_map == 0).astype(np.float32)
        else:
            # Default empty maps
            self.your_territory_mask = np.zeros((512, 512), dtype=np.float32)
            self.enemy_count_map = np.zeros((512, 512), dtype=np.float32)
            self.neutral_mask = np.zeros((512, 512), dtype=np.float32)

        # Troop distributions (placeholder - actual game may have this data)
        self.your_troops = np.zeros_like(self.your_territory_mask)
        self.enemy_troops = np.zeros_like(self.enemy_count_map)

        # Game progress (normalized time)
        self.game_progress = min(self.time_alive / 10000.0, 1.0)

        # Max time (for normalization)
        self.max_time = 50000


class GameWrapper:
    """
    Python wrapper for TypeScript game bridge.

    Communicates via JSON over stdin/stdout with Node.js process.
    """

    def __init__(
        self,
        map_name: str = 'plains',
        num_players: int = 50,
        game_bridge_path: Optional[str] = None
    ):
        """
        Initialize game wrapper.

        Args:
            map_name: Name of map to use
            num_players: Total number of players (including RL agent)
            game_bridge_path: Path to game_bridge.ts (auto-detected if None)
        """
        self.map_name = map_name
        self.num_players = num_players

        # Find game bridge
        if game_bridge_path is None:
            game_bridge_path = os.path.join(
                os.path.dirname(__file__),
                '../game_bridge/game_bridge.ts'
            )

        self.game_bridge_path = os.path.abspath(game_bridge_path)

        if not os.path.exists(self.game_bridge_path):
            raise FileNotFoundError(f"Game bridge not found: {self.game_bridge_path}")

        self.process: Optional[subprocess.Popen] = None
        self.current_state: Optional[GameState] = None

        # Start game bridge process
        self._start_bridge()

        # Register cleanup
        atexit.register(self.close)

        logger.info(f"GameWrapper initialized: map={map_name}, players={num_players}")

    def _start_bridge(self):
        """Start TypeScript game bridge process"""
        logger.info(f"Starting game bridge: {self.game_bridge_path}")

        # Start Node.js process with tsx
        self.process = subprocess.Popen(
            ['npx', 'tsx', self.game_bridge_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            cwd=os.path.dirname(self.game_bridge_path)
        )

        # Wait a bit for process to start
        time.sleep(0.5)

        if self.process.poll() is not None:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"Game bridge failed to start: {stderr}")

        logger.info("Game bridge process started")

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to game bridge and get response.

        Args:
            command: Command dictionary

        Returns:
            Response dictionary

        Raises:
            RuntimeError: If communication fails
        """
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Game bridge process not running")

        try:
            # Send command
            command_json = json.dumps(command) + '\n'
            self.process.stdin.write(command_json)
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()

            if not response_line:
                raise RuntimeError("No response from game bridge")

            response = json.loads(response_line)

            if not response.get('success', False):
                error = response.get('error', 'Unknown error')
                raise RuntimeError(f"Game bridge error: {error}")

            return response

        except Exception as e:
            logger.error(f"Communication error: {e}")
            raise

    def start_new_game(self, num_bots: Optional[int] = None):
        """
        Start new game (reset).

        Args:
            num_bots: Number of bot opponents (total players = num_bots + 1)
        """
        if num_bots is not None:
            self.num_players = num_bots + 1

        logger.info(f"Starting new game: {self.num_players} players")

        response = self._send_command({
            'type': 'reset',
            'map_name': self.map_name,
            'num_players': self.num_players
        })

        state_data = response.get('state', {})
        self.current_state = GameState(state_data)

        logger.info(f"Game started at tick {self.current_state.tick}")

    def update(self):
        """Execute one game tick"""
        response = self._send_command({'type': 'tick'})

        state_data = response.get('state', {})
        self.current_state = GameState(state_data)

    def get_state(self) -> GameState:
        """Get current game state"""
        if self.current_state is None:
            response = self._send_command({'type': 'get_state'})
            state_data = response.get('state', {})
            self.current_state = GameState(state_data)

        return self.current_state

    def get_population(self) -> int:
        """Get current population"""
        state = self.get_state()
        return state.population

    def attack(self, direction: int, troops: int) -> bool:
        """
        Attack in direction with specified troops.

        Args:
            direction: Direction index (0-7 for N, NE, E, SE, S, SW, W, NW)
            troops: Number of troops to send

        Returns:
            True if attack executed successfully
        """
        if troops <= 0:
            return False

        state = self.get_state()
        if state.population < troops:
            return False

        intensity = troops / state.population

        response = self._send_command({
            'type': 'attack_direction',
            'direction': direction,
            'intensity': intensity
        })

        return response.get('success', False)

    def can_build_city(self) -> bool:
        """Check if can build city"""
        state = self.get_state()
        CITY_COST = 5000
        return state.gold >= CITY_COST

    def build_city(self, location: Optional[Tuple[int, int]] = None) -> bool:
        """
        Build city at location.

        Args:
            location: (x, y) coordinates (currently ignored, bridge finds location)

        Returns:
            True if city built successfully
        """
        response = self._send_command({'type': 'build_city'})
        return response.get('success', False)

    def close(self):
        """Close game bridge and cleanup"""
        if self.process is not None:
            logger.info("Closing game bridge")

            try:
                # Send shutdown command
                self._send_command({'type': 'shutdown'})
                self.process.wait(timeout=2)
            except Exception:
                # Force kill if needed
                self.process.kill()
                self.process.wait()

            self.process = None

        logger.info("Game wrapper closed")

    def __del__(self):
        """Destructor - ensure cleanup"""
        self.close()


# Test harness
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing GameWrapper...")
    print("=" * 60)

    # Create wrapper
    print("\n1. Creating game wrapper...")
    wrapper = GameWrapper(map_name='plains', num_players=6)
    print("   ✓ Wrapper created")

    # Start game
    print("\n2. Starting new game...")
    wrapper.start_new_game()
    state = wrapper.get_state()
    print(f"   ✓ Game started")
    print(f"   Tick: {state.tick}")
    print(f"   Territory: {state.tiles_owned} tiles ({state.territory_pct:.1%})")
    print(f"   Population: {state.population} / {state.max_population}")

    # Test a few ticks
    print("\n3. Running 10 ticks...")
    for i in range(10):
        wrapper.update()
        state = wrapper.get_state()
        print(f"   Tick {state.tick}: "
              f"tiles={state.tiles_owned}, "
              f"pop={state.population}, "
              f"rank={state.rank}/{state.total_players}")

    # Test state features
    print("\n4. Checking state features...")
    print(f"   Territory map shape: {state.territory_map.shape}")
    print(f"   Your territory mask: {state.your_territory_mask.shape}")
    print(f"   Enemy density map: {state.enemy_count_map.shape}")
    print(f"   Border tiles: {state.border_tiles}")
    print(f"   Border pressure: {state.border_pressure}")
    print(f"   Nearest threat: {state.nearest_threat:.1f}")

    # Close
    print("\n5. Closing wrapper...")
    wrapper.close()
    print("   ✓ Closed")

    print("\n" + "=" * 60)
    print("All tests passed!")
