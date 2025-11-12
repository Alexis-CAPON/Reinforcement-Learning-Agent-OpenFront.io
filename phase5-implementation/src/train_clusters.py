"""
Phase 5 Training Script - Cluster-Aware Actions

Train agent with cluster awareness and action masking.
Requires: sb3-contrib for MaskablePPO
"""

import os
import sys
import argparse
from datetime import datetime
import logging
from typing import Optional
import torch

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from stable_baselines3.common.monitor import Monitor

from environment_clusters import OpenFrontEnvClusters
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


def mask_fn(env):
    """Action masking function for invalid actions."""
    return env.action_masks()


def make_env(num_bots: int, map_name: str):
    """Create cluster-aware environment factory with action masking."""
    def _init():
        env = OpenFrontEnvClusters(
            num_bots=num_bots,
            map_name=map_name
        )
        env = Monitor(env)
        # Wrap with action masker
        env = ActionMasker(env, mask_fn)
        return env
    return _init


def train(
    output_dir: Optional[str] = None,
    device: Optional[str] = None,
    n_envs: int = 8,
    map_name: str = 'plains',
    num_bots: int = 10,
    total_timesteps: int = 1_000_000,
    learning_rate: float = 1e-4,
    batch_size: Optional[int] = None,
    n_steps: Optional[int] = None,
):
    """
    Train with cluster-aware actions and masking.

    Args:
        output_dir: Output directory
        device: Device (None for auto-detect)
        n_envs: Parallel environments
        map_name: Map to train on
        num_bots: Number of bots
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
        batch_size = 256 if device == 'cuda' else 128

    if n_steps is None:
        n_steps = 1024 if device == 'cuda' else 512

    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'runs',
            f'cluster_run_{timestamp}'
        )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'checkpoints'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)

    logger.info("=" * 70)
    logger.info("PHASE 5 CLUSTER-AWARE TRAINING WITH ACTION MASKING")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Parallel environments: {n_envs}")
    logger.info(f"Map: {map_name}")
    logger.info(f"Opponent bots: {num_bots}")
    logger.info(f"Total timesteps: {total_timesteps:,}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Rollout steps: {n_steps}")
    logger.info(f"Learning rate: {learning_rate}")
    logger.info("=" * 70)

    # Create parallel environments
    logger.info(f"\nCreating {n_envs} cluster-aware environments with action masking...")
    env = SubprocVecEnv([
        make_env(num_bots=num_bots, map_name=map_name)
        for _ in range(n_envs)
    ])
    logger.info("✓ Environments created")

    # Create model with MaskablePPO
    logger.info("\nCreating MaskablePPO model with cluster-aware policy...")
    model = MaskablePPO(
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
        verbose=1,
        device=device,
        tensorboard_log=os.path.join(output_dir, 'logs')
    )
    logger.info("✓ MaskablePPO model created with action masking")

    if device == 'cuda':
        allocated = torch.cuda.memory_allocated(0) / 1e9
        logger.info(f"  GPU Memory: {allocated:.2f} GB")

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000 // n_envs,
        save_path=os.path.join(output_dir, 'checkpoints'),
        name_prefix='cluster_model'
    )

    logging_callback = DetailedLoggingCallback(verbose=1)

    best_model_callback = SaveBestModelCallback(
        save_path=os.path.join(output_dir, 'checkpoints', 'best_model'),
        verbose=1
    )

    callbacks = CallbackList([checkpoint_callback, logging_callback, best_model_callback])

    # Train
    logger.info(f"\n{'=' * 70}")
    logger.info(f"STARTING CLUSTER-AWARE TRAINING")
    logger.info(f"{'=' * 70}\n")

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
            tb_log_name='cluster_training'
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
    final_path = os.path.join(output_dir, 'cluster_final')
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
    """Main entry point for cluster-aware training"""
    parser = argparse.ArgumentParser(
        description='Phase 5: Cluster-Aware Training with Action Masking'
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
        help='Parallel environments (default: 8)'
    )
    parser.add_argument(
        '--map',
        type=str,
        default='plains',
        help='Map to train on'
    )
    parser.add_argument(
        '--num-bots',
        type=int,
        default=10,
        help='Number of opponent bots'
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
        total_timesteps=args.total_timesteps,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        n_steps=args.n_steps,
    )


if __name__ == "__main__":
    main()
