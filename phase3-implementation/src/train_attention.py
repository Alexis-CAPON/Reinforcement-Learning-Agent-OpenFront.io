"""
Training Script for Phase 3 - Battle Royale (WITH ATTENTION)

Features:
- ✨ Improved architecture with attention mechanisms (~500K params)
- ✨ Spatial attention in CNN (focus on borders/threats)
- ✨ Cross-attention fusion (link map and global features)
- Curriculum learning: 10 → 25 → 50 bots
- PPO algorithm with custom feature extractor
- Parallel environments for faster training
- Checkpointing and evaluation
"""

import os
import sys
import argparse
from datetime import datetime
import logging
from typing import Optional

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, CallbackList
from stable_baselines3.common.monitor import Monitor

from environment import OpenFrontEnv
from model_attention import BattleRoyaleExtractorWithAttention  # ← Use attention model
from training_callback import DetailedLoggingCallback
from best_model_callback import SaveBestModelCallback  # ← Save best model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def make_env(num_bots: int, game_interface=None):
    """
    Create environment factory for vectorized environments.

    Args:
        num_bots: Number of bot opponents
        game_interface: Game interface/wrapper

    Returns:
        Environment factory function
    """
    def _init():
        env = OpenFrontEnv(game_interface=game_interface, num_bots=num_bots)
        env = Monitor(env)
        return env
    return _init


def train_curriculum_phase(
    model: Optional[PPO],
    num_bots: int,
    total_timesteps: int,
    n_envs: int,
    output_dir: str,
    phase_name: str,
    device: str = 'cpu'
) -> PPO:
    """
    Train one phase of curriculum learning.

    Args:
        model: Existing model to continue training (or None for new)
        num_bots: Number of bots for this phase
        total_timesteps: Training steps for this phase
        n_envs: Number of parallel environments
        output_dir: Output directory
        phase_name: Name of this phase (for logging)
        device: Device to use ('cpu', 'cuda', or 'mps')

    Returns:
        Trained model
    """
    logger.info(f"=" * 60)
    logger.info(f"Starting {phase_name}: {num_bots} bots, {total_timesteps:,} steps")
    logger.info(f"=" * 60)

    # Create parallel environments
    logger.info(f"Creating {n_envs} parallel environments...")
    env = SubprocVecEnv([make_env(num_bots) for _ in range(n_envs)])

    # Create or update model
    if model is None:
        logger.info("Creating new PPO model...")
        model = PPO(
            policy="MultiInputPolicy",
            env=env,
            learning_rate=1e-4,  # REDUCED: Prevent overshooting good policies (was 3e-4)
            n_steps=1024,
            batch_size=128,
            n_epochs=10,
            gamma=0.995,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.005,  # REDUCED: Minimize exploration once good strategies found (was 0.01)
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs={
                'features_extractor_class': BattleRoyaleExtractorWithAttention,  # ← Attention model
                'features_extractor_kwargs': {'features_dim': 256}
            },
            verbose=1,
            device=device,
            tensorboard_log=os.path.join(output_dir, 'logs')
        )
    else:
        logger.info("Continuing with existing model...")
        model.set_env(env)

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000 // n_envs,
        save_path=os.path.join(output_dir, 'checkpoints', phase_name),
        name_prefix=f'{phase_name}_model'
    )

    # Detailed logging callback
    logging_callback = DetailedLoggingCallback(verbose=1)

    # Best model callback (saves model with highest mean reward)
    best_model_callback = SaveBestModelCallback(
        save_path=os.path.join(output_dir, 'checkpoints', phase_name, 'best_model'),
        verbose=1
    )

    callbacks = CallbackList([checkpoint_callback, logging_callback, best_model_callback])

    # Train
    logger.info(f"Starting training for {total_timesteps:,} timesteps...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=callbacks,
        progress_bar=True,
        tb_log_name=phase_name
    )

    # Save phase checkpoint
    save_path = os.path.join(output_dir, 'checkpoints', f'{phase_name}_final')
    model.save(save_path)
    logger.info(f"Saved {phase_name} model to {save_path}")

    # Clean up
    env.close()

    return model


