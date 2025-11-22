#!/usr/bin/env python3
"""
Test if MPS actually works with our MaskablePPO model
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import torch
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import DummyVecEnv
from environment_full_game import OpenFrontEnvFullGame

print("=" * 80)
print("MPS TRAINING TEST")
print("=" * 80)

# Check MPS
print(f"\nMPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

def mask_fn(env):
    """Wrapper function to get action masks from environment"""
    if hasattr(env, 'unwrapped'):
        return env.unwrapped.action_masks()
    return env.action_masks()

def make_env():
    """Create a single environment instance with action masking"""
    def _init():
        env = OpenFrontEnvFullGame(
            map_name='australia_256x256',
            num_bots=10,
            frame_stack=4
        )
        env = ActionMasker(env, mask_fn)
        return env
    return _init

# Create environment
print("\nCreating environment...")
env = DummyVecEnv([make_env()])

# Test MPS device
print("\nTesting MPS device...")
try:
    device = torch.device('mps')
    test_tensor = torch.randn(10, 10, device=device)
    result = torch.matmul(test_tensor, test_tensor)
    print(f"✓ MPS tensor operations work")
except Exception as e:
    print(f"✗ MPS tensor operations failed: {e}")
    sys.exit(1)

# Create model with MPS
print("\nCreating MaskablePPO model with MPS device...")
try:
    policy_kwargs = dict(
        net_arch=dict(
            pi=[256, 256],
            vf=[256, 256]
        ),
        activation_fn=torch.nn.ReLU,
        ortho_init=True
    )

    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=4,
        gamma=0.995,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.02,
        vf_coef=0.5,
        max_grad_norm=0.5,
        verbose=1,
        policy_kwargs=policy_kwargs,
        device='mps'
    )
    print(f"✓ Model created on device: {model.device}")
except Exception as e:
    print(f"✗ Model creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test training for a few steps
print("\nTesting training for 512 steps (2 iterations)...")
try:
    model.learn(total_timesteps=512, progress_bar=True)
    print("✓ Training completed successfully on MPS!")
except Exception as e:
    print(f"✗ Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

env.close()

print("\n" + "=" * 80)
print("✅ MPS TRAINING TEST PASSED - MPS works with our model!")
print("=" * 80)
