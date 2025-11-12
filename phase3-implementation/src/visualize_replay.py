"""
Replay Visualizer - Display saved game replays

Creates visualizations from saved replay JSON files:
1. ASCII map visualization
2. Statistics graphs (matplotlib)
3. Frame-by-frame playback
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not installed - graphs will be disabled")
    print("   Install with: pip install matplotlib")


def load_replay(replay_path: str) -> Dict[str, Any]:
    """Load replay data from JSON file"""
    with open(replay_path, 'r') as f:
        return json.load(f)


def print_ascii_map(territory_pct: float, population: int, rank: int, total_players: int):
    """
    Print simple ASCII visualization of current state.

    Args:
        territory_pct: Territory percentage (0-100)
        population: Current population
        rank: Current rank
        total_players: Total number of players
    """
    # Territory bar
    bar_width = 50
    filled = int(territory_pct / 100.0 * bar_width)
    empty = bar_width - filled

    territory_bar = '█' * filled + '░' * empty

    # Status display
    print(f"Territory: [{territory_bar}] {territory_pct:.1f}%")
    print(f"Population: {population:,}")
    print(f"Rank: {rank}/{total_players}")


def visualize_statistics(replay_data: Dict[str, Any]):
    """
    Create matplotlib graphs of game statistics.

    Args:
        replay_data: Loaded replay data
    """
    if not HAS_MATPLOTLIB:
        print("Cannot create graphs - matplotlib not installed")
        return

    frames = replay_data['frames']

    # Extract data
    steps = [f['step'] for f in frames]
    territory = [f['territory_pct'] for f in frames]
    population = [f['population'] for f in frames]
    ranks = [f['rank'] for f in frames]
    rewards = [f['reward'] for f in frames]

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f"Game Replay - {replay_data['timestamp']}\n"
                 f"Opponents: {replay_data['num_bots']}", fontsize=14)

    # Territory over time
    axes[0, 0].plot(steps, territory, 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Step')
    axes[0, 0].set_ylabel('Territory %')
    axes[0, 0].set_title('Territory Control')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=80, color='g', linestyle='--', alpha=0.5, label='Victory threshold')
    axes[0, 0].legend()

    # Population over time
    axes[0, 1].plot(steps, population, 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Step')
    axes[0, 1].set_ylabel('Population')
    axes[0, 1].set_title('Population')
    axes[0, 1].grid(True, alpha=0.3)

    # Rank over time (lower is better)
    axes[1, 0].plot(steps, ranks, 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Step')
    axes[1, 0].set_ylabel('Rank')
    axes[1, 0].set_title('Rank (lower is better)')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].invert_yaxis()  # Lower rank at top

    # Rewards over time
    axes[1, 1].plot(steps, rewards, 'm-', linewidth=1, alpha=0.7)
    axes[1, 1].set_xlabel('Step')
    axes[1, 1].set_ylabel('Reward')
    axes[1, 1].set_title('Reward per Step')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=0, color='k', linestyle='-', alpha=0.3)

    # Add cumulative reward
    cumulative_reward = np.cumsum(rewards)
    ax2 = axes[1, 1].twinx()
    ax2.plot(steps, cumulative_reward, 'c-', linewidth=2, alpha=0.5, label='Cumulative')
    ax2.set_ylabel('Cumulative Reward', color='c')
    ax2.tick_params(axis='y', labelcolor='c')

    plt.tight_layout()

    # Save figure
    output_dir = os.path.dirname(replay_data.get('replay_path', '.'))
    output_path = os.path.join(output_dir, f"replay_{replay_data['timestamp']}_stats.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"📊 Statistics saved to: {output_path}")

    plt.show()


def play_replay_interactive(replay_data: Dict[str, Any], frame_delay: float = 0.1):
    """
    Play replay frame-by-frame with ASCII visualization.

    Args:
        replay_data: Loaded replay data
        frame_delay: Delay between frames in seconds
    """
    import time

    frames = replay_data['frames']
    num_bots = replay_data['num_bots']
    total_players = num_bots + 1

    print("\n" + "="*80)
    print(f"🎬 REPLAY PLAYBACK - {len(frames)} frames")
    print(f"Timestamp: {replay_data['timestamp']}")
    print(f"Opponents: {num_bots}")
    print("="*80 + "\n")

    try:
        for i, frame in enumerate(frames):
            # Clear screen (ANSI escape code)
            print("\033[2J\033[H", end='')

            # Print frame header
            print(f"Frame {i+1}/{len(frames)} - Step {frame['step']}")
            print("-" * 80)

            # Action info
            direction = frame['direction']
            intensity = frame['intensity']
            build = '🏗️ ' if frame['build'] else ''
            print(f"Action: {direction} @ {intensity:.0%} {build}")
            print(f"Reward: {frame['reward']:+.2f}")
            print()

            # State visualization
            print_ascii_map(
                frame['territory_pct'],
                frame['population'],
                frame['rank'],
                total_players
            )

            print("-" * 80)

            time.sleep(frame_delay)

    except KeyboardInterrupt:
        print("\n⚠️  Playback interrupted")


def summarize_replay(replay_data: Dict[str, Any]):
    """
    Print summary statistics for a replay.

    Args:
        replay_data: Loaded replay data
    """
    frames = replay_data['frames']

    if not frames:
        print("Empty replay")
        return

    # Calculate stats
    total_steps = frames[-1]['step']
    total_reward = sum(f['reward'] for f in frames)
    max_territory = max(f['territory_pct'] for f in frames)
    max_population = max(f['population'] for f in frames)
    best_rank = min(f['rank'] for f in frames)
    final_rank = frames[-1]['rank']

    # Action distribution
    actions = [f['direction'] for f in frames]
    unique_actions = set(actions)

    # Victory check
    won = max_territory >= 80.0

    # Print summary
    print("\n" + "="*80)
    print("📋 REPLAY SUMMARY")
    print("="*80)
    print(f"Timestamp: {replay_data['timestamp']}")
    print(f"Opponents: {replay_data['num_bots']}")
    print(f"Result: {'🏆 VICTORY' if won else '💀 ELIMINATED'}")
    print()
    print(f"Duration: {total_steps:,} steps")
    print(f"Total Reward: {total_reward:+.2f}")
    print(f"Max Territory: {max_territory:.1f}%")
    print(f"Max Population: {max_population:,}")
    print(f"Best Rank: {best_rank}/{replay_data['num_bots']+1}")
    print(f"Final Rank: {final_rank}/{replay_data['num_bots']+1}")
    print()
    print("Action Distribution:")
    for action in sorted(unique_actions):
        count = actions.count(action)
        pct = 100.0 * count / len(actions)
        print(f"  {action:4s}: {count:5d} ({pct:5.1f}%)")
    print("="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Visualize OpenFront.io game replays'
    )
    parser.add_argument(
        'replay_path',
        type=str,
        help='Path to replay JSON file'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['summary', 'play', 'graphs', 'all'],
        default='all',
        help='Visualization mode (default: all)'
    )
    parser.add_argument(
        '--frame-delay',
        type=float,
        default=0.1,
        help='Delay between frames in play mode (default: 0.1s)'
    )

    args = parser.parse_args()

    # Check file exists
    if not os.path.exists(args.replay_path):
        print(f"❌ Error: Replay file not found: {args.replay_path}")
        sys.exit(1)

    # Load replay
    print(f"Loading replay from: {args.replay_path}")
    replay_data = load_replay(args.replay_path)
    replay_data['replay_path'] = args.replay_path
    print(f"✓ Loaded {len(replay_data['frames'])} frames\n")

    # Execute visualization
    if args.mode in ['summary', 'all']:
        summarize_replay(replay_data)

    if args.mode in ['graphs', 'all']:
        visualize_statistics(replay_data)

    if args.mode in ['play', 'all']:
        if args.mode == 'all':
            input("Press Enter to start replay playback...")
        play_replay_interactive(replay_data, args.frame_delay)


if __name__ == "__main__":
    main()
