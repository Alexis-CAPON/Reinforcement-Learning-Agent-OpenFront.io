"""
Visualization tool for watching the RL agent play OpenFront.io

This script allows you to:
1. Watch a trained agent play in real-time
2. Record episodes for later analysis
3. Generate HTML replays with step-by-step visualization
"""
import sys
import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

import numpy as np
from stable_baselines3 import PPO
from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper


class EpisodeRecorder:
    """Records game states during episodes for visualization"""

    def __init__(self):
        self.frames: List[Dict[str, Any]] = []
        self.episode_info: Dict[str, Any] = {}

    def reset(self):
        """Start recording a new episode"""
        self.frames = []
        self.episode_info = {
            'start_time': datetime.now().isoformat(),
            'total_reward': 0,
            'steps': 0,
            'won': False
        }

    def record_frame(self, step: int, obs: Dict, action: int, reward: float, info: Dict):
        """Record a single frame/step"""
        frame = {
            'step': step,
            'tiles_owned': info['tiles'],
            'enemy_tiles': info['enemy_tiles'],
            'troops': float(info['troops']),
            'gold': float(info['gold']),
            'action': int(action),
            'reward': float(reward),
            'num_neighbors': info['num_neighbors'],
            'action_mask': obs['action_mask'].tolist()
        }
        self.frames.append(frame)
        self.episode_info['total_reward'] += reward
        self.episode_info['steps'] = step

    def finalize(self, won: bool, final_tiles: int):
        """Finalize episode recording"""
        self.episode_info['won'] = won
        self.episode_info['final_tiles'] = final_tiles
        self.episode_info['end_time'] = datetime.now().isoformat()

    def save_to_json(self, filepath: str):
        """Save recording to JSON file"""
        data = {
            'episode_info': self.episode_info,
            'frames': self.frames
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Episode recording saved to: {filepath}")

    def generate_html(self, filepath: str):
        """Generate interactive HTML visualization"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>OpenFront.io RL Agent Replay</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        h1 {{ color: #4CAF50; }}
        .controls {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .chart-container {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        canvas {{
            max-width: 100%;
        }}
        button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }}
        button:hover {{
            background: #45a049;
        }}
        button:disabled {{
            background: #555;
            cursor: not-allowed;
        }}
        .slider {{
            width: 100%;
            margin: 10px 0;
        }}
        .action-display {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .action-label {{
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .won {{ color: #4CAF50; }}
        .lost {{ color: #f44336; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>🎮 OpenFront.io RL Agent Replay</h1>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">Outcome</div>
            <div class="stat-value {'won' if self.episode_info['won'] else 'lost'}">
                {'✅ VICTORY' if self.episode_info['won'] else '❌ DEFEAT'}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Steps</div>
            <div class="stat-value">{self.episode_info['steps']}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Reward</div>
            <div class="stat-value">{self.episode_info['total_reward']:.1f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Final Tiles</div>
            <div class="stat-value">{self.episode_info.get('final_tiles', 0)}</div>
        </div>
    </div>

    <div class="controls">
        <button id="playBtn">▶️ Play</button>
        <button id="pauseBtn">⏸️ Pause</button>
        <button id="resetBtn">⏮️ Reset</button>
        <button id="stepBtn">⏭️ Step</button>
        <br><br>
        <label>Speed: <span id="speedLabel">1x</span></label>
        <input type="range" class="slider" id="speedSlider" min="1" max="10" value="5">
        <br>
        <label>Frame: <span id="frameLabel">0 / {len(self.frames)}</span></label>
        <input type="range" class="slider" id="frameSlider" min="0" max="{len(self.frames)-1}" value="0">
    </div>

    <div class="action-display">
        <div class="action-label">Current Action: <span id="actionText">IDLE</span></div>
        <div>Reward: <span id="rewardText">0</span></div>
        <div>Available Actions: <span id="validActionsText">0, 1, 2</span></div>
    </div>

    <div class="chart-container">
        <canvas id="gameChart"></canvas>
    </div>

    <script>
        const frames = {json.dumps(self.frames)};
        let currentFrame = 0;
        let playing = false;
        let playInterval = null;

        const actionNames = ['IDLE', 'ATTACK_N0', 'ATTACK_N1', 'ATTACK_N2', 'ATTACK_N3',
                           'ATTACK_N4', 'ATTACK_N5', 'ATTACK_N6', 'ATTACK_N7'];

        // Initialize chart
        const ctx = document.getElementById('gameChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: frames.map(f => f.step),
                datasets: [
                    {{
                        label: 'Agent Tiles',
                        data: frames.map(f => f.tiles_owned),
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.1
                    }},
                    {{
                        label: 'Enemy Tiles',
                        data: frames.map(f => f.enemy_tiles),
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.1
                    }},
                    {{
                        label: 'Reward (÷10)',
                        data: frames.map(f => f.reward / 10),
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Territory Control & Rewards Over Time',
                        color: '#e0e0e0'
                    }},
                    legend: {{
                        labels: {{
                            color: '#e0e0e0'
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ color: '#444' }}
                    }},
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ color: '#444' }},
                        title: {{
                            display: true,
                            text: 'Tiles',
                            color: '#e0e0e0'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ drawOnChartArea: false }},
                        title: {{
                            display: true,
                            text: 'Reward (÷10)',
                            color: '#e0e0e0'
                        }}
                    }}
                }}
            }}
        }});

        function updateDisplay() {{
            const frame = frames[currentFrame];
            document.getElementById('frameLabel').textContent = `${{currentFrame}} / ${{frames.length}}`;
            document.getElementById('frameSlider').value = currentFrame;
            document.getElementById('actionText').textContent = actionNames[frame.action];
            document.getElementById('rewardText').textContent = frame.reward.toFixed(2);

            const validActions = frame.action_mask
                .map((valid, idx) => valid ? idx : -1)
                .filter(idx => idx >= 0)
                .map(idx => actionNames[idx])
                .join(', ');
            document.getElementById('validActionsText').textContent = validActions;

            // Update chart annotation (highlight current frame)
            chart.options.plugins.annotation = {{
                annotations: {{
                    line1: {{
                        type: 'line',
                        xMin: currentFrame,
                        xMax: currentFrame,
                        borderColor: 'rgba(255, 255, 255, 0.5)',
                        borderWidth: 2,
                    }}
                }}
            }};
            chart.update('none');
        }}

        function play() {{
            if (playing) return;
            playing = true;
            const speed = document.getElementById('speedSlider').value;
            const interval = 1000 / speed;
            playInterval = setInterval(() => {{
                currentFrame++;
                if (currentFrame >= frames.length) {{
                    currentFrame = frames.length - 1;
                    pause();
                }}
                updateDisplay();
            }}, interval);
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
            updateDisplay();
        }}

        function step() {{
            pause();
            currentFrame = Math.min(currentFrame + 1, frames.length - 1);
            updateDisplay();
        }}

        document.getElementById('playBtn').addEventListener('click', play);
        document.getElementById('pauseBtn').addEventListener('click', pause);
        document.getElementById('resetBtn').addEventListener('click', reset);
        document.getElementById('stepBtn').addEventListener('click', step);

        document.getElementById('frameSlider').addEventListener('input', (e) => {{
            pause();
            currentFrame = parseInt(e.target.value);
            updateDisplay();
        }});

        document.getElementById('speedSlider').addEventListener('input', (e) => {{
            document.getElementById('speedLabel').textContent = e.target.value + 'x';
            if (playing) {{
                pause();
                play();
            }}
        }});

        // Initialize display
        updateDisplay();
    </script>
</body>
</html>"""

        with open(filepath, 'w') as f:
            f.write(html)
        print(f"Interactive HTML replay saved to: {filepath}")


def watch_agent(
    model_path: str,
    config_path: str = 'configs/phase1_config.json',
    n_episodes: int = 1,
    save_recordings: bool = False,
    real_time: bool = True,
    delay: float = 0.5
):
    """
    Watch a trained agent play episodes

    Args:
        model_path: Path to trained model
        config_path: Path to config file
        n_episodes: Number of episodes to watch
        save_recordings: Save episode recordings to JSON/HTML
        real_time: Print updates in real-time
        delay: Delay between steps (seconds) for real-time viewing
    """
    print("=" * 80)
    print("🎮 WATCHING RL AGENT PLAY OPENFRONTIO")
    print("=" * 80)

    # Load model
    print(f"\nLoading model from: {model_path}")
    model = PPO.load(model_path)

    # Create environment
    print(f"Creating environment from: {config_path}")
    env = OpenFrontIOEnv(config_path=config_path)
    env = FlattenActionWrapper(env)  # Must match training wrapper

    # Create recordings directory
    if save_recordings:
        recordings_dir = Path('recordings')
        recordings_dir.mkdir(exist_ok=True)
        print(f"Recordings will be saved to: {recordings_dir}")

    for episode in range(n_episodes):
        print("\n" + "=" * 80)
        print(f"EPISODE {episode + 1}/{n_episodes}")
        print("=" * 80)

        recorder = EpisodeRecorder()
        recorder.reset()

        obs, info = env.reset()
        done = False
        step = 0
        episode_reward = 0

        print(f"\n🎬 Starting episode...")
        print(f"   Initial tiles: {info['tiles']}")
        print(f"   Initial troops: {info['troops']:.0f}")
        print(f"   Enemy tiles: {info['enemy_tiles']}")

        while not done:
            # Get action from model (flattened Box: [attack_target_continuous, attack_percentage])
            action, _ = model.predict(obs, deterministic=True)

            # Execute action
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            episode_reward += reward
            step += 1

            # Record frame
            recorder.record_frame(step, obs, action, reward, info)

            # Real-time display
            if real_time:
                # Parse flattened action
                attack_target = int(np.clip(np.round(action[0]), 0, 8))
                attack_pct = float(action[1]) * 100
                action_names = ['IDLE', 'ATK_N0', 'ATK_N1', 'ATK_N2', 'ATK_N3',
                              'ATK_N4', 'ATK_N5', 'ATK_N6', 'ATK_N7']
                action_str = f"{action_names[attack_target]}@{attack_pct:.0f}%"
                print(f"   Step {step:4d}: {action_str:12s} | "
                      f"Tiles: {info['tiles']:3d} | "
                      f"Enemy: {info['enemy_tiles']:3d} | "
                      f"Reward: {reward:8.2f} | "
                      f"Total: {episode_reward:10.2f}")

                if delay > 0:
                    time.sleep(delay)

        # Episode summary
        won = info.get('episode', {}).get('won', False)
        final_tiles = info['tiles']

        recorder.finalize(won, final_tiles)

        print("\n" + "-" * 80)
        print(f"📊 EPISODE SUMMARY")
        print("-" * 80)
        print(f"   Result: {'✅ VICTORY' if won else '❌ DEFEAT'}")
        print(f"   Total steps: {step}")
        print(f"   Total reward: {episode_reward:.2f}")
        print(f"   Final tiles: {final_tiles}")
        print(f"   Final troops: {info['troops']:.0f}")

        # Save recordings
        if save_recordings:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result = 'win' if won else 'loss'

            json_path = recordings_dir / f"episode_{episode+1}_{result}_{timestamp}.json"
            html_path = recordings_dir / f"episode_{episode+1}_{result}_{timestamp}.html"

            recorder.save_to_json(str(json_path))
            recorder.generate_html(str(html_path))

            print(f"\n📁 Recordings saved:")
            print(f"   JSON: {json_path}")
            print(f"   HTML: {html_path}")
            print(f"   Open HTML in browser to view interactive replay!")

    env.close()

    print("\n" + "=" * 80)
    print("✅ VISUALIZATION COMPLETE")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Visualize RL agent playing OpenFront.io')

    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model (.zip file)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/phase1_config.json',
        help='Path to config file'
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=1,
        help='Number of episodes to watch'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save episode recordings (JSON + HTML)'
    )
    parser.add_argument(
        '--no-realtime',
        action='store_true',
        help='Disable real-time step-by-step output'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.1,
        help='Delay between steps in seconds (for real-time viewing)'
    )

    args = parser.parse_args()

    watch_agent(
        model_path=args.model,
        config_path=args.config,
        n_episodes=args.episodes,
        save_recordings=args.save,
        real_time=not args.no_realtime,
        delay=args.delay
    )


if __name__ == '__main__':
    main()