def train(
    output_dir: Optional[str] = None,
    device: str = 'cpu',
    n_envs: int = 8,
    curriculum: bool = True
):
    """
    Main training function with curriculum learning.

    Args:
        output_dir: Output directory for logs and checkpoints
        device: Device to use ('cpu', 'cuda', or 'mps')
        n_envs: Number of parallel environments
        curriculum: Whether to use curriculum learning
    """
    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'runs',
            f'run_{timestamp}'
        )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'checkpoints'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device}")
    logger.info(f"Parallel environments: {n_envs}")

    if curriculum:
        # Phase 1: Learn basics (10 bots, 100K steps)
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: Learn Basics")
        logger.info("=" * 60)
        model = train_curriculum_phase(
            model=None,
            num_bots=10,
            total_timesteps=100_000,
            n_envs=n_envs,
            output_dir=output_dir,
            phase_name='phase1_basics',
            device=device
        )

        # Phase 2: Handle competition (25 bots, 300K steps)
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: Handle Competition")
        logger.info("=" * 60)
        model = train_curriculum_phase(
            model=model,
            num_bots=25,
            total_timesteps=300_000,
            n_envs=n_envs,
            output_dir=output_dir,
            phase_name='phase2_competition',
            device=device
        )

        # Phase 3: Full challenge (50 bots, 500K steps)
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: Full Challenge")
        logger.info("=" * 60)
        model = train_curriculum_phase(
            model=model,
            num_bots=50,
            total_timesteps=500_000,
            n_envs=n_envs,
            output_dir=output_dir,
            phase_name='phase3_challenge',
            device=device
        )
    else:
        # Single phase training (50 bots, 900K steps)
        logger.info("\n" + "=" * 60)
        logger.info("SINGLE PHASE TRAINING")
        logger.info("=" * 60)
        model = train_curriculum_phase(
            model=None,
            num_bots=50,
            total_timesteps=900_000,
            n_envs=n_envs,
            output_dir=output_dir,
            phase_name='full_training',
            device=device
        )

    # Save final model
    final_path = os.path.join(output_dir, 'openfront_final')
    model.save(final_path)
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Training complete!")
    logger.info(f"Final model saved to: {final_path}")
    logger.info(f"{'=' * 60}\n")

    return model


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Train OpenFront.io RL agent with curriculum learning'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for logs and checkpoints'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        choices=['cpu', 'cuda', 'mps'],
        help='Device to use for training'
    )
    parser.add_argument(
        '--n-envs',
        type=int,
        default=8,
        help='Number of parallel environments'
    )
    parser.add_argument(
        '--no-curriculum',
        action='store_true',
        help='Disable curriculum learning (train on 50 bots from start)'
    )
    parser.add_argument(
        '--total-timesteps',
        type=int,
        default=None,
        help='Override total timesteps (default: 900K for curriculum, uses config otherwise)'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=None,
        help='Number of bots (only used with --no-curriculum)'
    )

    args = parser.parse_args()

    # Start training
    if args.no_curriculum and args.total_timesteps:
        # Single phase training with custom timesteps
        logger.info(f"Single phase training: {args.num_bots or 50} bots, {args.total_timesteps:,} steps")
        output_dir = args.output_dir or os.path.join(
            os.path.dirname(__file__),
            '..',
            'runs',
            f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'checkpoints'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)

        train_curriculum_phase(
            model=None,
            num_bots=args.num_bots or 50,
            total_timesteps=args.total_timesteps,
            n_envs=args.n_envs,
            output_dir=output_dir,
            phase_name='single_phase',
            device=args.device
        )
    else:
        # Use regular training function
        train(
            output_dir=args.output_dir,
            device=args.device,
            n_envs=args.n_envs,
            curriculum=not args.no_curriculum
        )


if __name__ == "__main__":
    main()
