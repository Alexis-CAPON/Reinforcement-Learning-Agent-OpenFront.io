"""
Debug what gets stored in episode info
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper
from stable_baselines3.common.monitor import Monitor
import numpy as np

print("Creating environment with Monitor wrapper (like training)...")
env = OpenFrontIOEnv(config_path="configs/phase1_config.json")
env = FlattenActionWrapper(env)
env = Monitor(env)  # This is what adds episode info

print("\nResetting environment...")
obs, info = env.reset()

print(f"Initial observation features: {obs['features']}")
print(f"Initial info keys: {list(info.keys())}")

print("\nRunning until episode ends with IDLE actions...")
step = 0
while True:
    # IDLE action (flattened: [0.0, 0.0])
    action = np.array([0.0, 0.0], dtype=np.float32)

    obs, reward, terminated, truncated, info = env.step(action)
    step += 1

    if step % 500 == 0:
        print(f"Step {step}: tiles={info.get('tiles', '?')}, reward={reward:.1f}")

    if terminated or truncated:
        print(f"\n{'='*60}")
        print(f"EPISODE ENDED at step {step}")
        print(f"{'='*60}")
        print(f"Info dict keys: {list(info.keys())}")
        print(f"Info dict contents:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        if 'episode' in info:
            print(f"\nEpisode dict contents:")
            for key, value in info['episode'].items():
                print(f"  {key}: {value}")
        break

env.close()
print("\nDone!")
