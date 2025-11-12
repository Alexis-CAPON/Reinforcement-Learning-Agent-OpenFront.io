"""
Test what actions a checkpoint is outputting
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

import numpy as np
from stable_baselines3 import PPO
from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper

model_path = "runs/run_20251031_042107/checkpoints/ppo_openfrontio_10000_steps.zip"

print(f"Loading checkpoint: {model_path}")
model = PPO.load(model_path)

print("Creating environment...")
env = OpenFrontIOEnv(config_path="configs/phase1_config.json")
env = FlattenActionWrapper(env)

print("\nResetting environment...")
obs, info = env.reset()

print(f"Initial state: tiles={info['tiles']}, enemy_tiles={info['enemy_tiles']}")

print("\nTesting 50 steps:")
action_counts = {i: 0 for i in range(9)}
percentage_sum = 0

for i in range(50):
    action, _ = model.predict(obs, deterministic=False)  # Use stochastic

    # Parse action
    attack_target = int(np.clip(np.round(action[0]), 0, 8))
    attack_percentage = float(action[1])

    action_counts[attack_target] += 1
    percentage_sum += attack_percentage

    if i < 10 or i % 10 == 0:
        print(f"Step {i+1}: target={attack_target}, pct={attack_percentage:.3f}, tiles={info['tiles']}")

    obs, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        print(f"Episode ended at step {i+1}, tiles={info['tiles']}")
        break

print(f"\nFinal state: tiles={info['tiles']}, enemy_tiles={info['enemy_tiles']}")
print(f"\nAction distribution:")
for target, count in sorted(action_counts.items()):
    pct = (count / 50) * 100
    print(f"  Target {target}: {count:2d} times ({pct:5.1f}%)")

print(f"\nAverage attack percentage: {percentage_sum/50:.3f}")

env.close()
print("\nDone!")
