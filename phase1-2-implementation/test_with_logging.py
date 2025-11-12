"""
Test to see the stderr output from game bridge to check if loss detection is working
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing with stderr logging visible...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"\nInitial state:")
print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")

# Run random actions until we lose
print(f"\nRunning random actions until agent loses...")

for i in range(5000):
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    action = np.random.choice(valid_actions)

    obs, reward, terminated, truncated, info = env.step(action)

    # Print every 100 steps or when tiles get low
    if i % 100 == 0 or info['tiles'] <= 20:
        print(f"Step {i+1}: Tiles={info['tiles']}, Reward={reward:.1f}, Terminated={terminated}")

    if terminated or truncated:
        print(f"\n{'='*60}")
        print(f"Episode ended at step {i+1}")
        print(f"  Final tiles: {info['tiles']}")
        print(f"  Terminated: {terminated}")
        print(f"  Truncated: {truncated}")
        print(f"  Final reward: {reward:.1f}")

        if info['tiles'] == 0 and terminated:
            print(f"\n✅ Loss detected properly!")
        elif info['tiles'] == 0 and not terminated:
            print(f"\n❌ Loss NOT detected - this is the bug!")

        break

env.close()
print("\nDone!")
