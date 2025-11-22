"""
Training script for Full Game with Buildings and Nukes

Features:
- Economic system: Cities, Ports, Factories
- Military system: Missile Silos, SAM Launchers, Defense Posts
- Nuclear weapons: Atom Bombs, Hydrogen Bombs
- 38,500 action space with heavy action masking
- Enhanced observation space with 32 global features
- Reward shaping for economic/military objectives

Expected training time: 30-50 hours on GPU
"""

import os
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecMonitor
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

from environment_full_game import OpenFrontEnvFullGame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def mask_fn(env):
    """Wrapper function to get action masks from environment"""
    # Use unwrapped to get the base environment
    if hasattr(env, 'unwrapped'):
        return env.unwrapped.action_masks()
    return env.action_masks()


def make_env(map_name='australia_256x256', num_bots=10):
    """
    Create a single environment instance with action masking.

    Args:
        map_name: Map to use for training
        num_bots: Number of bot opponents

    Returns:
        Wrapped environment
    """
    def _init():
        env = OpenFrontEnvFullGame(
            map_name=map_name,
            num_bots=num_bots,
            frame_stack=4
        )
        # Wrap with action masker
        env = ActionMasker(env, mask_fn)
        return env
    return _init


def train_full_game(
    map_name: str = 'australia_256x256',
    num_bots: int = 10,
    total_timesteps: int = 20_000_000,
    device: str = 'auto',
    n_envs: int = 8,
    save_freq: int = 100_000,
    eval_freq: int = 50_000,
    n_eval_episodes: int = 5,
    learning_rate: float = 3e-4,
    batch_size: int = 128,
    n_steps: int = 2048,
    n_epochs: int = 10,
    gamma: float = 0.995,
    gae_lambda: float = 0.95,
    clip_range: float = 0.2,
    ent_coef: float = 0.02,
    vf_coef: float = 0.5,
    max_grad_norm: float = 0.5
):
    """
    Train agent with full game features.

    Args:
        map_name: Map to use (australia_256x256 recommended)
        num_bots: Number of opponents (10 recommended)
        total_timesteps: Total training steps (20M recommended)
        save_freq: Model checkpoint frequency
        eval_freq: Evaluation frequency
        n_eval_episodes: Episodes per evaluation
        learning_rate: PPO learning rate
        batch_size: Mini-batch size
        n_steps: Steps per rollout
        n_epochs: Optimization epochs per rollout
        gamma: Discount factor
        gae_lambda: GAE lambda
        clip_range: PPO clipping range
        ent_coef: Entropy coefficient (higher = more exploration)
        vf_coef: Value function coefficient
        max_grad_norm: Gradient clipping
    """

    logger.info("=" * 80)
    logger.info("FULL GAME TRAINING - Buildings + Nukes + Economy + Military")
    logger.info("=" * 80)
    logger.info(f"Map: {map_name}")
    logger.info(f"Opponents: {num_bots} bots")
    logger.info(f"Parallel envs: {n_envs}")
    logger.info(f"Total timesteps: {total_timesteps:,}")
    logger.info(f"Action space: 5 × 11 × 5 × 7 × 2 × 10 × 10 = 38,500 actions")
    logger.info(f"Observation space: 128×128×16 channels + 32 global features")
    logger.info(f"Features: Buildings (6 types), Nukes (2 types), Action masking")
    logger.info("=" * 80)

    # Create directories
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = f'models/ppo_full_game_{timestamp}'
    log_dir = f'logs/ppo_full_game_{timestamp}'
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    logger.info(f"Model directory: {model_dir}")
    logger.info(f"Log directory: {log_dir}")

    # Create training environment
    logger.info(f"Creating {n_envs} parallel training environment(s)...")
    if n_envs == 1:
        env = DummyVecEnv([make_env(map_name, num_bots)])
    else:
        # Use SubprocVecEnv for true parallelism (each env in separate process)
        env = SubprocVecEnv([make_env(map_name, num_bots) for _ in range(n_envs)])
    env = VecMonitor(env, log_dir)

    # Create evaluation environment (always single env)
    logger.info("Creating evaluation environment...")
    eval_env = DummyVecEnv([make_env(map_name, num_bots)])
    eval_env = VecMonitor(eval_env, f"{log_dir}/eval")

    # Create callbacks
    # Note: save_freq is per environment, so with n_envs=12, it saves 12x more frequently
    # Adjust if needed: save_freq_adjusted = save_freq * n_envs
    checkpoint_callback = CheckpointCallback(
        save_freq=max(save_freq // n_envs, 1),  # Adjust for parallel envs
        save_path=model_dir,
        name_prefix='checkpoint',
        save_replay_buffer=False,
        save_vecnormalize=True
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=f"{log_dir}/eval",
        eval_freq=max(eval_freq // n_envs, 1),  # Adjust for parallel envs
        n_eval_episodes=n_eval_episodes,
        deterministic=False,  # Use stochastic policy for evaluation
        render=False
    )

    # Create MaskablePPO model with policy kwargs for complex action space
    logger.info("Creating MaskablePPO model...")
    logger.info(f"Hyperparameters:")
    logger.info(f"  Learning rate: {learning_rate}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  N steps: {n_steps}")
    logger.info(f"  N epochs: {n_epochs}")
    logger.info(f"  Gamma: {gamma}")
    logger.info(f"  GAE lambda: {gae_lambda}")
    logger.info(f"  Clip range: {clip_range}")
    logger.info(f"  Entropy coef: {ent_coef}")
    logger.info(f"  VF coef: {vf_coef}")
    logger.info(f"  Max grad norm: {max_grad_norm}")

    policy_kwargs = dict(
        net_arch=dict(
            pi=[512, 512, 256],  # Actor network
            vf=[512, 512, 256]   # Critic network
        ),
        activation_fn=torch.nn.ReLU,
        ortho_init=True
    )

    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        verbose=1,
        tensorboard_log=log_dir,
        policy_kwargs=policy_kwargs,
        device=device
    )

    logger.info(f"Model device: {model.device}")
    logger.info("=" * 80)

    # Train the model
    logger.info("Starting training...")
    logger.info(f"Estimated time: 30-50 hours on GPU, 100-150 hours on CPU")
    logger.info(f"Monitor with: tensorboard --logdir {log_dir}")
    logger.info("=" * 80)

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True
        )
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")

    # Save final model
    final_model_path = os.path.join(model_dir, 'final_model.zip')
    model.save(final_model_path)
    logger.info(f"Final model saved to: {final_model_path}")

    # Cleanup
    env.close()
    eval_env.close()

    logger.info("=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info(f"Model directory: {model_dir}")
    logger.info(f"Best model: {os.path.join(model_dir, 'best_model.zip')}")
    logger.info(f"Final model: {final_model_path}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"1. View training curves: tensorboard --logdir {log_dir}")
    logger.info(f"2. Test model: python test_full_game.py --model {final_model_path}")
    logger.info(f"3. Visual test: python visual_test_full_game.py --model {final_model_path}")
    logger.info("=" * 80)


if __name__ == '__main__':
    import argparse
    import torch

    parser = argparse.ArgumentParser(description='Train full-game agent with buildings and nukes')

    # Environment args
    parser.add_argument('--map', type=str, default='australia_256x256',
                       help='Map name (default: australia_256x256)')
    parser.add_argument('--bots', type=int, default=10,
                       help='Number of bot opponents (default: 10)')

    # Training args
    parser.add_argument('--timesteps', type=int, default=20_000_000,
                       help='Total training timesteps (default: 20M)')
    parser.add_argument('--device', type=str, default='auto',
                       help='Device to use: auto, cpu, cuda, or mps (default: auto)')
    parser.add_argument('--n-envs', type=int, default=8,
                       help='Number of parallel environments (default: 8, recommended: 4-16 for GPU)')
    parser.add_argument('--save-freq', type=int, default=100_000,
                       help='Checkpoint save frequency (default: 100K)')
    parser.add_argument('--eval-freq', type=int, default=50_000,
                       help='Evaluation frequency (default: 50K)')
    parser.add_argument('--eval-episodes', type=int, default=5,
                       help='Episodes per evaluation (default: 5)')

    # PPO hyperparameters
    parser.add_argument('--lr', type=float, default=3e-4,
                       help='Learning rate (default: 3e-4)')
    parser.add_argument('--batch-size', type=int, default=128,
                       help='Batch size (default: 128)')
    parser.add_argument('--n-steps', type=int, default=2048,
                       help='Steps per rollout (default: 2048)')
    parser.add_argument('--n-epochs', type=int, default=10,
                       help='Optimization epochs (default: 10)')
    parser.add_argument('--gamma', type=float, default=0.995,
                       help='Discount factor (default: 0.995)')
    parser.add_argument('--gae-lambda', type=float, default=0.95,
                       help='GAE lambda (default: 0.95)')
    parser.add_argument('--clip-range', type=float, default=0.2,
                       help='PPO clip range (default: 0.2)')
    parser.add_argument('--ent-coef', type=float, default=0.02,
                       help='Entropy coefficient (default: 0.02, higher = more exploration)')
    parser.add_argument('--vf-coef', type=float, default=0.5,
                       help='Value function coefficient (default: 0.5)')
    parser.add_argument('--max-grad-norm', type=float, default=0.5,
                       help='Max gradient norm (default: 0.5)')

    args = parser.parse_args()

    # Check GPU availability
    if torch.cuda.is_available():
        logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        logger.warning("No GPU available - training will be slow!")
        logger.warning("Consider using a GPU for training (30-50 hours vs 100-150 hours)")

    # Run training
    train_full_game(
        map_name=args.map,
        num_bots=args.bots,
        total_timesteps=args.timesteps,
        device=args.device,
        n_envs=args.n_envs,
        save_freq=args.save_freq,
        eval_freq=args.eval_freq,
        n_eval_episodes=args.eval_episodes,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        n_steps=args.n_steps,
        n_epochs=args.n_epochs,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_range=args.clip_range,
        ent_coef=args.ent_coef,
        vf_coef=args.vf_coef,
        max_grad_norm=args.max_grad_norm
    )
