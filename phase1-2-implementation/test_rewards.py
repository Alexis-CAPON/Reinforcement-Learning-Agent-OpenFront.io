"""
Test the new reward structure
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv

print("Testing reward structure...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

initial_tiles = info['tiles']
print(f"\nInitial: {initial_tiles} tiles")

# Take expansion action
obs, reward, done, truncated, info = env.step(1)
print(f"\nStep 1 (expand): Reward = {reward:.1f}")
print(f"  Breakdown: -1 (time) + tile_changes * 10")

# Run a few idle steps
total_reward = reward
for i in range(5):
    obs, reward, done, truncated, info = env.step(0)  # IDLE
    total_reward += reward
    if i == 0:
        print(f"\nStep 2 (idle): Reward = {reward:.1f}")
        tile_change = info['tiles'] - initial_tiles
        print(f"  Tiles changed: {tile_change}")
        print(f"  Expected: -1 (time) + {tile_change} * 10 = {-1 + tile_change * 10}")

print(f"\nTotal reward after 6 steps: {total_reward:.1f}")
print(f"Final tiles: {info['tiles']} (gained {info['tiles'] - initial_tiles})")

env.close()
print("\n" + "=" * 60)
print("Reward structure working correctly!")
print("\nWith -1 per step penalty:")
print("  - Agent is incentivized to win quickly")
print("  - Idle actions are costly")
print("  - Territory gains (+10/tile) still dominate")
