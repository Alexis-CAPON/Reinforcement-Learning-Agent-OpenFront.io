"""
Test what Monitor wrapper is actually doing to episode info
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper
from stable_baselines3.common.monitor import Monitor
import numpy as np

print("Creating environment WITH Monitor wrapper...")
env = OpenFrontIOEnv(config_path="configs/phase1_config.json")
env = FlattenActionWrapper(env)
env = Monitor(env)

print("\nResetting...")
obs = env.reset()

print("\nRunning 100 steps with IDLE to see what happens...")
total_reward_calculated = 0

for i in range(100):
    # IDLE action
    action = np.array([0.0, 0.0], dtype=np.float32)
    obs, reward, done, info = env.step(action)
    total_reward_calculated += reward

    if i == 99 or done:
        print(f"\nStep {i+1}:")
        print(f"  Reward this step: {reward}")
        print(f"  Total reward calculated: {total_reward_calculated:.1f}")
        print(f"  Info keys: {list(info.keys())}")

        if 'episode' in info:
            print(f"  Episode dict: {info['episode']}")
            print(f"  Tiles in info: {info.get('tiles', 'NOT FOUND')}")
            print(f"  Tiles in episode: {info['episode'].get('tiles_final', 'NOT FOUND')}")

        if done:
            break

env.close()
print("\nDone!")
