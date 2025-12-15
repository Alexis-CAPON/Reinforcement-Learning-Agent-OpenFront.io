"""
Phase 6 Real-Time Visualizer - Cities Only
Watch your trained MaskablePPO model play with full game visualization

Usage:
    python visualize_cities.py --model models/ppo_cities_20251202_170832/final_model.zip
"""

import sys
import os
import argparse
import asyncio
import json
import time
import websockets
from pathlib import Path
from typing import Optional, Dict, Set
from collections import deque

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environment_cities import OpenFrontEnvCities
import numpy as np


class WebSocketServer:
    """WebSocket server for broadcasting game state to client"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.is_paused = False
        self.speed = 1.0

    async def register(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket):
        """Unregister a client"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True
            )

    async def handler(self, websocket, path):
        """Handle client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                # Handle control messages from client
                try:
                    data = json.loads(message)
                    if data.get('type') == 'control':
                        command = data.get('command')
                        if command == 'pause':
                            self.is_paused = True
                            print("Paused")
                        elif command == 'play':
                            self.is_paused = False
                            print("Playing")
                        elif command == 'speed':
                            self.speed = data.get('speed', 1.0)
                            print(f"Speed: {self.speed}x")
                except Exception as e:
                    print(f"Error handling message: {e}")
        finally:
            await self.unregister(websocket)

    async def start(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    def has_clients(self) -> bool:
        """Check if any clients are connected"""
        return len(self.clients) > 0

    def should_step(self) -> bool:
        """Check if game should step (based on pause state)"""
        return not self.is_paused


class CitiesVisualizer:
    """Real-time visualizer for Phase 6 cities-only model"""

    def __init__(
        self,
        model_path: str,
        num_bots: int = 10,
        map_name: str = 'australia_256x256',
        websocket_host: str = "localhost",
        websocket_port: int = 8765
    ):
        self.model_path = model_path
        self.num_bots = num_bots
        self.map_name = map_name

        # Load model
        print(f"Loading model from {model_path}...")
        self.model = MaskablePPO.load(model_path)
        print(f"✓ Model loaded successfully")

        # Create environment
        print(f"Creating environment: map={map_name}, bots={num_bots}...")
        self.env = OpenFrontEnvCities(
            map_name=map_name,
            num_bots=num_bots,
            frame_stack=4
        )
        print(f"✓ Environment created")

        # WebSocket server
        self.ws_server = WebSocketServer(websocket_host, websocket_port)

        # Game state
        self.cumulative_reward = 0.0
        self.step_count = 0
        self.episode_count = 0

    async def run(self):
        """Run the visualizer"""
        # Start WebSocket server
        await self.ws_server.start()

        print("\n" + "=" * 80)
        print("PHASE 6 CITIES VISUALIZER")
        print("=" * 80)
        print(f"Model: {self.model_path}")
        print(f"Map: {self.map_name}")
        print(f"Opponents: {self.num_bots} bots")
        print(f"WebSocket: ws://{self.ws_server.host}:{self.ws_server.port}")
        print("=" * 80)
        print("\nWaiting for client connection...")
        print("Open the web client and connect to visualize the game")
        print("=" * 80 + "\n")

        # Wait for client to connect
        while not self.ws_server.has_clients():
            await asyncio.sleep(0.5)

        print("Client connected! Starting game...\n")

        # Run episodes continuously
        try:
            while True:
                await self.run_episode()
                self.episode_count += 1

                # Wait a bit between episodes
                print("\nStarting new episode in 3 seconds...")
                await asyncio.sleep(3)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

    async def run_episode(self):
        """Run a single episode with visualization"""
        print(f"\n{'=' * 80}")
        print(f"EPISODE {self.episode_count + 1}")
        print('=' * 80)

        # Reset environment
        obs = self.env.reset()
        done = False
        self.cumulative_reward = 0.0
        self.step_count = 0

        # Send initial game state
        await self.broadcast_game_state()

        while not done:
            # Check if we should step (based on pause/speed controls)
            if not self.ws_server.should_step():
                await asyncio.sleep(0.1)
                continue

            # Get action from model with action masking
            action_masks = self.env.action_masks()
            action, _states = self.model.predict(
                obs,
                action_masks=action_masks,
                deterministic=False
            )

            # Execute action
            obs, reward, done, info = self.env.step(action)

            self.cumulative_reward += reward
            self.step_count += 1

            # Broadcast game state to clients
            await self.broadcast_game_state()

            # Broadcast model state (action info, reward, etc.)
            await self.broadcast_model_state(action, reward)

            # Print progress every 100 steps
            if self.step_count % 100 == 0:
                state = self.env.game.get_state()
                print(f"[Step {self.step_count:5d}] "
                      f"Territory: {state.tiles_owned:4d} ({state.territory_pct:5.1%}) | "
                      f"Cities: {state.cities_count} | "
                      f"Gold: {state.gold:6d} | "
                      f"Rank: {state.rank}/{state.total_players} | "
                      f"Reward: {reward:8.1f} | "
                      f"Cumulative: {self.cumulative_reward:10.1f}")

            # Control game speed
            await asyncio.sleep(0.05 / self.ws_server.speed)

        # Episode finished
        state = self.env.game.get_state()
        print("\n" + "=" * 80)
        print("EPISODE COMPLETE")
        print("=" * 80)
        print(f"Total Steps: {self.step_count}")
        print(f"Cumulative Reward: {self.cumulative_reward:.1f}")
        print(f"Final Territory: {state.tiles_owned} tiles ({state.territory_pct:.1%})")
        print(f"Final Cities: {state.cities_count}")
        print(f"Final Rank: {state.rank}/{state.total_players}")
        print(f"Result: {'Victory! 🏆' if state.rank == 1 else f'Eliminated (Rank {state.rank})'}")
        print("=" * 80)

    async def broadcast_game_state(self):
        """Broadcast current game state to clients"""
        state = self.env.game.get_state()

        # Convert game state to format expected by client
        game_state = {
            'type': 'game_state',
            'tick': state.tick,
            'visual_state': {
                'map_width': 512,
                'map_height': 512,
                'tiles': self._convert_territory_map_to_tiles(state),
                'players': self._get_players_info(state),
                'game_over': state.game_over,
                'rl_player': {
                    'is_alive': not state.has_lost,
                    'territory_pct': state.territory_pct,
                    'rank': state.rank,
                    'tiles_owned': state.tiles_owned,
                    'cities_count': state.cities_count,
                    'gold': state.gold
                }
            }
        }

        await self.ws_server.broadcast(game_state)

    async def broadcast_model_state(self, action: int, reward: float):
        """Broadcast model state (action, reward, etc.) to clients"""
        # Decode action from flat index to cluster, direction, intensity, build_location
        cluster_id = action // 500  # 0-4
        remainder = action % 500
        direction = remainder // 50  # 0-9
        remainder = remainder % 50
        intensity = remainder // 10  # 0-4
        build_location = remainder % 10  # 0-9

        # Map intensity bucket to actual intensity
        intensity_map = [0.0, 0.25, 0.5, 0.75, 1.0]
        intensity_value = intensity_map[intensity]

        model_state = {
            'type': 'model_state',
            'tick': self.step_count,
            'action': {
                'cluster_id': int(cluster_id),
                'direction': int(direction),
                'intensity': float(intensity_value),
                'build_location': int(build_location)
            },
            'reward': float(reward),
            'cumulative_reward': float(self.cumulative_reward),
            'value_estimate': 0.0  # MaskablePPO doesn't expose value easily
        }

        await self.ws_server.broadcast(model_state)

    def _convert_territory_map_to_tiles(self, state):
        """Convert territory map to tile list for visualization"""
        tiles = []

        # territory_map is 512x512, with values:
        # 0 = neutral, 1 = our territory, 2+ = enemy territories
        territory_map = state.territory_map

        # Downsample to reduce data (every 4th pixel for 128x128)
        step = 4
        for y in range(0, territory_map.shape[0], step):
            for x in range(0, territory_map.shape[1], step):
                owner_id = int(territory_map[y, x])

                # Only send non-neutral tiles to reduce bandwidth
                if owner_id > 0:
                    tile = {
                        'x': x // step,
                        'y': y // step,
                        'owner_id': owner_id,
                        'is_mountain': False,  # Phase 6 doesn't track mountains in observation
                        'is_city': False  # Will be updated if city is here
                    }
                    tiles.append(tile)

        # Mark city tiles
        for city_pos in state.our_cities_positions:
            city_x, city_y = city_pos
            tile_x = city_x // step
            tile_y = city_y // step
            # Find the tile and mark it as city
            for tile in tiles:
                if tile['x'] == tile_x and tile['y'] == tile_y:
                    tile['is_city'] = True
                    break

        return tiles

    def _get_players_info(self, state):
        """Get info about all players for visualization"""
        # We don't have full info about all players, so we'll create a minimal set
        players = [
            {
                'id': 1,
                'name': 'RL Agent',
                'color': '#00ff00',  # Green
                'is_alive': not state.has_lost,
                'tiles_owned': state.tiles_owned
            }
        ]

        # Add dummy info for enemies (we can see their territories in the map)
        # Use different colors for different player IDs
        colors = ['#ff0000', '#0000ff', '#ffff00', '#ff00ff', '#00ffff',
                  '#ff8800', '#8800ff', '#00ff88', '#ff0088', '#88ff00']
        for i in range(2, 12):  # Players 2-11 (10 bots)
            players.append({
                'id': i,
                'name': f'Bot {i-1}',
                'color': colors[(i-2) % len(colors)],
                'is_alive': True,  # We don't track this
                'tiles_owned': 0  # We don't track this individually
            })

        return players

    async def shutdown(self):
        """Shutdown the visualizer"""
        print("\nShutting down...")
        await self.ws_server.stop()
        self.env.close()
        print("Shutdown complete")


async def main():
    parser = argparse.ArgumentParser(
        description='Phase 6 Cities-Only Real-Time Visualizer'
    )
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model (.zip)'
    )
    parser.add_argument(
        '--map',
        type=str,
        default='australia_256x256',
        help='Map name (default: australia_256x256)'
    )
    parser.add_argument(
        '--bots',
        type=int,
        default=10,
        help='Number of bot opponents (default: 10)'
    )
    parser.add_argument(
        '--ws-host',
        type=str,
        default='localhost',
        help='WebSocket server host (default: localhost)'
    )
    parser.add_argument(
        '--ws-port',
        type=int,
        default=8765,
        help='WebSocket server port (default: 8765)'
    )

    args = parser.parse_args()

    # Check model exists
    if not os.path.exists(args.model):
        print(f"Error: Model not found at {args.model}")
        print()
        print("Available models:")
        models_dir = "models"
        if os.path.exists(models_dir):
            for run_dir in sorted(os.listdir(models_dir), reverse=True):
                run_path = os.path.join(models_dir, run_dir)
                if os.path.isdir(run_path):
                    print(f"  {run_dir}:")
                    for model_file in os.listdir(run_path):
                        if model_file.endswith('.zip'):
                            print(f"    - {model_file}")
        sys.exit(1)

    # Create and run visualizer
    visualizer = CitiesVisualizer(
        model_path=args.model,
        num_bots=args.bots,
        map_name=args.map,
        websocket_host=args.ws_host,
        websocket_port=args.ws_port
    )

    try:
        await visualizer.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        await visualizer.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
