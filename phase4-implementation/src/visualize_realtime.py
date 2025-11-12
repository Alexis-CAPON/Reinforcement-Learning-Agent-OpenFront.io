"""
Phase 4 Real-Time Visualizer
Watch your RL model play with full game client + overlays
"""

import sys
import os
import argparse
import asyncio
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path to import from phase3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../phase3-implementation/src'))

from stable_baselines3 import PPO
from websocket_server import RLWebSocketServer
from model_state_extractor import ModelStateExtractor
from visual_game_wrapper import VisualGameWrapper
from visual_observation_extractor import VisualObservationExtractor
from collections import deque


class RealtimeVisualizer:
    """Real-time visualizer that shows the model playing with overlays"""

    def __init__(
        self,
        model_path: str,
        num_bots: int = 10,
        websocket_host: str = "localhost",
        websocket_port: int = 8765,
        map_name: str = "australia",
        crop_region: Optional[Dict[str, int]] = None
    ):
        self.model_path = model_path
        self.num_bots = num_bots
        self.map_name = map_name
        self.crop_region = crop_region

        # Load model
        print(f"Loading model from {model_path}...")
        self.model = PPO.load(model_path)
        self.model_extractor = ModelStateExtractor(self.model)

        # Create visual game wrapper (for full visual state AND observations)
        print(f"Creating visual game wrapper...")
        print(f"Map: {map_name}")
        if crop_region:
            print(f"Crop region: x={crop_region['x']}, y={crop_region['y']}, "
                  f"width={crop_region['width']}, height={crop_region['height']}")
        self.visual_game = VisualGameWrapper(num_bots=num_bots, map_name=map_name, crop=crop_region)

        # Create observation extractor for visual game state
        self.obs_extractor = VisualObservationExtractor()

        # Frame stacking for temporal context (match training environment)
        self.frame_stack = 4
        self.frame_buffer = deque(maxlen=self.frame_stack)

        # Create WebSocket server (pass crop region so client can zoom to it)
        print(f"Creating WebSocket server with crop_region: {crop_region}")
        self.ws_server = RLWebSocketServer(websocket_host, websocket_port, crop_region=crop_region)

        # Game state
        self.cumulative_reward = 0.0
        self.step_count = 0
        self.client_ready = False
        self.initial_state_sent = False

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
        print("Phase 4 Real-Time Visualizer Started!")
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
        """Run a single episode with visualization"""
        # Reset visual game
        visual_response = self.visual_game.reset()

        # Get initial observation from visual game
        visual_state = visual_response.get('state', {})
        single_frame_obs = self.obs_extractor.extract_observation(visual_state)

        # Fill frame buffer with initial observation
        self.frame_buffer.clear()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(single_frame_obs)

        # Stack frames for model input
        obs = self._get_stacked_observation()

        done = False
        self.cumulative_reward = 0.0
        self.step_count = 0

        print(f"Episode started with {self.num_bots} opponents")

        # Wait for client to signal it's ready
        print("Waiting for client to be ready...")
        while not self.client_ready:
            await asyncio.sleep(0.1)

        # NOW tick once to trigger the full update with all tiles
        print("Ticking game to get full initial state...")
        visual_response = self.visual_game.tick()

        visual_state = visual_response.get('state')
        game_update = visual_response.get('gameUpdate')

        if visual_state and game_update:
            print(f"Sending initial state: tick={game_update.get('tick')}, tiles={len(game_update.get('packedTileUpdates', []))}")
            print(f"Update types: {list(game_update.get('updates', {}).keys())}")

            # Debug: Check player data
            player_updates = game_update.get('updates', {}).get('1', [])
            print(f"Players in update: {len(player_updates)}")
            for p in player_updates[:3]:  # Show first 3 players
                print(f"  - {p.get('name')}: {p.get('tilesOwned')} tiles, alive={p.get('isAlive')}")

            await self.ws_server.broadcast_game_update(visual_state, game_update)
            print("Initial game state sent to client")
            self.initial_state_sent = True
        else:
            print("ERROR: No game update in response!")
            print(f"Response keys: {visual_response.keys()}")

        import time
        timing_stats = {'inference': [], 'game_tick': [], 'observation': [], 'broadcast': []}

        while not done:
            # Check if we should step (based on pause/speed controls)
            if not self.ws_server.should_step():
                await asyncio.sleep(0.1)
                continue

            # Get action with detailed information
            t0 = time.time()
            action, action_details = self.model_extractor.predict_with_details(
                obs,
                deterministic=True
            )
            timing_stats['inference'].append(time.time() - t0)

            # Execute action in visual game
            direction = action_details['direction']
            intensity = action_details['intensity']
            self.visual_game.attack_direction(direction, intensity)

            t0 = time.time()
            visual_response = self.visual_game.tick()
            timing_stats['game_tick'].append(time.time() - t0)

            # Extract both visual state and game update
            visual_state = visual_response.get('state')
            game_update = visual_response.get('gameUpdate')

            # Get observation from visual game
            t0 = time.time()
            single_frame_obs = self.obs_extractor.extract_observation(visual_state)
            self.frame_buffer.append(single_frame_obs)
            obs = self._get_stacked_observation()
            timing_stats['observation'].append(time.time() - t0)

            # Check termination from visual game
            rl_player = visual_state.get('rl_player', {}) if visual_state else {}
            is_alive = rl_player.get('is_alive', True)
            game_over = visual_state.get('game_over', False) if visual_state else False
            done = not is_alive or game_over

            # Calculate simple reward based on territory change
            territory_pct = rl_player.get('territory_pct', 0.0)
            reward = 0.0  # Placeholder (rewards don't matter for visualization)

            self.cumulative_reward += reward
            self.step_count += 1

            # Broadcast visual game state and game update every step
            t0 = time.time()
            if visual_state and game_update:
                await self.ws_server.broadcast_game_update(visual_state, game_update)

            # Broadcast model state to client
            try:
                await self.ws_server.broadcast_model_state(
                    tick=self.step_count,
                    observation=action_details['raw_observation'],
                    action_dict={
                        'direction_probs': action_details['direction_probs'],
                        'intensity_probs': action_details['intensity_probs'],
                        'build_prob': action_details['build_prob'],
                        'selected_action': action_details['selected_action'],
                        'direction': action_details['direction'],
                        'intensity': action_details['intensity'],
                        'build': action_details['build'],
                    },
                    value=action_details['value_estimate'],
                    reward=float(reward),
                    cumulative_reward=self.cumulative_reward,
                    attention_weights=action_details.get('attention_weights')
                )
                timing_stats['broadcast'].append(time.time() - t0)
            except Exception as e:
                print(f"Warning: Failed to broadcast model state: {e}")
                timing_stats['broadcast'].append(time.time() - t0)

            # Print progress every 50 steps with timing info
            if self.step_count % 50 == 0 and len(timing_stats['inference']) > 0:
                action_str = self.model_extractor.get_action_explanation(action)
                # Calculate average timings
                avg_inference = sum(timing_stats['inference'][-50:]) / len(timing_stats['inference'][-50:]) * 1000
                avg_tick = sum(timing_stats['game_tick'][-50:]) / len(timing_stats['game_tick'][-50:]) * 1000
                avg_obs = sum(timing_stats['observation'][-50:]) / len(timing_stats['observation'][-50:]) * 1000
                avg_broadcast = sum(timing_stats['broadcast'][-50:]) / len(timing_stats['broadcast'][-50:]) * 1000
                total_avg = avg_inference + avg_tick + avg_obs + avg_broadcast

                print(f"[Step {self.step_count:5d}] "
                      f"Reward: {reward:7.2f} | "
                      f"Cumulative: {self.cumulative_reward:9.2f} | "
                      f"Action: {action_str}")
                print(f"  Timing (ms): Inference={avg_inference:.1f} | GameTick={avg_tick:.1f} | "
                      f"Observation={avg_obs:.1f} | Broadcast={avg_broadcast:.1f} | Total={total_avg:.1f}")

            # Delay between ticks (controls game speed)
            await asyncio.sleep(0.05)  # 20 ticks/second (smooth and fast!)

        # Episode finished
        print("\n" + "=" * 80)
        print("Episode Complete!")
        print("=" * 80)
        print(f"Total Steps: {self.step_count}")
        print(f"Cumulative Reward: {self.cumulative_reward:.2f}")
        if visual_state:
            rl_player = visual_state.get('rl_player', {})
            print(f"Result: {'Victory' if game_over and rl_player.get('rank', 99) == 1 else 'Eliminated'}")
        print("=" * 80 + "\n")

        # Wait a bit before closing
        await asyncio.sleep(2)

    def _get_stacked_observation(self) -> Dict:
        """Stack frames from buffer into model input format"""
        import numpy as np

        # Stack map frames (128, 128, 5*4)
        map_frames = [frame['map'] for frame in self.frame_buffer]
        stacked_map = np.concatenate(map_frames, axis=-1)

        # Stack global features (16*4)
        global_frames = [frame['global'] for frame in self.frame_buffer]
        stacked_global = np.concatenate(global_frames, axis=-1)

        return {
            'map': stacked_map,
            'global': stacked_global
        }

    async def shutdown(self):
        """Shutdown the visualizer"""
        print("\nShutting down...")
        await self.ws_server.stop()
        self.visual_game.close()
        print("Shutdown complete")


