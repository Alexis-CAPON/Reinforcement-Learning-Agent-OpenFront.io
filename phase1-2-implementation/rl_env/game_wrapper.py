"""
Game Wrapper: Python interface to TypeScript game engine

This module manages the subprocess communication with the Node.js game bridge.
"""

import subprocess
import json
import os
import sys
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GameWrapper:
    """
    Wrapper for OpenFront.io game engine.
    Communicates with Node.js process via JSON over stdin/stdout.
    """

    def __init__(self, map_name: str = 'plains', difficulty: str = 'easy', tick_interval_ms: int = 100, num_players: int = 6):
        """
        Initialize game wrapper.

        Args:
            map_name: Name of the map to load
            difficulty: AI difficulty (Easy, Medium, Hard, Impossible)
            tick_interval_ms: Game tick interval in milliseconds (default 100ms)
                              Lower values = faster simulation (e.g., 10ms = 10× speedup)
            num_players: Total number of players (1 RL agent + N-1 AI bots)
        """
        self.map_name = map_name
        self.difficulty = difficulty
        self.tick_interval_ms = tick_interval_ms
        self.num_players = num_players
        self.process: Optional[subprocess.Popen] = None
        self._start_game_process()

    def _start_game_process(self):
        """Start the Node.js game bridge process"""
        # Path to TypeScript bridge (using tsx to run directly, no compilation needed)
        bridge_path = os.path.join(
            os.path.dirname(__file__),
            '../game_bridge/game_bridge_cached.ts'
        )

        if not os.path.exists(bridge_path):
            raise FileNotFoundError(
                f"Game bridge not found at {bridge_path}"
            )

        # Base game directory for module resolution
        base_game_dir = os.path.join(
            os.path.dirname(__file__),
            '../../base-game'
        )

        logger.info(f"Starting game process: {bridge_path}")
        logger.info(f"Working directory: {base_game_dir}")

        self.process = subprocess.Popen(
            ['npx', 'tsx', bridge_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=base_game_dir
        )

        logger.info("Game process started (first reset will be slow ~0.3s, then fast!)")

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to game process and get response.

        Args:
            command: Command dictionary

        Returns:
            Response dictionary
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("Game process not initialized")

        try:
            # Send command
            command_str = json.dumps(command) + '\n'
            self.process.stdin.write(command_str)
            self.process.stdin.flush()

            # Read response
            response_str = self.process.stdout.readline()
            if not response_str:
                # Check if process died
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read()
                    raise RuntimeError(f"Game process died. Stderr: {stderr}")
                raise RuntimeError("Game process closed unexpectedly")

            response = json.loads(response_str)

            # Check for error response
            if response.get('type') == 'error':
                error = response.get('message', 'Unknown error')
                raise RuntimeError(f"Game command failed: {error}")

            return response

        except Exception as e:
            logger.error(f"Command failed: {command}, Error: {e}")
            raise

    def reset(self) -> Dict[str, Any]:
        """
        Reset game to initial state.

        Returns:
            Initial game state
        """
        logger.debug(f"Resetting game: map={self.map_name}, difficulty={self.difficulty}, tick_interval={self.tick_interval_ms}ms, players={self.num_players}")

        response = self._send_command({
            'type': 'reset',
            'map_name': self.map_name,
            'difficulty': self.difficulty,
            'tick_interval': self.tick_interval_ms,
            'num_players': self.num_players
        })

        return response['state']

    def tick(self) -> Dict[str, Any]:
        """
        Execute one game tick.

        Returns:
            Updated game state
        """
        response = self._send_command({
            'type': 'tick'
        })

        return response['state']

    def get_state(self, player_id: int = 1) -> Dict[str, Any]:
        """
        Get current game state for a player.

        Args:
            player_id: Player ID (not used in current bridge - always returns RL player's state)

        Returns:
            Game state dictionary
        """
        response = self._send_command({
            'type': 'get_state'
        })

        return response['state']

    def get_attackable_neighbors(self, player_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get list of attackable neighbor tiles.

        Args:
            player_id: Player ID (not used in current bridge - always returns RL player's neighbors)

        Returns:
            List of neighbor dictionaries with keys:
                - neighbor_idx: Index (0-7)
                - enemy_player_id: Enemy player ID
                - tile_x: X coordinate
                - tile_y: Y coordinate
                - enemy_troops: Enemy troop count
        """
        response = self._send_command({
            'type': 'get_attackable_neighbors'
        })

        return response['neighbors']

    def attack_tile(self, player_id: int, tile_x: int, tile_y: int, attack_percentage: float = 0.5):
        """
        Execute attack on specific tile.

        Args:
            player_id: Player ID (not used in current bridge - always RL player attacks)
            tile_x: Target tile X coordinate
            tile_y: Target tile Y coordinate
            attack_percentage: Percentage of troops to send (0.0-1.0), default 0.5
        """
        self._send_command({
            'type': 'attack_tile',
            'tile_x': tile_x,
            'tile_y': tile_y,
            'attack_percentage': attack_percentage
        })

    def ai_step(self, player_id: int = 2):
        """
        Let AI player take its turn.

        Note: In the current bridge, AI moves automatically during game ticks.
        This method is kept for compatibility but does nothing.

        Args:
            player_id: AI player ID
        """
        # AI moves automatically in the game - no explicit command needed
        pass

    def close(self):
        """Shutdown game process"""
        if self.process:
            logger.info("Closing game process")
            try:
                self._send_command({'type': 'shutdown'})
            except:
                pass

            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    def __del__(self):
        """Cleanup on deletion"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Test functionality
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Testing GameWrapper...")

    with GameWrapper(map_name='plains', difficulty='easy') as game:
        # Reset game
        print("\n1. Resetting game...")
        state = game.reset()
        print(f"Initial state: tiles={state['tiles_owned']}, troops={state['troops']}")

        # Get neighbors
        print("\n2. Getting attackable neighbors...")
        neighbors = game.get_attackable_neighbors(player_id=1)
        print(f"Found {len(neighbors)} attackable neighbors")
        for n in neighbors[:3]:
            print(f"  - Neighbor {n['neighbor_idx']}: tile ({n['tile_x']}, {n['tile_y']})")

        # Execute a few ticks
        print("\n3. Running 5 game ticks...")
        for i in range(5):
            state = game.tick()
            print(f"  Tick {i+1}: tiles={state['tiles_owned']}, troops={state['troops']:.0f}")

    print("\nTest complete!")
