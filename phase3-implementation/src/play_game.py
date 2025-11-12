"""
Play Game - Watch your trained model in action!

This script loads a trained model and plays a game while providing:
1. Real-time game statistics
2. Action explanations
3. Detailed state tracking
4. Optional game replay saving
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

import numpy as np
from stable_baselines3 import PPO

from environment import OpenFrontEnv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameVisualizer:
    """Visualizer for watching trained model play"""

    def __init__(self, model: PPO, num_bots: int = 10, save_replay: bool = False):
        """
        Initialize visualizer.

        Args:
            model: Trained PPO model
            num_bots: Number of bot opponents
            save_replay: Whether to save replay data
        """
        self.model = model
        self.num_bots = num_bots
        self.save_replay = save_replay
        self.replay_data = []

    def play_game(self, max_steps: int = 10000, step_delay: float = 0.0):
        """
        Play one game with visualization.

        Args:
            max_steps: Maximum steps before truncation
            step_delay: Delay between steps (seconds) for watching

        Returns:
            Game statistics dict
        """
        # Create environment
        env = OpenFrontEnv(num_bots=self.num_bots)

        # Reset
        obs, info = env.reset()

        # Game stats
        stats = {
            'total_reward': 0.0,
            'steps': 0,
            'actions_taken': [],
            'territory_history': [],
            'population_history': [],
            'rank_history': [],
            'max_territory': 0.0,
            'max_population': 0,
            'survival_time': 0
        }

        print("\n" + "="*80)
        print(f"🎮 GAME START - {self.num_bots} Opponents")
        print("="*80)

        done = False
        step = 0

        try:
            while not done and step < max_steps:
                # Get action from model
                action, _states = self.model.predict(obs, deterministic=True)

                # Execute action
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

                # Update stats
                stats['total_reward'] += reward
                stats['steps'] += 1
                stats['actions_taken'].append(info)

                # Extract state info
                state = env._get_game_state()
                if state is not None:
                    territory_pct = getattr(state, 'territory_pct', 0.0) * 100
                    population = getattr(state, 'population', 0)
                    rank = getattr(state, 'rank', self.num_bots + 1)

                    stats['territory_history'].append(territory_pct)
                    stats['population_history'].append(population)
                    stats['rank_history'].append(rank)
                    stats['max_territory'] = max(stats['max_territory'], territory_pct)
                    stats['max_population'] = max(stats['max_population'], population)

                    # Print update every 100 steps
                    if step % 100 == 0:
                        self._print_status(step, territory_pct, population, rank, reward, info)

                    # Save replay frame
                    if self.save_replay:
                        self.replay_data.append({
                            'step': step,
                            'action': int(action),
                            'direction': info.get('direction', 'UNKNOWN'),
                            'intensity': info.get('intensity', 0.0),
                            'build': info.get('build', False),
                            'territory_pct': territory_pct,
                            'population': population,
                            'rank': rank,
                            'reward': float(reward)
                        })

                step += 1

                # Delay for watching (optional)
                if step_delay > 0:
                    time.sleep(step_delay)

        except KeyboardInterrupt:
            print("\n⚠️  Game interrupted by user")
        except Exception as e:
            logger.error(f"Error during game: {e}")
        finally:
            env.close()

        # Final stats
        stats['survival_time'] = step
        self._print_final_stats(stats, terminated)

        # Save replay if requested
        if self.save_replay and self.replay_data:
            self._save_replay()

        return stats

    def _print_status(self, step: int, territory: float, population: int,
                     rank: int, reward: float, info: Dict[str, Any]):
        """Print current game status"""
        direction = info.get('direction', 'UNKNOWN')
        intensity = info.get('intensity', 0.0)
        build = info.get('build', False)

        print(f"[Step {step:5d}] "
              f"Territory: {territory:5.1f}% | "
              f"Population: {population:6d} | "
              f"Rank: {rank:2d}/{self.num_bots+1} | "
              f"Action: {direction:4s}@{intensity:.0%} {'🏗️ ' if build else '   '} | "
              f"Reward: {reward:+7.2f}")

    def _print_final_stats(self, stats: Dict[str, Any], won: bool):
        """Print final game statistics"""
        print("\n" + "="*80)
        print("📊 GAME OVER")
        print("="*80)

        result = "🏆 VICTORY" if won else "💀 ELIMINATED"
        print(f"Result: {result}")
        print(f"Survival Time: {stats['survival_time']:,} steps")
        print(f"Total Reward: {stats['total_reward']:+.2f}")
        print(f"Max Territory: {stats['max_territory']:.1f}%")
        print(f"Max Population: {stats['max_population']:,}")

        if stats['rank_history']:
            best_rank = min(stats['rank_history'])
            final_rank = stats['rank_history'][-1] if stats['rank_history'] else self.num_bots + 1
            print(f"Best Rank: {best_rank}/{self.num_bots+1}")
            print(f"Final Rank: {final_rank}/{self.num_bots+1}")

        # Action breakdown
        if stats['actions_taken']:
            directions = [a['direction'] for a in stats['actions_taken']]
            unique_dirs = set(directions)
            print("\nAction Distribution:")
            for direction in sorted(unique_dirs):
                count = directions.count(direction)
                pct = 100.0 * count / len(directions)
                print(f"  {direction:4s}: {count:5d} ({pct:5.1f}%)")

        print("="*80 + "\n")

    def _save_replay(self):
        """Save replay data to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        replay_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'replays'
        )
        os.makedirs(replay_dir, exist_ok=True)

        replay_path = os.path.join(replay_dir, f'replay_{timestamp}.json')

        with open(replay_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'num_bots': self.num_bots,
                'frames': self.replay_data
            }, f, indent=2)

        print(f"💾 Replay saved to: {replay_path}")


