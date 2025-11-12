"""
Quick test to verify the agent can expand into neutral territory
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing expansion into neutral territory...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"\nInitial state:")
print(f"  Tiles: {info['tiles']}")
print(f"  Troops: {info['troops']}")
print(f"  Neighbors: {info['num_neighbors']}")
print(f"  Action mask: {obs['action_mask']}")
print(f"  Valid actions: {np.where(obs['action_mask'] == 1)[0]}")

# Try to take an expansion action
valid_actions = np.where(obs['action_mask'] == 1)[0]
if len(valid_actions) > 1:
    # Take first non-IDLE action
    action = valid_actions[1]
    print(f"\nTaking action {action} (should expand)...")

    obs, reward, done, truncated, info = env.step(action)

    print(f"\nAfter action (immediate):")
    print(f"  Tiles: {info['tiles']} (change: {info['tiles'] - 52})")
    print(f"  Troops: {info['troops']}")
    print(f"  Reward: {reward}")
    print(f"  Neighbors: {info['num_neighbors']}")

    # Attacks take time - run more steps to see territory change
    print(f"\nRunning 10 more IDLE steps to let attack complete...")
    for i in range(10):
        obs, reward, done, truncated, info = env.step(0)  # IDLE
        if i % 3 == 0:
            print(f"  Step {i+1}: Tiles={info['tiles']}, Troops={info['troops']}, Reward={reward:.1f}")

    print(f"\nFinal state:")
    print(f"  Tiles: {info['tiles']} (change: {info['tiles'] - 52})")
    print(f"  Troops: {info['troops']}")

    if info['tiles'] > 52:
        print(f"\n✅ SUCCESS! Agent expanded from 52 to {info['tiles']} tiles!")
    else:
        print(f"\n❌ PROBLEM: Agent still has 52 tiles after 10 ticks")
else:
    print("\n❌ No valid expansion actions available!")

env.close()
print("\n" + "=" * 60)
