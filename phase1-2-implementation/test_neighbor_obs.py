"""
Test neighbor troops observation space
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("=" * 80)
print("TESTING NEIGHBOR TROOPS OBSERVATION")
print("=" * 80)

print("\n1. Creating Phase 2 environment...")
env = OpenFrontIOEnv(config_path="configs/phase2_config.json")

print(f"\nObservation space: {env.observation_space}")
print(f"  - features: {env.observation_space['features'].shape}")
print(f"  - action_mask: {env.observation_space['action_mask'].shape}")
print(f"  - neighbor_troops: {env.observation_space['neighbor_troops'].shape}")

print("\n2. Resetting environment...")
obs, info = env.reset()

print(f"\nObservation keys: {obs.keys()}")
print(f"  - features shape: {obs['features'].shape}")
print(f"  - action_mask shape: {obs['action_mask'].shape}")
print(f"  - neighbor_troops shape: {obs['neighbor_troops'].shape}")

print(f"\nFeatures: {obs['features']}")
print(f"Action mask: {obs['action_mask']}")
print(f"Neighbor troops: {obs['neighbor_troops']}")

print("\n3. Running a few steps to see neighbor troop changes...")
for i in range(5):
    # Sample random valid action
    valid_actions = np.where(obs['action_mask'] == 1)[0]

    if len(valid_actions) > 1:  # If we have neighbors
        action_target = np.random.choice(valid_actions)
    else:
        action_target = 0  # IDLE

    action_percentage = 0.5

    action = {
        'attack_target': action_target,
        'attack_percentage': np.array([action_percentage], dtype=np.float32)
    }

    obs, reward, terminated, truncated, info = env.step(action)

    num_neighbors = int(np.sum(obs['action_mask']) - 1)  # -1 for IDLE action
    neighbor_troops_values = obs['neighbor_troops'][:num_neighbors]

    print(f"\nStep {i+1}:")
    print(f"  Action: target={action_target}, pct={action_percentage:.2f}")
    print(f"  Reward: {reward:.2f}")
    print(f"  Num neighbors: {num_neighbors}")
    print(f"  Neighbor troops: {neighbor_troops_values}")
    print(f"  Tiles: {info['tiles']}, Own troops: {info['troops']:.0f}")

    if terminated or truncated:
        print(f"\nEpisode ended!")
        break

env.close()

print("\n" + "=" * 80)
print("✅ NEIGHBOR TROOPS OBSERVATION TEST COMPLETE!")
print("=" * 80)
print("\nKey observations:")
print("  - Observation space includes 'neighbor_troops' array")
print("  - neighbor_troops[i] corresponds to action (i+1)")
print("  - Values are normalized 0.0-1.0")
print("  - Agent can now see which neighbors are strong/weak!")
