"""
Complete reset verification test:
1. Game resets to initial state (consistent starting values)
2. Episodes have variety (different outcomes due to randomization)
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("=" * 70)
print("COMPLETE RESET VERIFICATION TEST")
print("=" * 70)

env = OpenFrontIOEnv()

# Test 1: Initial states are consistent
print("\n[TEST 1] Verifying initial states are consistent...")
initial_states = []

for ep in range(3):
    obs, info = env.reset()
    initial_states.append({
        'tiles': info['tiles'],
        'troops': info['troops'],
        'gold': info['gold'],
        'enemy_tiles': info['enemy_tiles']
    })

tiles_consistent = len(set(s['tiles'] for s in initial_states)) == 1
troops_consistent = len(set(s['troops'] for s in initial_states)) == 1
gold_consistent = len(set(s['gold'] for s in initial_states)) == 1

if tiles_consistent and troops_consistent and gold_consistent:
    print("✅ Initial states are consistent across resets")
    print(f"   Tiles: {initial_states[0]['tiles']}")
    print(f"   Troops: {initial_states[0]['troops']}")
    print(f"   Gold: {initial_states[0]['gold']}")
else:
    print("❌ Initial states are NOT consistent!")

# Test 2: Episodes have variety (different outcomes)
print("\n[TEST 2] Verifying episodes have variety...")
episode_lengths = []

for ep in range(3):
    obs, info = env.reset()

    for step in range(10000):
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            episode_lengths.append(step + 1)
            break

variety = len(set(episode_lengths))
if variety > 1:
    print(f"✅ Episodes have variety: {variety} different lengths")
    print(f"   Episode lengths: {episode_lengths}")
    print(f"   Variation range: {max(episode_lengths) - min(episode_lengths)} steps")
else:
    print(f"❌ Episodes are identical (all {episode_lengths[0]} steps)")
    print(f"   This indicates deterministic behavior!")

# Test 3: State doesn't carry over between episodes
print("\n[TEST 3] Verifying no state carryover...")

# Episode 1: Play until tiles change significantly
obs, info = env.reset()
initial_tiles = info['tiles']

for step in range(100):
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    action = np.random.choice(valid_actions)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break

ep1_final_tiles = info['tiles']
ep1_final_troops = info['troops']
ep1_final_gold = info['gold']

print(f"   Episode 1 ended with: tiles={ep1_final_tiles}, troops={ep1_final_troops}, gold={ep1_final_gold}")

# Episode 2: Should start fresh, not with Episode 1's final state
obs, info = env.reset()
ep2_initial_tiles = info['tiles']
ep2_initial_troops = info['troops']
ep2_initial_gold = info['gold']

print(f"   Episode 2 started with: tiles={ep2_initial_tiles}, troops={ep2_initial_troops}, gold={ep2_initial_gold}")

if ep2_initial_tiles == initial_tiles and ep2_initial_troops == initial_states[0]['troops']:
    print("✅ No state carryover - Episode 2 starts fresh!")
else:
    print("❌ State is carrying over between episodes!")

env.close()

print("\n" + "=" * 70)
print("FINAL VERDICT")
print("=" * 70)

if tiles_consistent and troops_consistent and gold_consistent and variety > 1 and ep2_initial_tiles == initial_tiles:
    print("🎉 ALL TESTS PASSED!")
    print("   ✅ Game resets properly to initial state")
    print("   ✅ Episodes have variety (not deterministic)")
    print("   ✅ No state carries over between episodes")
    print("\n   The environment is ready for training! 🚀")
else:
    print("⚠️  SOME TESTS FAILED!")
    print("   Please review the results above.")

print("=" * 70)
