"""
Phase 6 Real-Time Visualizer - Cities Only
Watch your trained MaskablePPO model play with full game visualization
"""

import sys
import os
import argparse
import asyncio
import subprocess
import time
import webbrowser
import socket
from pathlib import Path
from typing import Optional, Dict

from sb3_contrib import MaskablePPO
from visual_game_wrapper import VisualGameWrapper
from websocket_server import RLWebSocketServer
import numpy as np
from scipy.ndimage import zoom, sobel
from collections import deque


# Direction mapping for action decoding
DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT', 'BUILD_CITY']


class RealtimeVisualizer:
    """Real-time visualizer for Phase 6 cities-only model"""

    def __init__(
        self,
        model_path: str,
        num_bots: int = 10,
        websocket_host: str = "localhost",
        websocket_port: int = 8765,
        map_name: str = "australia_256x256",
        crop_region: Optional[Dict[str, int]] = None
    ):
        self.model_path = model_path
        self.num_bots = num_bots
        self.map_name = map_name
        self.crop_region = crop_region

        # Load model
        print(f"Loading model from {model_path}...")
        self.model = MaskablePPO.load(model_path)
        print("✓ Model loaded successfully")

        # Create visual game wrapper (SINGLE SOURCE OF TRUTH)
        print(f"Creating visual game wrapper (single source of truth)...")
        print(f"Map: {map_name}")
        if crop_region:
            print(f"Crop region: x={crop_region['x']}, y={crop_region['y']}, "
                  f"width={crop_region['width']}, height={crop_region['height']}")

        # Use the map name directly - no conversion needed
        # australia_256x256 is a real map, not a suffix to be stripped
        self.visual_game = VisualGameWrapper(num_bots=num_bots, map_name=map_name, crop=crop_region)
        print("✓ Visual game wrapper created")

        # Create WebSocket server (pass crop region so client can zoom to it)
        print(f"Creating WebSocket server with crop_region: {crop_region}")
        self.ws_server = RLWebSocketServer(websocket_host, websocket_port, crop_region=crop_region)

        # Game state tracking
        self.cumulative_reward = 0.0
        self.step_count = 0
        self.client_ready = False
        self.initial_state_sent = False
        self.previous_state = None

        # Frame stacking for temporal context (4 frames like training)
        self.frame_stack = 4
        self.frame_buffer = deque(maxlen=self.frame_stack)

        # Action space constants (must match training)
        self.action_dims = (5, 10, 5, 10)  # cluster, direction, intensity, tile
        self.intensities = [0.15, 0.30, 0.45, 0.60, 0.75]

    async def on_client_ready(self):
        """Called when client is ready to receive game state"""
        self.client_ready = True
        print("Client is ready! Sending initial game state...")

    async def run(self):
        """Run the visualizer"""
        # Start WebSocket server
        await self.ws_server.start()

        # Register callback for when client is ready
        self.ws_server.on_ready(self.on_client_ready)

        print("\n" + "=" * 80)
        print("Phase 6 Real-Time Visualizer Started!")
        print("=" * 80)
        print(f"WebSocket server: ws://{self.ws_server.host}:{self.ws_server.port}")
        print(f"Open the client in your browser to start visualization")
        print("=" * 80 + "\n")

        # Wait for client to connect
        print("Waiting for client connection...")
        while not self.ws_server.has_clients():
            await asyncio.sleep(0.5)

        print("Client connected! Waiting for client to be ready...\n")

        # Run the game (reset happens inside run_episode)
        await self.run_episode()

    async def run_episode(self):
        """Run a single episode with visualization (using only visual game)"""
        # Reset visual game (SINGLE SOURCE OF TRUTH)
        visual_response = self.visual_game.reset()
        visual_state = visual_response.get('state')

        done = False
        self.cumulative_reward = 0.0
        self.step_count = 0
        self.previous_state = None

        # Initialize frame buffer with initial observation
        print(f"Episode started with {self.num_bots} opponents (SINGLE GAME - no desync)")
        print("Initializing observations from visual game...")

        initial_obs = self._create_observation_from_visual_state(visual_state)
        for _ in range(self.frame_stack):
            self.frame_buffer.append(initial_obs)

        print("✓ Observations initialized")

        # Wait for client to signal it's ready
        print("Waiting for client to be ready...")
        while not self.client_ready:
            await asyncio.sleep(0.1)

        # Tick once to get full initial state
        print("Ticking game to get full initial state...")
        visual_response = self.visual_game.tick()
        visual_state = visual_response.get('state')
        game_update = visual_response.get('gameUpdate')

        if visual_state and game_update:
            print(f"Sending initial state: tick={game_update.get('tick')}, tiles={len(game_update.get('packedTileUpdates', []))}")
            await self.ws_server.broadcast_game_update(visual_state, game_update)
            print("Initial game state sent to client")
            self.initial_state_sent = True
        else:
            print("WARNING: No game update in response!")

        # Main game loop (using visual game state only - NO desync!)
        while not done:
            # Check if we should step (based on pause/speed controls)
            if not self.ws_server.should_step():
                await asyncio.sleep(0.1)
                continue

            # Create observation from visual state
            obs_frame = self._create_observation_from_visual_state(visual_state)
            self.frame_buffer.append(obs_frame)
            obs = self._stack_frames()

            # Create action masks from visual state
            action_masks = self._create_action_masks_from_visual_state(visual_state)

            # Get action from model
            action, _states = self.model.predict(
                obs,
                action_masks=action_masks,
                deterministic=False
            )

            # Decode action
            action_dict = self._decode_action(action)

            # Execute action on visual game
            direction_str = DIRECTIONS[action_dict['direction']]
            if direction_str == 'BUILD_CITY':
                # Build city action
                tile = action_dict['build_location']
                tile_x = tile % 2
                tile_y = tile // 2
                normalized_x = tile_x / 1.0
                normalized_y = tile_y / 4.0
                try:
                    success = self.visual_game.build_unit('City', normalized_x, normalized_y)
                    if success:
                        print(f"Step {self.step_count}: Built city at ({normalized_x:.2f}, {normalized_y:.2f})")
                except Exception as e:
                    print(f"Step {self.step_count}: Failed to build city: {e}")
            elif direction_str not in ['WAIT']:
                # Attack action
                self.visual_game.attack_direction(direction_str, action_dict['intensity'])

            # Tick visual game
            visual_response = self.visual_game.tick()
            visual_state = visual_response.get('state')
            game_update = visual_response.get('gameUpdate')

            # Compute reward from visual state
            reward = self._compute_reward(visual_state, self.previous_state)
            self.cumulative_reward += reward
            self.step_count += 1

            # Check if game is over (from visual game state)
            done = visual_state.get('game_over', False)

            # Store previous state
            self.previous_state = visual_state

            # Broadcast visual game state and game update
            if visual_state and game_update:
                await self.ws_server.broadcast_game_update(visual_state, game_update)

            # Broadcast model state
            try:
                direction_name = DIRECTIONS[action_dict['direction']] if action_dict['direction'] < len(DIRECTIONS) else 'WAIT'
                if direction_name == 'WAIT':
                    direction_name = 'IDLE'

                await self.ws_server.broadcast_model_state(
                    tick=self.step_count,
                    observation=None,
                    action_dict={
                        'direction': direction_name,
                        'intensity': action_dict['intensity'],
                        'cluster_id': action_dict['cluster_id'],
                        'build_location': action_dict['build_location'],
                        'selected_action': int(action)
                    },
                    value=0.0,
                    reward=float(reward),
                    cumulative_reward=self.cumulative_reward,
                    attention_weights=None
                )
            except Exception as e:
                print(f"Warning: Failed to broadcast model state: {e}")

            # Print progress every 10 steps
            if self.step_count % 10 == 0:
                territory = visual_state.get('territory_pct', 0.0)
                gold = visual_state.get('gold', 0)
                cities = visual_state.get('cities_count', 0)
                action_str = f"{direction_str} {action_dict['intensity']*100:.0f}%"
                print(f"[Step {self.step_count:5d}] "
                      f"Territory: {territory:5.1%} | "
                      f"Cities: {cities} | "
                      f"Gold: {gold:4d} | "
                      f"Reward: {reward:7.2f} | "
                      f"Cumulative: {self.cumulative_reward:9.2f} | "
                      f"Action: {action_str}")

            # Delay between ticks (controls game speed)
            await asyncio.sleep(0.05)  # 20 ticks/second

        # Episode finished
        print("\n" + "=" * 80)
        print("Episode Complete!")
        print("=" * 80)
        print(f"Total Steps: {self.step_count}")
        print(f"Cumulative Reward: {self.cumulative_reward:.2f}")
        print(f"Final Territory: {visual_state.get('territory_pct', 0.0):.1%}")
        print(f"Final Rank: {visual_state.get('rank', 0)}/{visual_state.get('total_players', 0)}")
        if visual_state.get('has_won'):
            print("Result: VICTORY!")
        elif visual_state.get('has_lost'):
            print("Result: Defeated")
        print("=" * 80 + "\n")

        # Wait a bit before closing
        await asyncio.sleep(2)

    def _create_observation_from_visual_state(self, visual_state: Dict) -> Dict[str, np.ndarray]:
        """
        Create Phase 6 observation from visual game state.
        Returns dict with 'map', 'global', 'clusters' matching training format.
        """
        # Extract basic state info
        territory_map = np.array(visual_state.get('territory_map', []), dtype=np.float32)
        if territory_map.size == 0:
            # Fallback: create dummy observation
            return {
                'map': np.zeros((128, 128, 8 * self.frame_stack), dtype=np.float32),
                'global': np.zeros(16 * self.frame_stack, dtype=np.float32),
                'clusters': np.zeros((5, 4), dtype=np.float32)
            }

        h, w = territory_map.shape

        # Downsample to 128×128
        target_size = 128
        if h > target_size or w > target_size:
            scale_h = target_size / h
            scale_w = target_size / w
            territory_map = zoom(territory_map, (scale_h, scale_w), order=0)

        # Pad if needed
        if territory_map.shape[0] < target_size or territory_map.shape[1] < target_size:
            padded = np.zeros((target_size, target_size), dtype=np.float32)
            padded[:territory_map.shape[0], :territory_map.shape[1]] = territory_map
            territory_map = padded

        # Create 8 spatial channels
        channels = np.zeros((target_size, target_size, 8), dtype=np.float32)

        # Channel 0: Our territory
        our_territory = (territory_map == 1).astype(np.float32)
        channels[:, :, 0] = our_territory

        # Channel 1: Enemy territory
        enemy_territory = (territory_map >= 2).astype(np.float32)
        channels[:, :, 1] = enemy_territory

        # Channel 2: Neutral territory
        channels[:, :, 2] = (territory_map == 0).astype(np.float32)

        # Channel 3: Border tiles
        border = np.abs(sobel(territory_map, axis=0)) + np.abs(sobel(territory_map, axis=1))
        channels[:, :, 3] = np.clip(border, 0, 1)

        # Channel 4: Troop density (simplified)
        channels[:, :, 4] = our_territory * 0.5

        # Channels 5-6: Cities
        scale_x = target_size / w if w > 0 else 1
        scale_y = target_size / h if h > 0 else 1

        for pos in visual_state.get('our_cities_positions', []):
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 5] = 1.0

        for pos in visual_state.get('enemy_cities_positions', []):
            x_scaled = int(pos['x'] * scale_x)
            y_scaled = int(pos['y'] * scale_y)
            if 0 <= x_scaled < target_size and 0 <= y_scaled < target_size:
                channels[y_scaled, x_scaled, 6] = 1.0

        # Channel 7: Valid building locations
        channels[:, :, 7] = our_territory

        # Create global features (16 features)
        global_features = np.zeros(16, dtype=np.float32)
        total_tiles = visual_state.get('total_tiles', 1)
        tiles_owned = visual_state.get('tiles_owned', 0)
        population = visual_state.get('population', 0)

        global_features[0] = visual_state.get('territory_pct', 0.0)
        global_features[1] = tiles_owned / max(total_tiles, 1)
        global_features[2] = visual_state.get('neutral_tiles', 0) / max(total_tiles, 1)
        global_features[3] = visual_state.get('border_tiles', 0) / max(tiles_owned, 1)
        global_features[4] = visual_state.get('territory_change', 0.0)
        global_features[5] = population / max(visual_state.get('max_population', 1), 1)
        global_features[6] = visual_state.get('population_growth_rate', 0.0)
        global_features[7] = visual_state.get('border_pressure', 0.0)
        global_features[8] = visual_state.get('rank', 0) / max(visual_state.get('total_players', 1), 1)
        global_features[9] = visual_state.get('alive_players', 0) / max(visual_state.get('total_players', 1), 1)
        global_features[10] = visual_state.get('time_alive', 0) / 10000.0
        global_features[11] = np.log1p(visual_state.get('gold', 0)) / 10.0
        global_features[12] = visual_state.get('cities_count', 0) / 10.0
        global_features[13] = float(visual_state.get('can_build_city', False))

        # Cluster features
        clusters = visual_state.get('clusters', [])
        global_features[14] = len(clusters) / 5.0
        if len(clusters) > 0:
            global_features[15] = clusters[0].get('troop_count', 0) / max(population, 1)

        # Create cluster features (5 clusters × 4 features)
        cluster_features = np.zeros((5, 4), dtype=np.float32)
        for i, cluster in enumerate(clusters[:5]):
            cluster_features[i, 0] = len(cluster.get('tiles', [])) / max(tiles_owned, 1)
            cluster_features[i, 1] = cluster.get('troop_count', 0) / max(population, 1)
            cluster_features[i, 2] = 0.0  # Has city (would need to check)
            cluster_features[i, 3] = float(visual_state.get('can_build_city', False))

        return {
            'map': channels,
            'global': global_features,
            'clusters': cluster_features
        }

    def _create_action_masks_from_visual_state(self, visual_state: Dict) -> np.ndarray:
        """
        Create action masks from visual game state.
        Returns flat boolean mask of shape (2500,) where True = valid action.
        """
        mask = np.zeros(self.action_dims, dtype=bool)  # (5, 10, 5, 10)

        clusters = visual_state.get('clusters', [])
        can_build_city = visual_state.get('can_build_city', False)
        num_clusters = len(clusters)

        # For each existing cluster
        for cluster_id in range(min(num_clusters, 5)):
            # Attack actions (0-8): enable all directions/intensities/tiles
            for direction in range(9):
                for intensity in range(5):
                    for tile in range(10):
                        mask[cluster_id, direction, intensity, tile] = True

            # BUILD_CITY action (9): enable if we have gold
            if can_build_city:
                for tile in range(10):
                    mask[cluster_id, 9, 0, tile] = True

        return mask.flatten()

    def _compute_reward(self, current_state: Dict, previous_state: Optional[Dict]) -> float:
        """Compute reward from visual game state changes"""
        if previous_state is None:
            return 1.0

        reward = 0.0

        # Territory reward
        territory_gained = current_state.get('tiles_owned', 0) - previous_state.get('tiles_owned', 0)
        reward += territory_gained * 10.0

        # Population reward
        pop_increase = current_state.get('population', 0) - previous_state.get('population', 0)
        reward += pop_increase * 5.0

        # Survival bonus
        if current_state.get('game_over', False):
            if current_state.get('has_won', False):
                reward += 200.0
            elif current_state.get('has_lost', False):
                reward -= 100.0
        else:
            reward += 1.0

        # Elimination bonus
        players_eliminated = previous_state.get('alive_players', 0) - current_state.get('alive_players', 0)
        if players_eliminated > 0:
            reward += players_eliminated * 50.0

        # Economic rewards
        gold_gained = current_state.get('gold', 0) - previous_state.get('gold', 0)
        reward += gold_gained * 0.1

        # City construction bonus
        cities_built = current_state.get('cities_count', 0) - previous_state.get('cities_count', 0)
        if cities_built > 0:
            reward += cities_built * 20.0

        return reward

    def _stack_frames(self) -> Dict[str, np.ndarray]:
        """Stack frames for temporal context"""
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

    def _decode_action(self, action: int) -> Dict:
        """Decode flat action index to components for Phase 6"""
        # Phase 6 action space: 5 clusters × 10 directions × 5 intensities × 10 build_locations = 2,500
        cluster_id = action // 500  # 0-4
        remainder = action % 500
        direction = remainder // 50  # 0-9
        remainder = remainder % 50
        intensity_bucket = remainder // 10  # 0-4
        build_location = remainder % 10  # 0-9

        # Map intensity bucket to actual intensity
        intensity_map = [0.0, 0.25, 0.5, 0.75, 1.0]
        intensity = intensity_map[intensity_bucket]

        return {
            'cluster_id': int(cluster_id),
            'direction': int(direction),
            'intensity': float(intensity),
            'build_location': int(build_location)
        }

    async def shutdown(self):
        """Shutdown the visualizer"""
        print("\nShutting down...")
        try:
            await self.ws_server.stop()
        except (asyncio.CancelledError, Exception) as e:
            # Ignore errors during shutdown
            pass
        try:
            self.visual_game.close()
        except Exception:
            pass
        print("Shutdown complete")


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def start_client_server(project_root: Path, port: int = 9000):
    """Start the development server for the client"""
    print(f"\n{'='*80}")
    print(f"CLIENT DEV SERVER")
    print(f"{'='*80}")

    # Check if port is already in use
    if is_port_in_use(port):
        print(f"✓ Dev server already running on port {port}")
        print(f"  Using existing server at http://localhost:{port}")
        print(f"{'='*80}\n")
        return "already_running"  # Special marker to indicate server is already up

    print(f"Starting dev server on port {port}...")

    # Check if we have package.json in the project root
    package_json = project_root / "package.json"

    if not package_json.exists():
        print(f"Error: package.json not found in {project_root}")
        print(f"Please run 'npm install' in {project_root}")
        return None

    # Check if node_modules exists
    node_modules = project_root / "node_modules"
    if not node_modules.exists():
        print(f"Error: node_modules not found in {project_root}")
        print(f"Please run 'npm install' in {project_root}")
        return None

    # Start dev server from project root (show output for user visibility)
    try:
        print(f"Running: npm run dev (in {project_root})")
        print(f"Note: Dev server output will appear below...")
        print(f"{'='*80}\n")

        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(project_root),
            # Don't capture output - let it show in terminal
            stdout=None,
            stderr=None
        )
        return process
    except Exception as e:
        print(f"Failed to start client server: {e}")
        return None


