#!/usr/bin/env python3
"""
Benchmark CPU vs MPS training speed
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import torch
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import DummyVecEnv
from environment_full_game import OpenFrontEnvFullGame

def mask_fn(env):
    if hasattr(env, 'unwrapped'):
        return env.unwrapped.action_masks()
    return env.action_masks()

def make_env():
    def _init():
        env = OpenFrontEnvFullGame(
            map_name='australia_256x256',
            num_bots=10,
            frame_stack=4
        )
        env = ActionMasker(env, mask_fn)
        return env
    return _init

policy_kwargs = dict(
    net_arch=dict(pi=[256, 256], vf=[256, 256]),
    activation_fn=torch.nn.ReLU,
    ortho_init=True
)

print("=" * 80)
print("DEVICE BENCHMARK: CPU vs MPS")
print("=" * 80)

for device_name in ['cpu', 'mps']:
    print(f"\n{'=' * 80}")
    print(f"Testing device: {device_name.upper()}")
    print('=' * 80)

    # Create environment
    env = DummyVecEnv([make_env()])

    # Create model
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=4,
        verbose=0,
        policy_kwargs=policy_kwargs,
        device=device_name
    )

    print(f"Model device: {model.device}")
    print("Training for 512 steps...")

    start_time = time.time()
    model.learn(total_timesteps=512, progress_bar=False)
    elapsed = time.time() - start_time

    fps = 512 / elapsed
    print(f"✓ Training completed in {elapsed:.2f} seconds")
    print(f"✓ Speed: {fps:.1f} fps")

    env.close()

print("\n" + "=" * 80)
print("BENCHMARK COMPLETE")
print("=" * 80)
