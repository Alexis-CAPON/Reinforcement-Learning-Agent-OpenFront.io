"""
Test to verify the AI bot is actually playing and expanding
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import time

print("Testing AI bot behavior...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"\nInitial state:")
print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
print(f"  AI Bot   - Tiles: {info['enemy_tiles']}")

# Run 100 IDLE steps to let the AI play
print(f"\nRunning 100 IDLE steps (only AI should be acting)...")
ai_tiles_history = [info['enemy_tiles']]
rl_tiles_history = [info['tiles']]

for i in range(100):
    obs, reward, done, truncated, info = env.step(0)  # IDLE - only AI acts

    if i % 20 == 19:
        print(f"  Step {i+1}:")
        print(f"    RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
        print(f"    AI Bot   - Tiles: {info['enemy_tiles']}")

    ai_tiles_history.append(info['enemy_tiles'])
    rl_tiles_history.append(info['tiles'])

    if done or truncated:
        print(f"\n  Game ended at step {i+1}!")
        break

print(f"\n" + "=" * 60)
print(f"Results:")
print(f"  RL Agent tiles: {rl_tiles_history[0]} → {rl_tiles_history[-1]} (change: {rl_tiles_history[-1] - rl_tiles_history[0]})")
print(f"  AI Bot tiles:   {ai_tiles_history[0]} → {ai_tiles_history[-1]} (change: {ai_tiles_history[-1] - ai_tiles_history[0]})")

ai_tile_changes = [ai_tiles_history[i] != ai_tiles_history[i-1] for i in range(1, len(ai_tiles_history))]
num_ai_changes = sum(ai_tile_changes)

print(f"\n  AI territory changed {num_ai_changes} times out of {len(ai_tile_changes)} steps")

if num_ai_changes > 0:
    print(f"\n✅ SUCCESS! AI bot is actively playing and expanding!")
else:
    print(f"\n❌ PROBLEM! AI bot is NOT playing - territory never changed!")

env.close()
print("=" * 60)
