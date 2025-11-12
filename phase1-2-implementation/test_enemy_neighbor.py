"""
Test to find when agent encounters enemy neighbors
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))
from openfrontio_env import OpenFrontIOEnv
import numpy as np

env = OpenFrontIOEnv(config_path='configs/phase2_config.json')
obs, info = env.reset()

found_enemy = False
for i in range(500):
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    action_target = np.random.choice(valid_actions) if len(valid_actions) > 0 else 0

    action = {'attack_target': action_target, 'attack_percentage': np.array([0.8], dtype=np.float32)}
    obs, reward, terminated, truncated, info = env.step(action)

    # Check if any neighbor has troops
    if np.any(obs['neighbor_troops'] > 0) and not found_enemy:
        found_enemy = True
        num_neighbors = int(np.sum(obs['action_mask']) - 1)
        print(f'SUCCESS: Step {i}: Found enemy neighbors!')
        print(f'  Neighbor troops (normalized): {obs["neighbor_troops"][:num_neighbors]}')
        print(f'  Own troops: {info["troops"]:.0f}')
        print(f'  Tiles: {info["tiles"]}')
        print(f'  Action mask: {obs["action_mask"]}')
        print(f'  Global features: {obs["features"]}')
        break

    if terminated or truncated:
        print(f'Episode ended at step {i}')
        break

if not found_enemy:
    print('Did not encounter enemy neighbors in 500 steps')

env.close()
print('Test complete!')
