"""
Evaluation Script for Phase 3 - Battle Royale

Evaluates trained model on multiple episodes and reports metrics:
- Win rate
- Average rank
- Average territory
- Survival time
"""

import argparse
import logging
from typing import Dict, List
import numpy as np

from stable_baselines3 import PPO
from environment import OpenFrontEnv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate(
    model_path: str,
    n_episodes: int = 50,
    num_bots: int = 50,
    deterministic: bool = True
) -> Dict[str, float]:
    """
    Evaluate trained model.

    Args:
        model_path: Path to saved model (without .zip extension)
        n_episodes: Number of episodes to evaluate
        num_bots: Number of bot opponents
        deterministic: Use deterministic actions

    Returns:
        Dictionary with evaluation metrics
    """
    logger.info(f"Loading model from {model_path}...")
    model = PPO.load(model_path)

    logger.info(f"Creating environment with {num_bots} bots...")
    env = OpenFrontEnv(game_interface=None, num_bots=num_bots)

    logger.info(f"Starting evaluation for {n_episodes} episodes...")
    logger.info("=" * 60)

    results = []

    for episode in range(n_episodes):
        obs, _ = env.reset()
        done = False
        episode_reward = 0
        episode_steps = 0

        while not done:
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, reward, done, _, info = env.step(action)
            episode_reward += reward
            episode_steps += 1

        # Extract episode info
        state = env._get_game_state()

        episode_result = {
            'episode': episode + 1,
            'reward': episode_reward,
            'steps': episode_steps,
            'territory_pct': getattr(state, 'territory_pct', 0.0) if state else 0.0,
            'won': getattr(state, 'territory_pct', 0.0) >= 0.80 if state else False,
            'rank': getattr(state, 'rank', num_bots) if state else num_bots
        }

        results.append(episode_result)

        # Log episode
        logger.info(
            f"Episode {episode + 1:3d}: "
            f"Reward={episode_reward:8.1f}, "
            f"Steps={episode_steps:4d}, "
            f"Territory={episode_result['territory_pct']:.2%}, "
            f"Rank={episode_result['rank']:2.0f}, "
            f"Won={episode_result['won']}"
        )

    env.close()

    # Compute statistics
    win_rate = sum(r['won'] for r in results) / n_episodes
    avg_reward = np.mean([r['reward'] for r in results])
    std_reward = np.std([r['reward'] for r in results])
    avg_territory = np.mean([r['territory_pct'] for r in results])
    avg_rank = np.mean([r['rank'] for r in results])
    avg_steps = np.mean([r['steps'] for r in results])

    # Log summary
    logger.info("=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Episodes:         {n_episodes}")
    logger.info(f"Bot opponents:    {num_bots}")
    logger.info(f"")
    logger.info(f"Win rate:         {win_rate:.2%}")
    logger.info(f"Average rank:     {avg_rank:.1f} / {num_bots}")
    logger.info(f"Average territory:{avg_territory:.2%}")
    logger.info(f"Average steps:    {avg_steps:.1f}")
    logger.info(f"Average reward:   {avg_reward:.1f} ± {std_reward:.1f}")
    logger.info("=" * 60)

    metrics = {
        'win_rate': win_rate,
        'avg_rank': avg_rank,
        'avg_territory': avg_territory,
        'avg_reward': avg_reward,
        'std_reward': std_reward,
        'avg_steps': avg_steps
    }

    return metrics


def compare_models(
    model_paths: List[str],
    n_episodes: int = 50,
    num_bots: int = 50
):
    """
    Compare multiple models.

    Args:
        model_paths: List of model paths to compare
        n_episodes: Number of episodes per model
        num_bots: Number of bot opponents
    """
    logger.info(f"Comparing {len(model_paths)} models...")
    logger.info("=" * 60)

    all_metrics = []

    for i, model_path in enumerate(model_paths):
        logger.info(f"\nModel {i+1}/{len(model_paths)}: {model_path}")
        logger.info("-" * 60)

        metrics = evaluate(
            model_path=model_path,
            n_episodes=n_episodes,
            num_bots=num_bots
        )

        metrics['model_path'] = model_path
        all_metrics.append(metrics)

    # Print comparison table
    logger.info("\n" + "=" * 60)
    logger.info("MODEL COMPARISON")
    logger.info("=" * 60)

    for i, metrics in enumerate(all_metrics):
        logger.info(f"\nModel {i+1}: {metrics['model_path']}")
        logger.info(f"  Win rate:     {metrics['win_rate']:.2%}")
        logger.info(f"  Avg rank:     {metrics['avg_rank']:.1f}")
        logger.info(f"  Avg territory:{metrics['avg_territory']:.2%}")
        logger.info(f"  Avg reward:   {metrics['avg_reward']:.1f}")

    logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Evaluate OpenFront.io RL agent'
    )
    parser.add_argument(
        'model_path',
        type=str,
        help='Path to saved model (without .zip extension)'
    )
    parser.add_argument(
        '--n-episodes',
        type=int,
        default=50,
        help='Number of episodes to evaluate'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=50,
        help='Number of bot opponents'
    )
    parser.add_argument(
        '--stochastic',
        action='store_true',
        help='Use stochastic (non-deterministic) actions'
    )
    parser.add_argument(
        '--compare',
        type=str,
        nargs='+',
        help='Compare multiple models (provide multiple paths)'
    )

    args = parser.parse_args()

    if args.compare:
        # Compare multiple models
        compare_models(
            model_paths=args.compare,
            n_episodes=args.n_episodes,
            num_bots=args.num_bots
        )
    else:
        # Evaluate single model
        evaluate(
            model_path=args.model_path,
            n_episodes=args.n_episodes,
            num_bots=args.num_bots,
            deterministic=not args.stochastic
        )


if __name__ == "__main__":
    main()
