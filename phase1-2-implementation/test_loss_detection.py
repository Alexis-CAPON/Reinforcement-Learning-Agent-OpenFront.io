"""
Test to verify that loss detection works properly
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing loss detection mechanism...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"\nInitial state:")
print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
print(f"  AI Bots  - Tiles: {info['enemy_tiles']}")
print(f"  Total players: 6 (1 RL agent + 5 AI bots)")

# Run IDLE steps and wait for the agent to lose
print(f"\nRunning IDLE steps (only AI acts) until agent loses or 1000 steps...")
print(f"We expect the agent to eventually lose all tiles and episode to terminate.\n")

max_steps = 1000
for i in range(max_steps):
    obs, reward, terminated, truncated, info = env.step(0)  # IDLE - only AI acts

    # Print status every 50 steps
    if i % 50 == 49 or info['tiles'] == 0 or terminated:
        print(f"Step {i+1}:")
        print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
        print(f"  AI Bots  - Tiles: {info['enemy_tiles']}")
        print(f"  Terminated: {terminated}, Truncated: {truncated}")

        if info['tiles'] == 0:
            print(f"  ⚠️  Agent has 0 tiles!")

    if terminated or truncated:
        print(f"\n{'='*60}")
        print(f"Episode ended at step {i+1}!")
        print(f"{'='*60}")

        # Check the episode info
        if 'episode' in info:
            episode_info = info['episode']
            print(f"\nEpisode Summary:")
            print(f"  Final tiles: {episode_info['tiles_final']}")
            print(f"  Won: {episode_info['won']}")
            print(f"  Total reward: {episode_info['r']:.1f}")
            print(f"  Episode length: {episode_info['l']}")

        print(f"\nFinal state:")
        print(f"  Tiles: {info['tiles']}")
        print(f"  Terminated: {terminated}")
        print(f"  Truncated: {truncated}")

        # Verify loss detection worked
        if info['tiles'] == 0 and terminated:
            print(f"\n✅ SUCCESS! Loss detected properly:")
            print(f"   - Agent has 0 tiles")
            print(f"   - Episode terminated (not truncated)")
            print(f"   - Loss penalty should have been applied")
        elif info['tiles'] == 0 and not terminated:
            print(f"\n❌ FAILURE! Loss detection NOT working:")
            print(f"   - Agent has 0 tiles")
            print(f"   - Episode did NOT terminate")
            print(f"   - This is the bug we need to fix!")
        elif terminated and info['tiles'] > 0:
            print(f"\n✅ Agent won or other termination condition met")

        break
else:
    print(f"\n{'='*60}")
    print(f"Reached {max_steps} steps without termination")
    print(f"Final tiles: {info['tiles']}")
    print(f"This suggests the agent is surviving (good) or episodes are too long")
    print(f"{'='*60}")

env.close()
print("\nTest complete!")
