"""
Phase 5 Training Script - GPU-Enabled with Self-Play

Features:
- GPU support with automatic device detection (CUDA/MPS/CPU)
- Self-play training against agent copies
- Larger map support (up to 500x500)
- Load and continue from Phase 3 models
- Optimized for JupyterHub environment
- Enhanced logging and checkpointing
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
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, CallbackList
from stable_baselines3.common.monitor import Monitor

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase3-implementation', 'src'))

from environment_large import OpenFrontEnvLarge
from self_play_env import SelfPlayEnv
from model import BattleRoyaleExtractor
from training_callback import DetailedLoggingCallback

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
    opponent_model_path: Optional[str] = None,
    game_interface=None
):
    """
    Create environment factory for vectorized environments.

    Args:
        num_bots: Number of bot opponents
        map_name: Name of the map to use
        use_self_play: Whether to use self-play
        opponent_model_path: Path to opponent model (for self-play)
        game_interface: Game interface/wrapper

    Returns:
        Environment factory function
    """
    def _init():
        if use_self_play:
            env = SelfPlayEnv(
                game_interface=game_interface,
                num_bots=num_bots,
                map_name=map_name,
                opponent_model_path=opponent_model_path
            )
        else:
            env = OpenFrontEnvLarge(
                game_interface=game_interface,
                num_bots=num_bots,
                map_name=map_name
            )
        env = Monitor(env)
        return env
    return _init


def train_phase(
    model: Optional[PPO],
    num_bots: int,
    total_timesteps: int,
    n_envs: int,
    output_dir: str,
    phase_name: str,
    device: str = 'cuda',
    map_name: str = 'plains',
    use_self_play: bool = False,
    learning_rate: float = 3e-4,
    batch_size: int = 256,  # Larger for GPU
    n_steps: int = 2048,    # Larger for GPU
) -> PPO:
    """
    Train one phase with GPU optimization.

    Args:
        model: Existing model to continue training (or None for new)
        num_bots: Number of bots for this phase
        total_timesteps: Training steps for this phase
        n_envs: Number of parallel environments
        output_dir: Output directory
        phase_name: Name of this phase (for logging)
        device: Device to use ('cuda', 'mps', or 'cpu')
        map_name: Map to train on
        use_self_play: Whether to use self-play
        learning_rate: Learning rate
        batch_size: Batch size (larger for GPU)
        n_steps: Steps per rollout (larger for GPU)

    Returns:
        Trained model
    """
    logger.info(f"=" * 70)
    logger.info(f"Starting {phase_name}")
    logger.info(f"  Bots: {num_bots}")
    logger.info(f"  Map: {map_name}")
    logger.info(f"  Timesteps: {total_timesteps:,}")
    logger.info(f"  Device: {device.upper()}")
    logger.info(f"  Self-Play: {use_self_play}")
    logger.info(f"  GPU Memory: {get_gpu_memory_usage()}")
    logger.info(f"=" * 70)

    # Create parallel environments
    logger.info(f"Creating {n_envs} parallel environments...")
    env = SubprocVecEnv([
        make_env(
            num_bots=num_bots,
            map_name=map_name,
            use_self_play=use_self_play,
            opponent_model_path=None  # Will be updated during training
        ) for _ in range(n_envs)
    ])

    # Create or update model
    if model is None:
        logger.info("Creating new PPO model with GPU optimization...")
        model = PPO(
            policy="MultiInputPolicy",
            env=env,
            learning_rate=learning_rate,
            n_steps=n_steps,           # Larger rollouts for GPU
            batch_size=batch_size,     # Larger batches for GPU
            n_epochs=10,
            gamma=0.995,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.03,  # Slightly reduced from phase 3
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs={
                'features_extractor_class': BattleRoyaleExtractor,
                'features_extractor_kwargs': {'features_dim': 256}
            },
            verbose=1,
            device=device,
            tensorboard_log=os.path.join(output_dir, 'logs')
        )
        logger.info(f"Model created on device: {device}")
        logger.info(f"GPU Memory after model creation: {get_gpu_memory_usage()}")
    else:
        logger.info("Continuing with existing model...")
        # Move model to correct device
        model.set_env(env)
        if hasattr(model, 'policy'):
            model.policy = model.policy.to(device)
        logger.info(f"Model moved to device: {device}")

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000 // n_envs,
        save_path=os.path.join(output_dir, 'checkpoints', phase_name),
        name_prefix=f'{phase_name}_model'
    )

    # Detailed logging callback
    logging_callback = DetailedLoggingCallback(verbose=1)

    callbacks = CallbackList([checkpoint_callback, logging_callback])

    # Train
    logger.info(f"Starting training for {total_timesteps:,} timesteps...")
    logger.info(f"Initial GPU Memory: {get_gpu_memory_usage()}")

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
            tb_log_name=phase_name
        )
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user!")
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise
    finally:
        logger.info(f"Final GPU Memory: {get_gpu_memory_usage()}")

    # Save phase checkpoint
    save_path = os.path.join(output_dir, 'checkpoints', f'{phase_name}_final')
    model.save(save_path)
    logger.info(f"Saved {phase_name} model to {save_path}")

    # Clean up
    env.close()

    # Clear GPU cache if using CUDA
    if device == 'cuda':
        torch.cuda.empty_cache()
        logger.info("Cleared CUDA cache")

    return model


def train(
    output_dir: Optional[str] = None,
    device: Optional[str] = None,
    n_envs: int = 16,  # More envs for GPU
    phase3_model_path: Optional[str] = None,
    map_name: str = 'australia_500x500',
    use_self_play: bool = True,
    total_timesteps: int = 1_000_000
):
    """
    Main training function for Phase 5.

    Args:
        output_dir: Output directory for logs and checkpoints
        device: Device to use (None for auto-detect)
        n_envs: Number of parallel environments
        phase3_model_path: Path to Phase 3 model to continue from
        map_name: Map to train on
        use_self_play: Whether to use self-play
        total_timesteps: Total training timesteps
    """
    # Detect device if not specified
    if device is None:
        device = detect_device()

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

    logger.info(f"=" * 70)
    logger.info(f"PHASE 5 TRAINING - GPU-ENABLED WITH SELF-PLAY")
    logger.info(f"=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Parallel environments: {n_envs}")
    logger.info(f"Map: {map_name}")
    logger.info(f"Self-Play: {use_self_play}")
    logger.info(f"Total timesteps: {total_timesteps:,}")

    # Load Phase 3 model if provided
    model = None
    if phase3_model_path:
        logger.info(f"Loading Phase 3 model from: {phase3_model_path}")
        try:
            model = PPO.load(phase3_model_path, device=device)
            logger.info("✓ Phase 3 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Phase 3 model: {e}")
            logger.info("Starting from scratch instead")
            model = None

    # Train Phase 5
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 5: LARGE MAP + SELF-PLAY TRAINING")
    logger.info("=" * 70)
    model = train_phase(
        model=model,
        num_bots=10,
        total_timesteps=total_timesteps,
        n_envs=n_envs,
        output_dir=output_dir,
        phase_name='phase5_selfplay',
        device=device,
        map_name=map_name,
        use_self_play=use_self_play,
        learning_rate=3e-4 if model is None else 1e-4,  # Lower LR if fine-tuning
        batch_size=512 if device == 'cuda' else 256,  # Larger batch for CUDA
        n_steps=2048 if device == 'cuda' else 1024,   # Larger rollout for CUDA
    )

    # Save final model
    final_path = os.path.join(output_dir, 'openfront_phase5_final')
    model.save(final_path)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✓ TRAINING COMPLETE!")
    logger.info(f"Final model saved to: {final_path}")
    logger.info(f"{'=' * 70}\n")

    return model


def main():
    """Main entry point for Phase 5 training"""
    parser = argparse.ArgumentParser(
        description='Phase 5: GPU-Enabled Training with Self-Play'
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
        help='Number of parallel environments (16 recommended for GPU)'
    )
    parser.add_argument(
        '--phase3-model',
        type=str,
        default=None,
        help='Path to Phase 3 model to continue training from'
    )
    parser.add_argument(
        '--map',
        type=str,
        default='australia_500x500',
        help='Map to train on (e.g., australia_500x500, plains)'
    )
    parser.add_argument(
        '--no-self-play',
        action='store_true',
        help='Disable self-play (use regular bots)'
    )
    parser.add_argument(
        '--total-timesteps',
        type=int,
        default=1_000_000,
        help='Total training timesteps'
    )

    args = parser.parse_args()

    # Start training
    train(
        output_dir=args.output_dir,
        device=args.device,
        n_envs=args.n_envs,
        phase3_model_path=args.phase3_model,
        map_name=args.map,
        use_self_play=not args.no_self_play,
        total_timesteps=args.total_timesteps
    )


if __name__ == "__main__":
    main()
