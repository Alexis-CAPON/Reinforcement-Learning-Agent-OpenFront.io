"""
Visual Game Wrapper for Phase 4
Provides full visual state from the game for client rendering
"""

import subprocess
import json
import logging
import os
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class VisualGameWrapper:
    """Wrapper that uses visual game bridge for full state export"""

    def __init__(self, num_bots: int = 10, map_name: str = 'plains', crop: Optional[Dict[str, int]] = None):
        self.num_bots = num_bots
        self.map_name = map_name
        self.crop = crop
        self.process = None
        self.stderr_thread = None
        self._start_visual_bridge()

    def _start_visual_bridge(self):
        """Start the visual game bridge subprocess"""
        bridge_path = os.path.join(
            os.path.dirname(__file__),
            '../game_bridge/game_bridge_visual.ts'
        )

        base_game_dir = os.path.join(
            os.path.dirname(__file__),
            '../../base-game'
        )

        logger.info(f"Starting visual game bridge...")
        self.process = subprocess.Popen(
            ['npx', 'tsx', bridge_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=base_game_dir
        )

        # Start thread to read and print stderr (for [BRIDGE] debug logs)
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_thread.start()

        logger.info("Visual bridge started!")

    def _read_stderr(self):
        """Read stderr from bridge process and print to console"""
        if not self.process or not self.process.stderr:
            return

        try:
            for line in self.process.stderr:
                # Print bridge stderr to Python console (includes spawn coordinates)
                print(f"[BRIDGE_STDERR] {line.rstrip()}")
        except Exception as e:
            logger.debug(f"Stderr thread ended: {e}")

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command and get response"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Bridge not initialized")

        command_str = json.dumps(command) + '\n'
        self.process.stdin.write(command_str)
        self.process.stdin.flush()

        response_str = self.process.stdout.readline()
        if not response_str:
            if self.process.poll() is not None:
                stderr = self.process.stderr.read()
                raise RuntimeError(f"Bridge died. Stderr: {stderr}")
            raise RuntimeError("Bridge closed unexpectedly")

        response = json.loads(response_str)
        if response.get('type') == 'error':
            raise RuntimeError(f"Bridge error: {response.get('message')}")

        return response

    def reset(self):
        """Reset game"""
        command = {
            'type': 'reset',
            'num_bots': self.num_bots,
            'map_name': self.map_name
        }
        if self.crop:
            command['crop'] = self.crop
        return self._send_command(command)

    def tick(self):
        """Execute game tick"""
        return self._send_command({'type': 'tick'})

    def get_visual_state(self):
        """Get full visual state (all tiles, all players)"""
        return self._send_command({'type': 'get_visual_state'})

    def get_full_state_update(self):
        """Get full state as a game update (for initial sync)"""
        response = self.get_visual_state()
        # The visual state already includes everything we need
        return response

    def get_state(self):
        """Get current game state (for RL observations)"""
        response = self.get_visual_state()
        return response.get('state', {})

    def attack_direction(self, direction: str, intensity: float):
        """Execute action in direction"""
        self._send_command({
            'type': 'attack_direction',
            'direction': direction,
            'intensity': intensity
        })

    def close(self):
        """Shutdown bridge"""
        if self.process:
            try:
                self._send_command({'type': 'shutdown'})
            except:
                pass
            self.process.terminate()
            self.process.wait(timeout=5)