def start_client_server(project_root: Path, port: int = 9000):
    """Start the development server for the client"""
    print(f"Starting client dev server on http://localhost:{port}")

    # Check if we have package.json in the project root
    package_json = project_root / "package.json"

    if not package_json.exists():
        print("Error: package.json not found in project root")
        print(f"Please run 'npm install' in {project_root}")
        return None

    # Start dev server from project root
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"Failed to start client server: {e}")
        return None


async def main():
    parser = argparse.ArgumentParser(
        description='Phase 4 Real-Time RL Visualizer'
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
        default='australia',
        help='Map to use (default: australia)'
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
                    'world': (2000, 1000),
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
        client_process = start_client_server(project_root, port=9000)
        if client_process:
            print(f"Client server starting on http://localhost:9000")
            time.sleep(3)  # Give server time to start

            # Open the correct RL visualizer URL
            rl_url = f"http://localhost:9000/rl-index.html?ws=ws://{args.ws_host}:{args.ws_port}&map={args.map}"
            print(f"Opening browser: {rl_url}")
            webbrowser.open(rl_url)
        else:
            print("Warning: Failed to start client server")
            print("You can manually start it with: npm run dev")
            print(f"Then open: http://localhost:9000/rl-index.html?ws=ws://{args.ws_host}:{args.ws_port}&map={args.map}")

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
        print("\nInterrupted by user")
    finally:
        await visualizer.shutdown()

        # Stop client server
        if client_process:
            client_process.terminate()
            client_process.wait()

        print("Shutdown complete")


if __name__ == '__main__':
    asyncio.run(main())
