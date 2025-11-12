"""
Phase 5 Multi-Scale Training Script

For large maps (1024×1024+) where multi-scale observations are essential.
"""

import os
import sys
import argparse
from datetime import datetime
import logging
from typing import Optional
import torch

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from stable_baselines3.common.monitor import Monitor

from environment_multiscale import OpenFrontEnvMultiScale
from model_multiscale_attention import MultiScaleExtractorWithAttention
from training_callback import DetailedLoggingCallback
from best_model_callback import SaveBestModelCallback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_device() -> str:
    """Detect best available device."""
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
        logger.warning("⚠️  No GPU detected, using CPU")

    return device


def make_env(
    num_bots: int,
    map_name: str,
    local_view_size: int = 256
):
    """Create multi-scale environment factory."""
    def _init():
        env = OpenFrontEnvMultiScale(
            num_bots=num_bots,
            map_name=map_name,
            local_view_size=local_view_size
        )
        env = Monitor(env)
        return env
    return _init


def train(
    output_dir: Optional[str] = None,
    device: Optional[str] = None,
    n_envs: int = 8,  # Lower default for multi-scale (more memory)
    map_name: str = 'plains',
    num_bots: int = 10,
    local_view_size: int = 256,
    total_timesteps: int = 1_000_000,
    learning_rate: float = 1e-4,
    batch_size: Optional[int] = None,
    n_steps: Optional[int] = None,
):
    """
    Train with multi-scale observations.

    Args:
        output_dir: Output directory
        device: Device (None for auto-detect)
        n_envs: Parallel environments (lower for multi-scale)
        map_name: Map to train on
        num_bots: Number of bots
        local_view_size: Size of local view in tiles
        total_timesteps: Training steps
        learning_rate: Learning rate
        batch_size: Batch size (auto if None)
        n_steps: Rollout steps (auto if None)
    """
    # Detect device
    if device is None:
        device = detect_device()

    # Auto-configure based on device
    if batch_size is None:
        batch_size = 256 if device == 'cuda' else 128  # Smaller for multi-scale

    if n_steps is None:
        n_steps = 1024 if device == 'cuda' else 512   # Smaller for multi-scale

    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'runs',
            f'multiscale_run_{timestamp}'
        )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'checkpoints'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)

    logger.info("=" * 70)
    logger.info("PHASE 5 MULTI-SCALE TRAINING WITH ATTENTION - LARGE MAP SUPPORT")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Parallel environments: {n_envs}")
    logger.info(f"Map: {map_name}")
    logger.info(f"Opponent bots: {num_bots}")
    logger.info(f"Local view size: {local_view_size}×{local_view_size}")
    logger.info(f"Total timesteps: {total_timesteps:,}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Rollout steps: {n_steps}")
    logger.info(f"Learning rate: {learning_rate}")
    logger.info("=" * 70)

    # Create parallel environments
    logger.info(f"\nCreating {n_envs} multi-scale environments...")
    env = SubprocVecEnv([
        make_env(
            num_bots=num_bots,
            map_name=map_name,
            local_view_size=local_view_size
        ) for _ in range(n_envs)
    ])
    logger.info("✓ Environments created")

    # Create model
    logger.info("\nCreating PPO model with multi-scale attention architecture...")
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
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs={
            'features_extractor_class': MultiScaleExtractorWithAttention,
            'features_extractor_kwargs': {'features_dim': 512}
        },
        verbose=1,
        device=device,
        tensorboard_log=os.path.join(output_dir, 'logs')
    )
    logger.info("✓ Multi-scale attention model created")

    if device == 'cuda':
        allocated = torch.cuda.memory_allocated(0) / 1e9
        logger.info(f"  GPU Memory: {allocated:.2f} GB")

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000 // n_envs,
        save_path=os.path.join(output_dir, 'checkpoints'),
        name_prefix='multiscale_model'
    )

    logging_callback = DetailedLoggingCallback(verbose=1)

    best_model_callback = SaveBestModelCallback(
        save_path=os.path.join(output_dir, 'checkpoints', 'best_model'),
        verbose=1
    )

    callbacks = CallbackList([checkpoint_callback, logging_callback, best_model_callback])

    # Train
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STARTING MULTI-SCALE TRAINING")
    logger.info(f"{'=' * 70}\n")

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
            tb_log_name='multiscale_training'
        )
        logger.info(f"\n{'=' * 70}")
        logger.info("✓ TRAINING COMPLETE!")
        logger.info(f"{'=' * 70}")
    except KeyboardInterrupt:
        logger.warning(f"\n{'=' * 70}")
        logger.warning("⚠️  Training interrupted")
        logger.warning(f"{'=' * 70}")
    finally:
        if device == 'cuda':
            allocated = torch.cuda.memory_allocated(0) / 1e9
            logger.info(f"\nFinal GPU Memory: {allocated:.2f} GB")

    # Save final model
    final_path = os.path.join(output_dir, 'multiscale_final')
    model.save(final_path)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✓ Model saved to: {final_path}")
    logger.info(f"{'=' * 70}")

    # Clean up
    env.close()
    if device == 'cuda':
        torch.cuda.empty_cache()

    return model


def main():
    """Main entry point for multi-scale attention training"""
    parser = argparse.ArgumentParser(
        description='Phase 5: Multi-Scale Training with Attention for Large Maps (1024×1024+)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        choices=['cpu', 'cuda', 'mps'],
        help='Device (auto-detect if not specified)'
    )
    parser.add_argument(
        '--n-envs',
        type=int,
        default=8,
        help='Parallel environments (default: 8 for multi-scale)'
    )
    parser.add_argument(
        '--map',
        type=str,
        default='plains',
        help='Map to train on (recommend 1024×1024 or larger)'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=10,
        help='Number of opponent bots'
    )
    parser.add_argument(
        '--local-view-size',
        type=int,
        default=256,
        help='Size of local view in tiles (default: 256)'
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
        default=1e-4,
        help='Learning rate'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Batch size (auto: 256 for CUDA, 128 otherwise)'
    )
    parser.add_argument(
        '--n-steps',
        type=int,
        default=None,
        help='Rollout steps (auto: 1024 for CUDA, 512 otherwise)'
    )

    args = parser.parse_args()

    # Start training
    train(
        output_dir=args.output_dir,
        device=args.device,
        n_envs=args.n_envs,
        map_name=args.map,
        num_bots=args.num_bots,
        local_view_size=args.local_view_size,
        total_timesteps=args.total_timesteps,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        n_steps=args.n_steps,
    )


if __name__ == "__main__":
    main()
