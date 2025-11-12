"""
Debug script to see what state values are returned when agent loses
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Running episode until agent loses...")
print("=" * 70)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"Initial: tiles={info['tiles']}")

for step in range(10000):
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    action = np.random.choice(valid_actions)

    obs, reward, terminated, truncated, info = env.step(action)

    # Print when tiles get low
    if info['tiles'] <= 10:
        # Get raw state from game
        raw_state = env.game.get_state()
        print(f"\nStep {step+1}:")
        print(f"  tiles={info['tiles']}")
        print(f"  raw_state keys: {list(raw_state.keys())}")
        print(f"  raw has_lost: {raw_state.get('has_lost', 'MISSING')}")
        print(f"  raw game_over: {raw_state.get('game_over', 'MISSING')}")
        print(f"  raw has_won: {raw_state.get('has_won', 'MISSING')}")
        print(f"  terminated: {terminated}")
        print(f"  truncated: {truncated}")
        print(f"  reward: {reward:.1f}")

    if terminated or truncated:
        raw_state = env.game.get_state()
        print(f"\n{'='*70}")
        print(f"Episode ended at step {step+1}")
        print(f"  Final tiles: {info['tiles']}")
        print(f"  Terminated: {terminated}")
        print(f"  Truncated: {truncated}")
        print(f"  Raw state has_lost: {raw_state.get('has_lost', 'MISSING')}")
        print(f"  Raw state game_over: {raw_state.get('game_over', 'MISSING')}")
        print(f"  Raw state tiles_owned: {raw_state.get('tiles_owned', 'MISSING')}")
        print(f"{'='*70}")
        break

env.close()
