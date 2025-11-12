"""
Debug what happens with DummyVecEnv (like training uses)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
import numpy as np

def make_env():
    def _init():
        env = OpenFrontIOEnv(config_path="configs/phase1_config.json")
        env = FlattenActionWrapper(env)
        env = Monitor(env)
        return env
    return _init

print("Creating vectorized environment (like training)...")
env = DummyVecEnv([make_env()])

print("\nResetting environment...")
obs = env.reset()

print(f"Initial observation shape: {obs.shape}")

print("\nRunning until episode ends with IDLE actions...")
step = 0
while True:
    # IDLE action (flattened: [0.0, 0.0])
    actions = np.array([[0.0, 0.0]], dtype=np.float32)

    obs, rewards, dones, infos = env.step(actions)
    step += 1

    if step % 500 == 0:
        info = infos[0]
        tiles = info.get('tiles', '?')
        print(f"Step {step}: tiles={tiles}, reward={rewards[0]:.1f}")

    if dones[0]:
        info = infos[0]
        print(f"\n{'='*60}")
        print(f"EPISODE ENDED at step {step}")
        print(f"{'='*60}")
        print(f"Info dict keys: {list(info.keys())}")
        print(f"\nInfo dict contents:")
        for key, value in info.items():
            if key != 'terminal_observation':  # Skip large arrays
                print(f"  {key}: {value}")

        if 'episode' in info:
            print(f"\nEpisode dict contents:")
            for key, value in info['episode'].items():
                print(f"  {key}: {value}")

        break

env.close()
print("\nDone!")
