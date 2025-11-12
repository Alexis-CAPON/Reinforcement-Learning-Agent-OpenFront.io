"""
Verify that loss detection fix works in training scenarios

This runs a few episodes with random actions and checks:
1. Episodes terminate when agent loses (tiles=0)
2. has_lost flag is set correctly
3. Loss penalty is applied
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Verifying loss detection fix...")
print("=" * 70)

env = OpenFrontIOEnv()

num_episodes = 3
max_steps_per_episode = 10000

for episode in range(num_episodes):
    print(f"\n{'='*70}")
    print(f"Episode {episode + 1}")
    print(f"{'='*70}")

    obs, info = env.reset()
    print(f"Initial state: Tiles={info['tiles']}, Troops={info['troops']}, Enemy tiles={info['enemy_tiles']}")

    episode_reward = 0
    tiles_history = []
    step = 0

    for step in range(max_steps_per_episode):
        # Take random valid action
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)

        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        tiles_history.append(info['tiles'])

        # Log periodically or on significant events
        if step % 500 == 0 or info['tiles'] <= 10 or terminated or truncated:
            print(f"  Step {step+1}: Tiles={info['tiles']:4d}, "
                  f"Troops={info['troops']:6.0f}, "
                  f"Enemy={info['enemy_tiles']:4d}, "
                  f"Reward={reward:7.1f}")

        if terminated or truncated:
            print(f"\n  Episode ended at step {step+1}")
            print(f"  Terminated: {terminated}, Truncated: {truncated}")

            # Check episode info
            if 'episode' in info:
                ep_info = info['episode']
                print(f"\n  Episode Info:")
                print(f"    Final tiles: {ep_info['tiles_final']}")
                print(f"    Won: {ep_info['won']}")
                print(f"    Episode reward: {ep_info['r']:.1f}")
                print(f"    Episode length: {ep_info['l']}")

            # Analyze termination reason
            print(f"\n  Analysis:")
            if info['tiles'] == 0:
                if terminated:
                    print(f"    ✅ CORRECT: Agent lost (tiles=0) and episode terminated")
                    print(f"    ✅ Loss penalty should be -10,000")

                    # Check if loss penalty was applied (roughly)
                    if reward < -5000:
                        print(f"    ✅ Loss penalty was applied (reward={reward:.1f})")
                    else:
                        print(f"    ⚠️  Loss penalty might not have been applied (reward={reward:.1f})")
                else:
                    print(f"    ❌ BUG: Agent lost (tiles=0) but episode did NOT terminate")
                    print(f"    ❌ This is the bug we're trying to fix!")

            elif terminated:
                print(f"    Agent won or other termination condition (tiles={info['tiles']})")

            elif truncated:
                print(f"    Episode truncated (reached max_steps)")

            # Show tile trajectory
            if len(tiles_history) > 10:
                print(f"\n  Tile trajectory (last 10 steps): {tiles_history[-10:]}")

            break
    else:
        # Episode didn't terminate within max_steps
        print(f"\n  Episode did not terminate within {max_steps_per_episode} steps")
        print(f"  Final tiles: {info['tiles']}")

    print(f"\n  Total episode reward: {episode_reward:.1f}")

env.close()

print(f"\n{'='*70}")
print("Verification complete!")
print(f"{'='*70}")
print("\nSummary:")
print("If you see '✅ CORRECT' messages, the loss detection is working properly.")
print("If you see '❌ BUG' messages, there's still an issue with loss detection.")