async def main():
    parser = argparse.ArgumentParser(
        description='Phase 6 Real-Time RL Visualizer - Cities Only'
    )
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model (.zip)'
    )
    parser.add_argument(
        '--num-bots',
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
    parser.add_argument(
        '--map',
        type=str,
        default='australia_256x256',
        help='Map to use (default: australia_256x256)'
    )
    parser.add_argument(
        '--crop',
        type=str,
        default='center-800x600',
        help='Crop region: "center-WxH" or "x,y,w,h" or "none" (default: center-800x600)'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not start the client dev server'
    )

    args = parser.parse_args()

    # Check model exists
    if not os.path.exists(args.model):
        print(f"Error: Model not found at {args.model}")
        sys.exit(1)

    # Parse crop parameter
    crop_region = None
    if args.crop and args.crop != 'none':
        if args.crop.startswith('center-'):
            # Format: center-WIDTHxHEIGHT (e.g., center-512x384)
            size_str = args.crop[7:]  # Remove 'center-'
            try:
                width, height = map(int, size_str.split('x'))

                # Map dimensions (hardcoded for now, could be dynamic)
                map_dimensions = {
                    'australia': (2000, 1500),
                    'australia_256x256': (2000, 1500),
                    'world': (2000, 1000),
                    'world_256x256': (2000, 1000),
                    'europe': (1500, 1200),
                }
                full_width, full_height = map_dimensions.get(args.map, (2000, 1500))

                # Calculate centered crop
                x = (full_width - width) // 2
                y = (full_height - height) // 2

                crop_region = {'x': x, 'y': y, 'width': width, 'height': height}
                center_x = x + width // 2
                center_y = y + height // 2
                spawn_radius = min(width, height) // 2 - 20
                print(f"[PYTHON] Using centered crop: {width}x{height} at ({x}, {y})")
                print(f"[PYTHON] Crop center: ({center_x}, {center_y}), spawn radius: {spawn_radius}")
            except ValueError:
                print(f"Error: Invalid crop format '{args.crop}'. Use 'center-WxH' (e.g., center-512x384)")
                sys.exit(1)
        else:
            # Format: x,y,w,h (e.g., 744,558,512,384)
            try:
                x, y, width, height = map(int, args.crop.split(','))
                crop_region = {'x': x, 'y': y, 'width': width, 'height': height}
                center_x = x + width // 2
                center_y = y + height // 2
                spawn_radius = min(width, height) // 2 - 20
                print(f"[PYTHON] Using custom crop: {width}x{height} at ({x}, {y})")
                print(f"[PYTHON] Crop center: ({center_x}, {center_y}), spawn radius: {spawn_radius}")
            except ValueError:
                print(f"Error: Invalid crop format '{args.crop}'. Use 'x,y,w,h' (e.g., 744,558,512,384)")
                sys.exit(1)

    # Start client dev server (if requested)
    client_process = None
    if not args.no_browser:
        # Start server from base-game directory
        project_root = Path(__file__).parent.parent.parent / "base-game"
        result = start_client_server(project_root, port=9000)

        if result == "already_running":
            # Server already running, no need to wait
            client_process = None  # Don't need to track process
            server_ready = True
        elif result:
            # New server started successfully
            client_process = result
            print(f"\nWaiting for dev server to start...")
            time.sleep(5)  # Give server time to start
            server_ready = True
        else:
            # Failed to start server
            server_ready = False

        if server_ready:
            # Open the correct RL visualizer URL
            # Use the map name directly (australia_256x256 is a real map name)
            rl_url = f"http://localhost:9000/rl-index.html?ws=ws://{args.ws_host}:{args.ws_port}&map={args.map}"

            print(f"\n{'='*80}")
            print(f"BROWSER LAUNCH")
            print(f"{'='*80}")
            print(f"Opening browser automatically...")
            print(f"URL: {rl_url}")
            print(f"\nIf the browser doesn't open, manually navigate to:")
            print(f"  {rl_url}")
            print(f"{'='*80}\n")

            webbrowser.open(rl_url)
            time.sleep(2)  # Give browser time to launch
        else:
            print("\n" + "="*80)
            print("WARNING: Failed to start client server")
            print("="*80)
            print("You can manually start it with:")
            print(f"  cd {project_root}")
            print(f"  npm run dev")
            print(f"\nThen open in your browser:")
            print(f"  http://localhost:9000/rl-index.html?ws=ws://{args.ws_host}:{args.ws_port}&map={args.map}")
            print("="*80 + "\n")

    # Create and run visualizer
    visualizer = RealtimeVisualizer(
        model_path=args.model,
        num_bots=args.num_bots,
        websocket_host=args.ws_host,
        websocket_port=args.ws_port,
        map_name=args.map,
        crop_region=crop_region
    )

    try:
        await visualizer.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError during execution: {e}")
    finally:
        try:
            await visualizer.shutdown()
        except Exception:
            pass

        # Stop client server
        if client_process:
            try:
                client_process.terminate()
                client_process.wait(timeout=5)
            except Exception:
                pass

        print("\nVisualization ended. Thank you!")


if __name__ == '__main__':
    asyncio.run(main())
