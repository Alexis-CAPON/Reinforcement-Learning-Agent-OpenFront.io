"""
Game Visualizer - Watch the RL agent play with actual game map rendering

Creates an interactive HTML file showing the game map with territories,
just like you'd see in the actual OpenFront.io client.
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
from stable_baselines3 import PPO

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from environment import OpenFrontEnv


class VisualGameWrapper:
    """Wrapper that uses visual game bridge for full state export"""

    def __init__(self, num_bots: int = 10, map_name: str = 'plains'):
        self.num_bots = num_bots
        self.map_name = map_name
        self.process = None
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
            'num_bots': self.num_bots,
            'map_name': self.map_name
        })

    def tick(self):
        """Execute game tick"""
        return self._send_command({'type': 'tick'})

    def get_visual_state(self):
        """Get full visual state (all tiles, all players)"""
        return self._send_command({'type': 'get_visual_state'})

    def attack_direction(self, direction: str, intensity: float, build: bool):
        """Execute action in direction"""
        self._send_command({
            'type': 'attack_direction',
            'direction': direction,
            'intensity': intensity,
            'build': build
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


def record_visual_episode(model_path: str, num_bots: int = 10, frame_skip: int = 50):
    """
    Record an episode with full visual state

    Args:
        model_path: Path to trained model (.zip)
        num_bots: Number of bot opponents
        frame_skip: Record every Nth frame (default: 50)

    Returns:
        frames: List of recorded frames
        won: Whether agent won
    """
    print("=" * 80)
    print(f"🎬 RECORDING VISUAL EPISODE ({num_bots} bots)")
    print("=" * 80)
    print(f"Frame skip: Recording every {frame_skip} frames")

    # Load model
    print(f"\nLoading model: {model_path}")
    model = PPO.load(model_path)

    # Create visual wrapper
    visual_game = VisualGameWrapper(num_bots=num_bots)

    # Create environment for action selection
    env = OpenFrontEnv(num_bots=num_bots)

    # Reset both
    print("\nResetting game...")
    visual_game.reset()
    obs, info = env.reset()

    # Action mapping
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
    intensities = [0.20, 0.35, 0.50, 0.75, 1.00]

    # Record frames
    frames = []
    done = False
    step = 0
    max_steps = 10000

    print("\nRecording episode...")

    while not done and step < max_steps:
        # Get action from model
        action, _ = model.predict(obs, deterministic=True)

        # Decode action (90 discrete actions)
        direction_idx = int(action) // 10
        intensity_idx = (int(action) % 10) // 2
        build = (int(action) % 2) == 1

        direction = directions[direction_idx]
        intensity = intensities[intensity_idx]

        # Execute in visual game
        visual_game.attack_direction(direction, intensity, build)
        visual_game.tick()

        # Execute in training env (for observations)
        obs, reward, terminated, truncated, info = env.step(action)

        # Get visual state
        visual_response = visual_game.get_visual_state()
        visual_state = visual_response['state']

        # Check termination from visual game (authoritative)
        done = visual_state['game_over']

        # Safety check
        if not visual_state['rl_player']['is_alive']:
            done = True

        # Record frame (only every Nth step)
        if step % frame_skip == 0 or done:
            frame = {
                'step': step,
                'direction': direction,
                'intensity': intensity,
                'build': build,
                'reward': float(reward),
                'visual_state': visual_state
            }
            frames.append(frame)

            if step % 100 == 0:
                rl = visual_state['rl_player']
                print(f"  Step {step}: "
                      f"tiles={rl['tiles_owned']}, "
                      f"territory={rl['territory_pct']*100:.1f}%, "
                      f"rank={rl['rank']}")

        step += 1

    # Get final state
    final_visual = visual_game.get_visual_state()['state']
    won = final_visual['winner_id'] == 1  # RL agent is player 1

    print(f"\nEpisode complete!")
    print(f"  Steps: {step}")
    print(f"  Final tiles: {final_visual['rl_player']['tiles_owned']}")
    print(f"  Final rank: {final_visual['rl_player']['rank']}")
    if won:
        print(f"  Result: ✅ VICTORY")
    else:
        print(f"  Result: ❌ DEFEAT")

    # Clean up
    visual_game.close()
    env.close()

    return frames, won


def generate_html_visualization(frames: List[Dict], won: bool, output_path: str):
    """Generate interactive HTML with map visualization"""

    if not frames:
        print("No frames to visualize!")
        return

    first_frame = frames[0]['visual_state']
    map_width = first_frame['map_width']
    map_height = first_frame['map_height']
    players = first_frame['players']

    # Generate legend items for players
    player_legend_items = []
    for player in players[:20]:  # Show first 20 in legend
        emoji = '🤖' if player['id'] == 1 else '🎮'
        label = 'RL Agent' if player['id'] == 1 else f'Bot {player["id"]-1}'
        player_legend_items.append(
            f'<span class="legend-item" style="background: {player["color"]};">{emoji} {label}</span>'
        )
    if len(players) > 20:
        player_legend_items.append(f'<span class="legend-item">...and {len(players)-20} more</span>')
    player_legend_html = '\n            '.join(player_legend_items)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>OpenFront.io Phase 3 - Battle Royale Visualization</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0a0a;
            color: #e0e0e0;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        h1 {{ color: #FF4136; text-align: center; }}
        h2 {{ color: #FF851B; }}
        .game-canvas {{
            border: 3px solid #FF4136;
            background: #000;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            display: block;
            margin: 20px auto;
        }}
        .controls {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #333;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #333;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: #FF4136;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            margin-top: 10px;
        }}
        button {{
            background: linear-gradient(135deg, #FF4136 0%, #FF851B 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 10px;
            font-weight: bold;
            font-size: 14px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        button:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(255, 65, 54, 0.4);
        }}
        .slider {{
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #333;
            outline: none;
        }}
        .legend {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #333;
        }}
        .legend-item {{
            display: inline-block;
            margin: 5px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            border: 1px solid #444;
        }}
        .leaderboard {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #333;
            max-height: 400px;
            overflow-y: auto;
        }}
        .leaderboard-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background: #2d2d2d;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        .leaderboard-item.rl-agent {{
            background: #2a1a1a;
            border-left-color: #FF4136;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 OpenFront.io Phase 3 - Battle Royale</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Result</div>
                <div class="stat-value" style="color: {'#00FF00' if won else '#FF4136'}">
                    {'🏆 VICTORY' if won else '💀 ELIMINATED'}
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Frames</div>
                <div class="stat-value" style="color: #3D9970">{len(frames)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Map Size</div>
                <div class="stat-value" style="color: #0074D9">{map_width}×{map_height}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Opponents</div>
                <div class="stat-value" style="color: #FF851B">{len(players)-1}</div>
            </div>
        </div>

        <div class="legend">
            <strong>🎨 Player Colors:</strong><br>
            {player_legend_html}
            <br><br>
            <span class="legend-item" style="background: #808080;">⛰️ Mountain</span>
            <span class="legend-item" style="background: #1a1a1a;">◻️ Neutral</span>
        </div>

        <canvas id="gameCanvas" class="game-canvas" width="{map_width * 3}" height="{map_height * 3}"></canvas>

        <div class="controls">
            <button onclick="play()">▶️ Play</button>
            <button onclick="pause()">⏸️ Pause</button>
            <button onclick="reset()">⏮️ Reset</button>
            <button onclick="step()">⏭️ Step</button>
            <button onclick="speedDown()">🔽 Slower</button>
            <button onclick="speedUp()">🔼 Faster</button>
            <br><br>
            <label><strong>Frame:</strong> <span id="frameLabel">0 / {len(frames)}</span></label>
            <input type="range" class="slider" id="frameSlider" min="0" max="{len(frames)-1}" value="0" oninput="updateFrame(this.value)">
            <br><br>
            <label><strong>Speed:</strong> <span id="speedLabel">5x</span></label>
        </div>

        <div class="stats" id="currentStats"></div>

        <h2>📊 Live Leaderboard</h2>
        <div class="leaderboard" id="leaderboard"></div>
    </div>

    <script>
        const frames = {json.dumps(frames, indent=2)};
        let currentFrame = 0;
        let playing = false;
        let playInterval = null;
        let speed = 5;

        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const tileSize = 3;  // Each tile is 3x3 pixels

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
                    color = '#505050';
                }} else if (tile.owner_id === 0) {{
                    color = '#1a1a1a';
                }} else {{
                    const player = state.players.find(p => p.id === tile.owner_id);
                    color = player ? player.color : '#FFFFFF';
                }}

                ctx.fillStyle = color;
                ctx.fillRect(tile.x * tileSize, tile.y * tileSize, tileSize, tileSize);

                // Draw city marker (white center)
                if (tile.is_city) {{
                    ctx.fillStyle = '#FFFFFF';
                    ctx.fillRect(
                        tile.x * tileSize + 1,
                        tile.y * tileSize + 1,
                        1, 1
                    );
                }}
            }}

            // Update frame label
            document.getElementById('frameLabel').textContent = `${{frameIndex}} / ${{frames.length}}`;

            // Update RL agent stats
            const rlPlayer = state.rl_player;
            const statsHTML = `
                <div class="stat-card">
                    <div class="stat-label">Territory</div>
                    <div class="stat-value" style="color: #FF4136">
                        ${{(rlPlayer.territory_pct * 100).toFixed(1)}}%
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Tiles</div>
                    <div class="stat-value" style="color: #FF851B">
                        ${{rlPlayer.tiles_owned}}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Troops</div>
                    <div class="stat-value" style="color: #3D9970">
                        ${{rlPlayer.troops.toFixed(0)}}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Rank</div>
                    <div class="stat-value" style="color: #0074D9">
                        ${{rlPlayer.rank}} / ${{state.players.length}}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Action</div>
                    <div class="stat-value" style="color: #B10DC9; font-size: 16px;">
                        ${{frame.direction}} @ ${{(frame.intensity * 100).toFixed(0)}}%
                        ${{frame.build ? '🏗️' : ''}}
                    </div>
                </div>
            `;
            document.getElementById('currentStats').innerHTML = statsHTML;

            // Update leaderboard
            const sortedPlayers = [...state.players]
                .filter(p => p.is_alive)
                .sort((a, b) => b.tiles_owned - a.tiles_owned);

            const leaderboardHTML = sortedPlayers.map((player, index) => `
                <div class="leaderboard-item ${{player.id === 1 ? 'rl-agent' : ''}}"
                     style="border-left-color: ${{player.color}}">
                    <div>
                        <strong>#${{index + 1}}</strong>
                        ${{player.id === 1 ? '🤖 ' : ''}}${{player.name}}
                    </div>
                    <div>
                        ${{player.tiles_owned}} tiles |
                        ${{player.total_troops.toFixed(0)}} troops
                    </div>
                </div>
            `).join('');

            document.getElementById('leaderboard').innerHTML = leaderboardHTML;
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

        function speedUp() {{
            speed = Math.min(speed + 1, 20);
            document.getElementById('speedLabel').textContent = speed + 'x';
            if (playing) {{ pause(); play(); }}
        }}

        function speedDown() {{
            speed = Math.max(speed - 1, 1);
            document.getElementById('speedLabel').textContent = speed + 'x';
            if (playing) {{ pause(); play(); }}
        }}

        function updateFrame(value) {{
            pause();
            currentFrame = parseInt(value);
            drawFrame(currentFrame);
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
    parser = argparse.ArgumentParser(
        description='Visualize Phase 3 RL agent with game map rendering'
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
        '--output',
        type=str,
        default=None,
        help='Output HTML file path'
    )
    parser.add_argument(
        '--frame-skip',
        type=int,
        default=50,
        help='Record every Nth frame (default: 50)'
    )

    args = parser.parse_args()

    # Check model exists
    if not os.path.exists(args.model):
        print(f"❌ Error: Model not found at {args.model}")
        sys.exit(1)

    # Record episode
    frames, won = record_visual_episode(args.model, args.num_bots, args.frame_skip)

    # Generate HTML
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = 'win' if won else 'loss'
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'visualizations')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"battle_royale_{result}_{timestamp}.html")

    generate_html_visualization(frames, won, output_path)

    print("\n" + "=" * 80)
    print("✅ VISUALIZATION COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
