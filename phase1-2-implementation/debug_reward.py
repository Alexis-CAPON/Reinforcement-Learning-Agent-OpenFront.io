"""
Debug reward calculation - see exactly what's happening
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv

print("Creating environment...")
env = OpenFrontIOEnv(config_path="configs/phase1_config.json")

print("\nResetting environment...")
obs, info = env.reset()

print(f"Initial state:")
print(f"  Agent tiles: {info['tiles']}")
print(f"  Enemy tiles: {info['enemy_tiles']}")
print(f"  Total tiles on map: {info['tiles'] + info['enemy_tiles']}")

print("\nRunning 100 IDLE steps and tracking rewards:")
total_reward = 0
for i in range(100):
    # IDLE action
    action = {'attack_target': 0, 'attack_percentage': [0.0]}

    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward

    if i % 10 == 0:
        print(f"Step {i:3d}: agent_tiles={info['tiles']:4d}, enemy_tiles={info['enemy_tiles']:5d}, "
              f"reward={reward:8.1f}, total_reward={total_reward:10.1f}")

    if terminated or truncated:
        print(f"\nEpisode ended at step {i}")
        print(f"  Final agent tiles: {info['tiles']}")
        print(f"  Final enemy tiles: {info['enemy_tiles']}")
        print(f"  Total reward: {total_reward:.1f}")
        break

env.close()
print("\nDone!")
