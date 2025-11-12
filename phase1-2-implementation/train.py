"""
Training script for Phase 1 - OpenFront.io RL Agent

This script trains a PPO agent with action masking on a small map.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import logging

# Add rl_env to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, CallbackList
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.env_checker import check_env

from openfrontio_env import OpenFrontIOEnv
from training_callback import CleanProgressCallback, CheckpointLogCallback
from flatten_action_wrapper import FlattenActionWrapper

# Setup logging - cleaner format for training
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of sub-modules
logging.getLogger('openfrontio_env').setLevel(logging.WARNING)  # Suppress episode logs
logging.getLogger('game_wrapper').setLevel(logging.WARNING)


def make_env(config_path: str):
    """
    Create and wrap environment.

    Args:
        config_path: Path to config file

    Returns:
        Wrapped environment
    """
    def _init():
        env = OpenFrontIOEnv(config_path=config_path)
        env = FlattenActionWrapper(env)  # Flatten Dict action space for SB3
        env = Monitor(env)
        return env
    return _init


def train(
    config_path: str,
    total_timesteps: int = None,
    eval_freq: int = 5000,
    save_freq: int = 10000,
    output_dir: str = None
):
    """
    Train PPO agent on OpenFront.io environment.

    Args:
        config_path: Path to configuration JSON
        total_timesteps: Total training timesteps (overrides config)
        eval_freq: Evaluation frequency
        save_freq: Checkpoint save frequency
        output_dir: Output directory for logs and checkpoints
    """

    # Load configuration
    logger.info(f"Loading configuration from {config_path}")
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Extract settings
    training_config = config['training']
    if total_timesteps is None:
        total_timesteps = training_config['total_timesteps']

    # Setup output directories
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(__file__),
            f"runs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'checkpoints'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Save config to output dir
    with open(os.path.join(output_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=2)

    # Create environment
    logger.info("Creating environment...")
    env = DummyVecEnv([make_env(config_path)])

    # Add observation normalization if enabled
    if training_config.get('normalize_observations', False):
        logger.info("Adding VecNormalize wrapper for observation normalization...")
        env = VecNormalize(
            env,
            norm_obs=True,      # Normalize observations
            norm_reward=False,  # Don't normalize rewards (we want to keep reward scale)
            clip_obs=10.0,      # Clip normalized obs to [-10, 10]
            clip_reward=10000.0 # Don't clip rewards (large terminal rewards)
        )

    # Create evaluation environment
    logger.info("Creating evaluation environment...")
    eval_env = DummyVecEnv([make_env(config_path)])

    # Add normalization to eval env (uses same stats as training env)
    if training_config.get('normalize_observations', False):
        eval_env = VecNormalize(
            eval_env,
            norm_obs=True,
            norm_reward=False,
            clip_obs=10.0,
            training=False  # Don't update stats during evaluation
        )

    # Check environment
    logger.info("Checking environment validity...")
    check_env(OpenFrontIOEnv(config_path), warn=True)
    logger.info("Environment check passed!")

    # Setup callbacks (verbose=0 to reduce clutter)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(output_dir, 'best_model'),
        log_path=os.path.join(output_dir, 'logs'),
        eval_freq=eval_freq,
        n_eval_episodes=10,
        deterministic=True,
        render=False,
        verbose=0  # Reduce verbosity - our custom callback will report
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path=os.path.join(output_dir, 'checkpoints'),
        name_prefix='ppo_openfrontio',
        save_replay_buffer=False,
        save_vecnormalize=True,  # Save normalization stats with checkpoints
        verbose=0  # Reduce verbosity - our custom callback will report
    )

    # Clean progress callback for periodic summaries
    progress_callback = CleanProgressCallback(
        report_freq=5000,
        total_timesteps=total_timesteps,
        verbose=0
    )

    # Checkpoint logging callback
    checkpoint_log_callback = CheckpointLogCallback(verbose=0)

    callbacks = CallbackList([
        eval_callback,
        checkpoint_callback,
        progress_callback,
        checkpoint_log_callback
    ])

    # Create learning rate schedule if specified
    learning_rate = training_config['learning_rate']
    lr_schedule_type = training_config.get('learning_rate_schedule', None)

    if lr_schedule_type == 'linear':
        # Linear decay from learning_rate to 0
        initial_lr = learning_rate
        def lr_schedule(progress_remaining: float) -> float:
            """Linear learning rate schedule

            Args:
                progress_remaining: Progress will decrease from 1 (beginning) to 0 (end)

            Returns:
                Current learning rate
            """
            return progress_remaining * initial_lr

        learning_rate = lr_schedule
        logger.info(f"Using linear learning rate schedule: {initial_lr} → 0")
    else:
        logger.info(f"Using constant learning rate: {learning_rate}")

    # Create PPO model
    logger.info("Creating PPO model...")
    model = PPO(
        policy='MultiInputPolicy',  # Required for Dict observation space (obs is still Dict)
        env=env,
        learning_rate=learning_rate,  # Can be float or callable
        n_steps=training_config['n_steps'],
        batch_size=training_config['batch_size'],
        n_epochs=training_config['n_epochs'],
        gamma=training_config['gamma'],
        gae_lambda=training_config['gae_lambda'],
        clip_range=training_config['clip_range'],
        ent_coef=training_config['ent_coef'],
        vf_coef=training_config['vf_coef'],
        max_grad_norm=training_config['max_grad_norm'],
        verbose=0,  # Disable verbose episode logging - use custom callback instead
        tensorboard_log=os.path.join(output_dir, 'tensorboard')
    )

    logger.info("=" * 80)
    logger.info("TRAINING CONFIGURATION")
    logger.info("=" * 80)
    logger.info(f"Algorithm: PPO")
    logger.info(f"Total timesteps: {total_timesteps:,}")
    logger.info(f"Learning rate: {training_config['learning_rate']}")
    logger.info(f"Batch size: {training_config['batch_size']}")
    logger.info(f"Environment: OpenFront.io Phase 1")
    logger.info(f"Map: {config['game']['map_name']}")
    logger.info(f"Difficulty: {config['game']['opponent_difficulty']}")
    logger.info(f"Action space: Discrete(9) with masking")
    logger.info(f"Observation space: Dict(features=Box(5), mask=Box(9))")
    logger.info("=" * 80)

    # Train
    logger.info("Starting training...")
    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True
        )

        logger.info("Training completed successfully!")

        # Save final model
        final_model_path = os.path.join(output_dir, 'final_model.zip')
        model.save(final_model_path)
        logger.info(f"Final model saved to {final_model_path}")

    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        interrupt_model_path = os.path.join(output_dir, 'interrupted_model.zip')
        model.save(interrupt_model_path)
        logger.info(f"Model saved to {interrupt_model_path}")

    finally:
        # Cleanup
        env.close()
        eval_env.close()
        logger.info("Environments closed")

    logger.info(f"Training artifacts saved to: {output_dir}")
    logger.info("Training complete!")


def evaluate(model_path: str, config_path: str, n_episodes: int = 10):
    """
    Evaluate a trained model.

    Args:
        model_path: Path to trained model
        config_path: Path to config file
        n_episodes: Number of episodes to evaluate
    """
    logger.info(f"Loading model from {model_path}")
    model = PPO.load(model_path)

    logger.info("Creating evaluation environment...")
    env = OpenFrontIOEnv(config_path=config_path)

    logger.info(f"Evaluating for {n_episodes} episodes...")
    episode_rewards = []
    episode_lengths = []
    wins = 0

    for episode in range(n_episodes):
        obs, info = env.reset()
        done = False
        episode_reward = 0
        steps = 0

        while not done:
            # Get action from model
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)

            episode_reward += reward
            steps += 1
            done = terminated or truncated

        episode_rewards.append(episode_reward)
        episode_lengths.append(steps)

        if info.get('episode', {}).get('won', False):
            wins += 1

        logger.info(
            f"Episode {episode+1}/{n_episodes}: "
            f"reward={episode_reward:.1f}, "
            f"length={steps}, "
            f"tiles={info.get('tiles', 0)}, "
            f"won={info.get('episode', {}).get('won', False)}"
        )

    env.close()

    # Print summary
    logger.info("=" * 80)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Episodes: {n_episodes}")
    logger.info(f"Mean reward: {sum(episode_rewards)/n_episodes:.2f}")
    logger.info(f"Mean length: {sum(episode_lengths)/n_episodes:.1f}")
    logger.info(f"Win rate: {wins/n_episodes*100:.1f}%")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Train PPO agent on OpenFront.io')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train a new agent')
    train_parser.add_argument(
        '--config',
        type=str,
        default='configs/phase1_config.json',
        help='Path to configuration file'
    )
    train_parser.add_argument(
        '--timesteps',
        type=int,
        default=None,
        help='Total timesteps to train (overrides config)'
    )
    train_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory'
    )

    # Evaluate command
    eval_parser = subparsers.add_parser('eval', help='Evaluate a trained agent')
    eval_parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model'
    )
    eval_parser.add_argument(
        '--config',
        type=str,
        default='configs/phase1_config.json',
        help='Path to configuration file'
    )
    eval_parser.add_argument(
        '--episodes',
        type=int,
        default=10,
        help='Number of episodes to evaluate'
    )

    args = parser.parse_args()

    if args.command == 'train':
        train(
            config_path=args.config,
            total_timesteps=args.timesteps,
            output_dir=args.output
        )
    elif args.command == 'eval':
        evaluate(
            model_path=args.model,
            config_path=args.config,
            n_episodes=args.episodes
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
