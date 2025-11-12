"""
Test to verify that episodes are actually different (not deterministic)
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing episode variety (checking for determinism bug)...")
print("=" * 70)

env = OpenFrontIOEnv()

# Run 5 episodes and track their lengths
episode_lengths = []
episode_final_tiles = []

for ep in range(5):
    obs, info = env.reset()

    initial_tiles = info['tiles']
    print(f"\nEpisode {ep+1}: Starting tiles = {initial_tiles}")

    step_count = 0
    for step in range(10000):
        # Take random valid actions
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)

        obs, reward, terminated, truncated, info = env.step(action)
        step_count += 1

        if terminated or truncated:
            episode_lengths.append(step_count)
            episode_final_tiles.append(info['tiles'])
            print(f"  Ended at step {step_count}, final tiles = {info['tiles']}")
            break

env.close()

print(f"\n{'='*70}")
print("Results:")
print(f"  Episode lengths: {episode_lengths}")
print(f"  Final tiles:     {episode_final_tiles}")

# Check if episodes are identical (determinism bug)
if len(set(episode_lengths)) == 1:
    print(f"\n❌ PROBLEM! All episodes ended at exactly {episode_lengths[0]} steps!")
    print(f"   This means the game is NOT resetting properly - it's deterministic!")
    print(f"   The spawn positions and/or AI behavior are identical every time.")
else:
    print(f"\n✅ SUCCESS! Episodes have varying lengths: {set(episode_lengths)}")
    print(f"   The game IS resetting properly with variation.")
    print(f"   Episode length variation: {max(episode_lengths) - min(episode_lengths)} steps")

print(f"{'='*70}")
