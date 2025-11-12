"""
Quick test to see what actions the model is actually choosing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

import numpy as np
from stable_baselines3 import PPO
from openfrontio_env import OpenFrontIOEnv
from flatten_action_wrapper import FlattenActionWrapper

print("Loading model...")
model = PPO.load("runs/run_20251031_034919/final_model.zip")

print("Creating environment...")
env = OpenFrontIOEnv(config_path="configs/phase1_config.json")
env = FlattenActionWrapper(env)

print("\nResetting environment...")
obs, info = env.reset()

print(f"Initial observation:")
print(f"  Features: {obs['features']}")
print(f"  Action mask: {obs['action_mask']}")

print("\nTesting 20 steps:")
for i in range(20):
    action, _ = model.predict(obs, deterministic=True)

    # Parse action
    attack_target = int(np.clip(np.round(action[0]), 0, 8))
    attack_percentage = float(action[1])

    print(f"Step {i+1}: target={attack_target}, pct={attack_percentage:.3f}, tiles={info['tiles']}")

    obs, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        print(f"Episode ended! tiles={info['tiles']}")
        break

env.close()
print("\nDone!")