def play_multiple_games(
    model_path: str,
    num_games: int = 5,
    num_bots: int = 10,
    step_delay: float = 0.0,
    save_replays: bool = False
):
    """
    Play multiple games and aggregate statistics.

    Args:
        model_path: Path to trained model
        num_games: Number of games to play
        num_bots: Number of bot opponents
        step_delay: Delay between steps
        save_replays: Save replay files
    """
    # Load model
    print(f"Loading model from: {model_path}")
    model = PPO.load(model_path)
    print("✓ Model loaded successfully\n")

    # Play games
    all_stats = []
    wins = 0

    for game_num in range(1, num_games + 1):
        print(f"\n{'='*80}")
        print(f"GAME {game_num}/{num_games}")
        print(f"{'='*80}\n")

        visualizer = GameVisualizer(model, num_bots, save_replays)
        stats = visualizer.play_game(step_delay=step_delay)
        all_stats.append(stats)

        # Check if won (80% territory or survived to end with high rank)
        if stats['max_territory'] >= 80.0:
            wins += 1

        # Brief pause between games
        if game_num < num_games:
            time.sleep(1)

    # Print aggregate statistics
    print("\n" + "="*80)
    print("📈 AGGREGATE STATISTICS")
    print("="*80)
    print(f"Games Played: {num_games}")
    print(f"Wins: {wins} ({100.0*wins/num_games:.1f}%)")

    avg_reward = np.mean([s['total_reward'] for s in all_stats])
    avg_survival = np.mean([s['survival_time'] for s in all_stats])
    avg_max_territory = np.mean([s['max_territory'] for s in all_stats])

    print(f"Avg Reward: {avg_reward:+.2f}")
    print(f"Avg Survival Time: {avg_survival:.0f} steps")
    print(f"Avg Max Territory: {avg_max_territory:.1f}%")

    if all_stats[0]['rank_history']:
        all_best_ranks = [min(s['rank_history']) if s['rank_history'] else num_bots+1
                         for s in all_stats]
        avg_best_rank = np.mean(all_best_ranks)
        print(f"Avg Best Rank: {avg_best_rank:.1f}/{num_bots+1}")

    print("="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Watch your trained OpenFront.io RL agent play!'
    )
    parser.add_argument(
        'model_path',
        type=str,
        help='Path to trained model (.zip file)'
    )
    parser.add_argument(
        '--num-games',
        type=int,
        default=1,
        help='Number of games to play (default: 1)'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=10,
        help='Number of bot opponents (default: 10)'
    )
    parser.add_argument(
        '--step-delay',
        type=float,
        default=0.0,
        help='Delay between steps in seconds (default: 0.0, set to 0.1 for slow-motion)'
    )
    parser.add_argument(
        '--save-replays',
        action='store_true',
        help='Save replay data to JSON files'
    )

    args = parser.parse_args()

    # Check model exists
    if not os.path.exists(args.model_path):
        print(f"❌ Error: Model not found at {args.model_path}")
        sys.exit(1)

    # Play games
    play_multiple_games(
        model_path=args.model_path,
        num_games=args.num_games,
        num_bots=args.num_bots,
        step_delay=args.step_delay,
        save_replays=args.save_replays
    )


if __name__ == "__main__":
    main()
