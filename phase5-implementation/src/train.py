"""
Phase 5 Training Script - Clean Implementation with GPU Support

Features:
- GPU support with automatic device detection (CUDA/MPS/CPU)
- Train from scratch OR continue from Phase 3/4 models
- Configurable map and number of bots
- Optional self-play training
- Clean implementation with working attacks
- Optimized for GPU training
"""

import os
import sys
import argparse
from datetime import datetime
import logging
from typing import Optional
import torch

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from stable_baselines3.common.monitor import Monitor

from environment import OpenFrontEnv
from self_play_env import SelfPlayEnv
from model import BattleRoyaleExtractorWithAttention
from training_callback import DetailedLoggingCallback
from best_model_callback import SaveBestModelCallback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_device() -> str:
    """
    Automatically detect the best available device.

    Returns:
        Device string: 'cuda', 'mps', or 'cpu'
    """
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"🚀 CUDA GPU detected: {gpu_name}")
        logger.info(f"   GPU Memory: {gpu_memory:.2f} GB")
    elif torch.backends.mps.is_available():
        device = 'mps'
        logger.info("🚀 Apple Metal (MPS) detected")
    else:
        device = 'cpu'
        logger.warning("⚠️  No GPU detected, using CPU (training will be slow)")

    return device


def get_gpu_memory_usage():
    """Get current GPU memory usage if CUDA is available."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1e9
        reserved = torch.cuda.memory_reserved(0) / 1e9
        return f"Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB"
    return "N/A (No CUDA GPU)"


def make_env(
    num_bots: int,
    map_name: str = 'plains',
    use_self_play: bool = False,
    game_interface=None
):
    """
    Create environment factory for vectorized environments.

    Args:
        num_bots: Number of bot opponents
        map_name: Name of the map to use
        use_self_play: Whether to use self-play
        game_interface: Game interface/wrapper

    Returns:
        Environment factory function
    """
    def _init():
        if use_self_play:
            env = SelfPlayEnv(
                game_interface=game_interface,
                num_bots=num_bots,
                map_name=map_name
            )
        else:
            env = OpenFrontEnv(
                game_interface=game_interface,
                num_bots=num_bots,
                map_name=map_name
            )
        env = Monitor(env)
        return env
    return _init


def train(
    output_dir: Optional[str] = None,
    device: Optional[str] = None,
    n_envs: int = 16,
    continue_from: Optional[str] = None,
    map_name: str = 'plains',
    num_bots: int = 10,
    use_self_play: bool = False,
    total_timesteps: int = 1_000_000,
    learning_rate: Optional[float] = None,
    batch_size: Optional[int] = None,
    n_steps: Optional[int] = None,
):
    """
    Main training function for Phase 5.

    Args:
        output_dir: Output directory for logs and checkpoints
        device: Device to use (None for auto-detect)
        n_envs: Number of parallel environments
        continue_from: Path to model to continue training from
        map_name: Map to train on
        num_bots: Number of opponent bots
        use_self_play: Whether to use self-play
        total_timesteps: Total training timesteps
        learning_rate: Learning rate (auto if None)
        batch_size: Batch size (auto if None)
        n_steps: Rollout steps (auto if None)
    """
    # Detect device if not specified
    if device is None:
        device = detect_device()

    # Auto-configure batch size and n_steps based on device
    if batch_size is None:
        batch_size = 512 if device == 'cuda' else 256

    if n_steps is None:
        n_steps = 2048 if device == 'cuda' else 1024

    # Adjust n_envs for non-CUDA devices
    if device != 'cuda' and n_envs > 8:
        logger.info(f"Reducing n_envs from {n_envs} to 8 for {device}")
        n_envs = 8

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

    logger.info("=" * 70)
    logger.info("PHASE 5 TRAINING - CLEAN IMPLEMENTATION WITH GPU SUPPORT")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Parallel environments: {n_envs}")
    logger.info(f"Map: {map_name}")
    logger.info(f"Opponent bots: {num_bots}")
    logger.info(f"Self-Play: {use_self_play}")
    logger.info(f"Total timesteps: {total_timesteps:,}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Rollout steps: {n_steps}")

    # Load existing model if continuing
    model = None
    if continue_from:
        logger.info(f"\nLoading model from: {continue_from}")
        try:
            model = PPO.load(continue_from, device=device)
            logger.info("✓ Model loaded successfully")

            # Use lower learning rate for fine-tuning
            if learning_rate is None:
                learning_rate = 1e-4
                logger.info(f"  Using fine-tuning learning rate: {learning_rate}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.info("Starting from scratch instead")
            model = None

    # Default learning rate for new models
    if learning_rate is None:
        learning_rate = 1e-4  # Conservative default

    logger.info("=" * 70)

    # Create parallel environments
    logger.info(f"\nCreating {n_envs} parallel environments...")
    env = SubprocVecEnv([
        make_env(
            num_bots=num_bots,
            map_name=map_name,
            use_self_play=use_self_play
        ) for _ in range(n_envs)
    ])
    logger.info("✓ Environments created")

    # Create or update model
    if model is None:
        logger.info("\nCreating new PPO model with attention...")
        model = PPO(
            policy="MultiInputPolicy",
            env=env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=10,
            gamma=0.995,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.005,  # Low entropy for more deterministic policies
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs={
                'features_extractor_class': BattleRoyaleExtractorWithAttention,
                'features_extractor_kwargs': {'features_dim': 256}
            },
            verbose=1,
            device=device,
            tensorboard_log=os.path.join(output_dir, 'logs')
        )
        logger.info("✓ Model created")
        if device == 'cuda':
            logger.info(f"  GPU Memory: {get_gpu_memory_usage()}")
    else:
        logger.info("\nUpdating existing model...")
        model.set_env(env)
        # Move model to correct device
        if hasattr(model, 'policy'):
            model.policy = model.policy.to(device)
        logger.info(f"✓ Model updated and moved to {device}")

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000 // n_envs,
        save_path=os.path.join(output_dir, 'checkpoints'),
        name_prefix='phase5_model'
    )

    logging_callback = DetailedLoggingCallback(verbose=1)

    best_model_callback = SaveBestModelCallback(
        save_path=os.path.join(output_dir, 'checkpoints', 'best_model'),
        verbose=1
    )

    callbacks = CallbackList([checkpoint_callback, logging_callback, best_model_callback])

    # Train
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STARTING TRAINING")
    logger.info(f"{'=' * 70}\n")

    if device == 'cuda':
        logger.info(f"Initial GPU Memory: {get_gpu_memory_usage()}\n")

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
            tb_log_name='phase5_training'
        )
        logger.info(f"\n{'=' * 70}")
        logger.info("✓ TRAINING COMPLETE!")
        logger.info(f"{'=' * 70}")
    except KeyboardInterrupt:
        logger.warning(f"\n{'=' * 70}")
        logger.warning("⚠️  Training interrupted by user")
        logger.warning(f"{'=' * 70}")
    finally:
        if device == 'cuda':
            logger.info(f"\nFinal GPU Memory: {get_gpu_memory_usage()}")

    # Save final model
    final_path = os.path.join(output_dir, 'phase5_final')
    model.save(final_path)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✓ Model saved to: {final_path}")
    logger.info(f"{'=' * 70}")
    logger.info(f"\nCheckpoints: {os.path.join(output_dir, 'checkpoints')}")
    logger.info(f"Logs: {os.path.join(output_dir, 'logs')}")
    logger.info(f"\nTo view logs: tensorboard --logdir {os.path.join(output_dir, 'logs')}")

    # Clean up
    env.close()
    if device == 'cuda':
        torch.cuda.empty_cache()
        logger.info("\n✓ CUDA cache cleared")

    return model


def main():
    """Main entry point for Phase 5 training"""
    parser = argparse.ArgumentParser(
        description='Phase 5: Clean GPU Training with Configurable Options'
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
        default=None,
        choices=['cpu', 'cuda', 'mps'],
        help='Device to use (auto-detect if not specified)'
    )
    parser.add_argument(
        '--n-envs',
        type=int,
        default=16,
        help='Number of parallel environments (default: 16 for GPU, 8 for CPU)'
    )
    parser.add_argument(
        '--continue-from',
        type=str,
        default=None,
        help='Path to model to continue training from (Phase 3, 4, or 5)'
    )
    parser.add_argument(
        '--map',
        type=str,
        default='plains',
        help='Map to train on (e.g., plains, australia_500x500)'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=10,
        help='Number of opponent bots (1-50)'
    )
    parser.add_argument(
        '--self-play',
        action='store_true',
        help='Enable self-play training'
    )
    parser.add_argument(
        '--total-timesteps',
        type=int,
        default=1_000_000,
        help='Total training timesteps'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=None,
        help='Learning rate (auto: 1e-4)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Batch size (auto: 512 for CUDA, 256 otherwise)'
    )
    parser.add_argument(
        '--n-steps',
        type=int,
        default=None,
        help='Rollout steps (auto: 2048 for CUDA, 1024 otherwise)'
    )

    args = parser.parse_args()

    # Start training
    train(
        output_dir=args.output_dir,
        device=args.device,
        n_envs=args.n_envs,
        continue_from=args.continue_from,
        map_name=args.map,
        num_bots=args.num_bots,
        use_self_play=args.self_play,
        total_timesteps=args.total_timesteps,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        n_steps=args.n_steps,
    )


if __name__ == "__main__":
    main()
