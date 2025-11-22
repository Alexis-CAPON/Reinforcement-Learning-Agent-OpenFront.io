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

        # Territory clusters (for disconnected territories)
        self.clusters = data.get('clusters', [])

        # Economic features
        self.cities_count = data.get('cities_count', 0)
        self.ports_count = data.get('ports_count', 0)
        self.silos_count = data.get('silos_count', 0)
        self.sam_launchers_count = data.get('sam_launchers_count', 0)
        self.defense_posts_count = data.get('defense_posts_count', 0)
        self.factories_count = data.get('factories_count', 0)

        # Military features
        self.atom_bombs_available = data.get('atom_bombs_available', 0)
        self.hydrogen_bombs_available = data.get('hydrogen_bombs_available', 0)
        self.can_launch_nuke = data.get('can_launch_nuke', False)

        # Building capabilities
        self.can_build_city = data.get('can_build_city', False)
        self.can_build_port = data.get('can_build_port', False)
        self.can_build_silo = data.get('can_build_silo', False)
        self.can_build_sam = data.get('can_build_sam', False)

        # Unit positions for spatial observations
        self.our_cities_positions = data.get('our_cities_positions', [])
        self.our_ports_positions = data.get('our_ports_positions', [])
        self.our_silos_positions = data.get('our_silos_positions', [])
        self.our_sam_positions = data.get('our_sam_positions', [])
        self.our_defense_positions = data.get('our_defense_positions', [])
        self.our_factories_positions = data.get('our_factories_positions', [])
        self.enemy_buildings_positions = data.get('enemy_buildings_positions', [])

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

            # Check for failures
            if not response.get('success', False):
                error = response.get('error', 'Unknown error')
                command_type = command.get('type', '')

                # Expected failures for build/nuke actions (not enough resources, etc.)
                # These are normal game states, not errors
                if command_type in ['build_unit', 'launch_nuke']:
                    logger.debug(f"{command_type} action failed: {error}")
                    return response  # Return response with success=false, caller handles it

                # Actual errors for other command types
                logger.error(f"Game bridge error for {command_type}: {error}")
                raise RuntimeError(f"Game bridge error: {error}")

            return response

        except RuntimeError:
            # Re-raise RuntimeError (already logged above or actual communication issue)
            raise
        except Exception as e:
            # Log other exceptions (JSON parsing, I/O errors, etc.)
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

    def attack(self, direction: int, troops_pct: float = None, troops: int = None) -> bool:
        """
        Attack in direction with specified troops or percentage.

        Args:
            direction: Direction index (0-8 for N, NE, E, SE, S, SW, W, NW, WAIT)
            troops_pct: Percentage of troops to send (0.0-1.0)
            troops: Absolute number of troops (alternative to troops_pct)

        Returns:
            True if attack executed successfully
        """
        if troops_pct is None and troops is None:
            return False

        # Calculate intensity
        if troops_pct is not None:
            intensity = troops_pct
        else:
            state = self.get_state()
            if state.population == 0:
                return False
            intensity = troops / state.population

        response = self._send_command({
            'type': 'attack_direction',
            'direction': direction,
            'intensity': intensity
        })

        return response.get('success', False)

    def attack_cluster(self, cluster_id: int, direction: int, troops_pct: float) -> bool:
        """
        Attack from specific cluster in direction with specified troops percentage.

        NEW: Cluster-aware attack for disconnected territories.

        Args:
            cluster_id: Which cluster to attack from (0-4)
            direction: Direction index (0-8 for N, NE, E, SE, S, SW, W, NW, WAIT)
            troops_pct: Percentage of cluster's troops to send (0.0-1.0)

        Returns:
            True if attack executed successfully
        """
        response = self._send_command({
            'type': 'attack_direction',
            'cluster_id': cluster_id,
            'direction': direction,
            'intensity': troops_pct
        })

        return response.get('success', False)

    def build_unit(self, unit_type: str, tile_x: float, tile_y: float) -> bool:
        """
        Build a unit (City, Port, Silo, SAM Launcher, Defense Post, Factory).

        Args:
            unit_type: Type of unit to build
            tile_x: Normalized X coordinate (0.0-1.0)
            tile_y: Normalized Y coordinate (0.0-1.0)

        Returns:
            True if unit built successfully
        """
        response = self._send_command({
            'type': 'build_unit',
            'unit_type': unit_type,
            'tile_x': tile_x,
            'tile_y': tile_y
        })
        return response.get('success', False)

    def launch_nuke(self, nuke_type: str, tile_x: float, tile_y: float) -> bool:
        """
        Launch a nuclear weapon (Atom Bomb or Hydrogen Bomb).

        Args:
            nuke_type: Type of nuke ('Atom Bomb' or 'Hydrogen Bomb')
            tile_x: Normalized X coordinate (0.0-1.0)
            tile_y: Normalized Y coordinate (0.0-1.0)

        Returns:
            True if nuke launched successfully
        """
        response = self._send_command({
            'type': 'launch_nuke',
            'nuke_type': nuke_type,
            'tile_x': tile_x,
            'tile_y': tile_y
        })
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
