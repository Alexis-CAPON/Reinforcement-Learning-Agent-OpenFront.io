"""
Game Visualizer - Watch the RL agent play with actual game map rendering

This creates an HTML file that shows the game map with colors and territories,
just like you'd see in the actual OpenFront.io client.
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO
from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper
from compat_wrapper import Phase1CompatWrapper
import subprocess


class VisualGameWrapper:
    """Wrapper that captures visual game state (full map)"""

    def __init__(self, map_name: str = 'plains', difficulty: str = 'easy',
                 tick_interval_ms: int = 100, num_players: int = 2):
        self.map_name = map_name
        self.difficulty = difficulty
        self.tick_interval_ms = tick_interval_ms
        self.num_players = num_players
        self.process = None
        self._start_visual_bridge()

    def _start_visual_bridge(self):
        """Start the visual game bridge"""
        bridge_path = os.path.join(
            os.path.dirname(__file__),
            'game_bridge/game_bridge_visual.ts'
        )

        base_game_dir = os.path.join(
            os.path.dirname(__file__),
            '../base-game'
        )

        print(f"Starting visual game bridge...")
        self.process = subprocess.Popen(
            ['npx', 'tsx', bridge_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=base_game_dir
        )
        print("Visual bridge started!")

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
        return self._send_command({
            'type': 'reset',
            'map_name': self.map_name,
            'difficulty': self.difficulty,
            'tick_interval': self.tick_interval_ms,
            'num_players': self.num_players
        })

    def tick(self):
        """Execute game tick"""
        return self._send_command({'type': 'tick'})

    def get_visual_state(self):
        """Get full visual state (all tiles, all players)"""
        return self._send_command({'type': 'get_visual_state'})

    def attack_tile(self, tile_x: int, tile_y: int, attack_percentage: float = 0.5):
        """Attack a tile with specified troop percentage"""
        self._send_command({
            'type': 'attack_tile',
            'tile_x': tile_x,
            'tile_y': tile_y,
            'attack_percentage': attack_percentage
        })

    def get_attackable_neighbors(self):
        """Get attackable neighbors"""
        response = self._send_command({'type': 'get_attackable_neighbors'})
        return response['neighbors']

    def close(self):
        """Shutdown bridge"""
        if self.process:
            try:
                self._send_command({'type': 'shutdown'})
            except:
                pass
            self.process.terminate()
            self.process.wait(timeout=5)


def record_visual_episode(model_path: str, config_path: str, frame_skip: int = 1):
    """Record an episode with full visual state

    Args:
        model_path: Path to trained model
        config_path: Path to config file
        frame_skip: Record every Nth frame (default 1 = all frames)
    """
    print("=" * 80)
    print("🎬 RECORDING VISUAL EPISODE")
    print("=" * 80)
    if frame_skip > 1:
        print(f"Frame skip: Recording every {frame_skip} frames")

    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load model
    print(f"\nLoading model: {model_path}")
    model = PPO.load(model_path)

    # Create visual wrapper
    visual_game = VisualGameWrapper(
        map_name=config['game']['map_name'],
        difficulty=config['game']['opponent_difficulty'],
        tick_interval_ms=config['game']['tick_interval_ms'],
        num_players=config['game']['num_players']
    )

    # Create environment (for action selection)
    env = OpenFrontIOEnv(config_path=config_path)

    # Check if model observation space matches environment
    # Model's policy has observation_space that tells us what it expects
    model_obs_space = model.policy.observation_space

    # Check if model expects neighbor_troops
    model_has_neighbor_troops = 'neighbor_troops' in model_obs_space.spaces if isinstance(model_obs_space, spaces.Dict) else False
    env_has_neighbor_troops = 'neighbor_troops' in env.observation_space.spaces

    print(f"Model expects neighbor_troops: {model_has_neighbor_troops}")
    print(f"Environment has neighbor_troops: {env_has_neighbor_troops}")

    # Apply compatibility wrapper if there's a mismatch
    if not model_has_neighbor_troops and env_has_neighbor_troops:
        print("→ Applying Phase 1 compatibility wrapper (removing neighbor_troops)")
        env = Phase1CompatWrapper(env)
    elif model_has_neighbor_troops and not env_has_neighbor_troops:
        print("ERROR: Model expects neighbor_troops but environment doesn't provide it!")
        print("This shouldn't happen with current code. Check your environment.")
        raise ValueError("Observation space mismatch")

    env = FlattenActionWrapper(env)  # Must match training wrapper

    # Reset both
    print("\nResetting game...")
    visual_game.reset()
    obs, info = env.reset()

    # Record frames
    frames = []
    done = False
    step = 0

    print("\nRecording episode...")

    while not done:
        # Get action from model (flattened Box: [attack_target_continuous, attack_percentage])
        # Use deterministic=False to see actual learned behavior (with exploration)
        action, _ = model.predict(obs, deterministic=False)

        # Parse action (model outputs Box(2,) due to FlattenActionWrapper)
        attack_target_continuous = float(action[0])
        attack_percentage = float(action[1])

        # Round attack target to nearest integer
        attack_target = int(np.clip(np.round(attack_target_continuous), 0, 8))

        # Execute in both
        neighbors = visual_game.get_attackable_neighbors()

        # Debug: Print action every 50 steps
        if step % 50 == 0:
            print(f"  Action: target={attack_target}, pct={attack_percentage:.3f}, neighbors={len(neighbors)}")

        if attack_target > 0 and attack_target - 1 < len(neighbors) and attack_percentage >= 0.01:
            neighbor = neighbors[attack_target - 1]
            visual_game.attack_tile(
                neighbor['tile_x'],
                neighbor['tile_y'],
                attack_percentage
            )

        visual_game.tick()
        obs, reward, terminated, truncated, info = env.step(action)

        # Get visual state
        visual_state = visual_game.get_visual_state()['state']

        # IMPORTANT: Only use visual game state for termination, not the training env
        # The training env and visual game are separate instances and will diverge
        # due to AI randomness in 8-player games
        done = visual_state.get('game_over', False)

        # Safety check: Stop if agent has 0 tiles (dead)
        if visual_state['tiles_owned'] == 0:
            if not done:
                print(f"\n⚠️  Agent eliminated at step {step}! (0 tiles remaining)")
            done = True

        # Safety check: Stop if no valid neighbors (stalemate - agent is surrounded/blocked)
        if len(neighbors) == 0 and visual_state['tiles_owned'] > 0:
            if not done:
                print(f"\n⚠️  Stalemate at step {step}! (agent has {visual_state['tiles_owned']} tiles but no valid attack targets)")
            done = True

        # Record frame (only every Nth step)
        if step % frame_skip == 0 or done:
            frame = {
                'step': step,
                'attack_target': attack_target,
                'attack_percentage': float(attack_percentage),
                'reward': float(reward),
                'visual_state': visual_state
            }
            frames.append(frame)

            if step % 50 == 0:
                print(f"  Step {step}: tiles={visual_state['tiles_owned']}, "
                      f"enemy={visual_state['enemy_tiles']}, "
                      f"terminated={terminated}, truncated={truncated}")

        step += 1

    # Get final state
    final_visual = visual_game.get_visual_state()['state']
    won = final_visual['has_won']
    lost = final_visual['has_lost']
    tiles = final_visual['tiles_owned']

    print(f"\nEpisode complete!")
    print(f"  Steps: {step}")
    print(f"  Final tiles: {tiles}")
    if won:
        print(f"  Result: ✅ WIN (all enemies eliminated)")
    elif lost:
        if tiles == 0:
            print(f"  Result: ❌ LOSS (eliminated - 0 tiles)")
        else:
            print(f"  Result: ❌ LOSS")
    else:
        print(f"  Result: ⏱️ TIMEOUT")

    # Clean up
    visual_game.close()
    env.close()

    return frames, won, final_visual


def generate_html_visualization(frames: List[Dict], won: bool, output_path: str):
    """Generate interactive HTML with map visualization"""

    if not frames:
        print("No frames to visualize!")
        return

    first_frame = frames[0]['visual_state']
    map_width = first_frame['map_width']
    map_height = first_frame['map_height']
    players = first_frame['players']

    # Generate legend items dynamically based on actual players
    player_legend_items = []
    for player in players:
        emoji = '🤖' if player['id'] == 1 else '🎮'
        label = 'RL Agent' if player['id'] == 1 else f'AI Bot {player["id"]}'
        player_legend_items.append(
            f'<span class="legend-item" style="background: {player["color"]};">{emoji} {label}</span>'
        )
    player_legend_html = '\n            '.join(player_legend_items)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>OpenFront.io RL Agent - Game Visualization</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #4CAF50; }}
        .game-canvas {{
            border: 2px solid #444;
            background: #000;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }}
        .controls {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-label {{ font-size: 12px; color: #888; }}
        .stat-value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
        button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }}
        button:hover {{ background: #45a049; }}
        .slider {{ width: 100%; }}
        .legend {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            padding: 5px 10px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 OpenFront.io RL Agent Visualization</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Result</div>
                <div class="stat-value" style="color: {'#4CAF50' if won else '#f44336'}">
                    {'✅ VICTORY' if won else '❌ DEFEAT'}
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Steps</div>
                <div class="stat-value">{len(frames)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Map Size</div>
                <div class="stat-value">{map_width}×{map_height}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Players</div>
                <div class="stat-value">{len(players)}</div>
            </div>
        </div>

        <div class="legend">
            <strong>Players:</strong><br>
            {player_legend_html}
            <span class="legend-item" style="background: #808080;">⛰️ Mountain</span>
            <span class="legend-item" style="background: #333;">◻️ Neutral</span>
        </div>

        <canvas id="gameCanvas" class="game-canvas" width="{map_width * 4}" height="{map_height * 4}"></canvas>

        <div class="controls">
            <button onclick="play()">▶️ Play</button>
            <button onclick="pause()">⏸️ Pause</button>
            <button onclick="reset()">⏮️ Reset</button>
            <button onclick="step()">⏭️ Step</button>
            <br><br>
            <label>Frame: <span id="frameLabel">0 / {len(frames)}</span></label>
            <input type="range" class="slider" id="frameSlider" min="0" max="{len(frames)-1}" value="0" oninput="updateFrame(this.value)">
            <br>
            <label>Speed: <span id="speedLabel">5x</span></label>
            <input type="range" class="slider" id="speedSlider" min="1" max="20" value="5" oninput="updateSpeed(this.value)">
        </div>

        <div class="stats" id="currentStats"></div>
    </div>

    <script>
        const frames = {json.dumps(frames, indent=2)};
        let currentFrame = 0;
        let playing = false;
        let playInterval = null;
        let speed = 5;

        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const tileSize = 4;  // Each tile is 4x4 pixels

        function drawFrame(frameIndex) {{
            const frame = frames[frameIndex];
            const state = frame.visual_state;

            // Clear canvas
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw tiles
            for (const tile of state.tiles) {{
                let color;

                if (tile.is_mountain) {{
                    color = '#808080';  // Gray for mountains
                }} else if (tile.owner_id === 0) {{
                    color = '#333333';  // Dark gray for neutral
                }} else {{
                    // Get player color
                    const player = state.players.find(p => p.id === tile.owner_id);
                    color = player ? player.color : '#FFFFFF';
                }}

                ctx.fillStyle = color;
                ctx.fillRect(tile.x * tileSize, tile.y * tileSize, tileSize, tileSize);

                // Draw city marker
                if (tile.is_city) {{
                    ctx.fillStyle = '#FFFFFF';
                    ctx.fillRect(
                        tile.x * tileSize + 1,
                        tile.y * tileSize + 1,
                        tileSize - 2,
                        tileSize - 2
                    );
                }}
            }}

            // Update stats
            document.getElementById('frameLabel').textContent = `${{frameIndex}} / ${{frames.length}}`;

            const statsHTML = state.players.map(player => `
                <div class="stat-card">
                    <div class="stat-label">Player ${{player.id}} ${{player.id === 1 ? '(RL)' : '(AI)'}}</div>
                    <div class="stat-value" style="color: ${{player.color}}">
                        ${{player.tiles_owned}} tiles
                    </div>
                    <div style="font-size: 12px; margin-top: 5px;">
                        ${{player.total_troops.toFixed(0)}} troops
                    </div>
                </div>
            `).join('');

            document.getElementById('currentStats').innerHTML = statsHTML;
        }}

        function play() {{
            if (playing) return;
            playing = true;
            playInterval = setInterval(() => {{
                currentFrame++;
                if (currentFrame >= frames.length) {{
                    currentFrame = frames.length - 1;
                    pause();
                }}
                drawFrame(currentFrame);
                document.getElementById('frameSlider').value = currentFrame;
            }}, 1000 / speed);
        }}

        function pause() {{
            playing = false;
            if (playInterval) {{
                clearInterval(playInterval);
                playInterval = null;
            }}
        }}

        function reset() {{
            pause();
            currentFrame = 0;
            drawFrame(currentFrame);
            document.getElementById('frameSlider').value = 0;
        }}

        function step() {{
            pause();
            currentFrame = Math.min(currentFrame + 1, frames.length - 1);
            drawFrame(currentFrame);
            document.getElementById('frameSlider').value = currentFrame;
        }}

        function updateFrame(value) {{
            pause();
            currentFrame = parseInt(value);
            drawFrame(currentFrame);
        }}

        function updateSpeed(value) {{
            speed = parseInt(value);
            document.getElementById('speedLabel').textContent = value + 'x';
            if (playing) {{
                pause();
                play();
            }}
        }}

        // Initialize
        drawFrame(0);
    </script>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\n✅ HTML visualization saved to: {output_path}")
    print(f"   Open in browser to watch the replay!")


def main():
    parser = argparse.ArgumentParser(description='Visualize RL agent with game map rendering')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--config', type=str, default='configs/phase1_config.json', help='Config file')
    parser.add_argument('--output', type=str, default=None, help='Output HTML file')
    parser.add_argument('--frame-skip', type=int, default=50, help='Record every Nth frame (default: 50)')
    parser.add_argument('--max-frames', type=int, default=200, help='Maximum frames to record (default: 200)')

    args = parser.parse_args()

    # Record episode
    frames, won, final_state = record_visual_episode(args.model, args.config, args.frame_skip)

    # Generate HTML
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = 'win' if won else 'loss'
        output_path = f"visualization_{result}_{timestamp}.html"

    generate_html_visualization(frames, won, output_path)

    print("\n" + "=" * 80)
    print("✅ VISUALIZATION COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
