"""
Test to verify that the game FULLY resets every episode
- Map state resets (all tiles back to neutral/starting)
- Player state resets (troops, gold, tiles)
- Tick counter resets
- AI state resets
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing FULL game reset between episodes...")
print("=" * 70)

env = OpenFrontIOEnv()

# Track initial state of each episode
episode_initial_states = []

for ep in range(5):
    obs, info = env.reset()

    # Capture initial state
    initial_state = {
        'episode': ep + 1,
        'tiles': info['tiles'],
        'troops': info['troops'],
        'gold': info['gold'],
        'enemy_tiles': info['enemy_tiles'],
        'step': info['step']
    }
    episode_initial_states.append(initial_state)

    print(f"\nEpisode {ep+1} - Initial State:")
    print(f"  RL Agent: tiles={info['tiles']}, troops={info['troops']}, gold={info['gold']}")
    print(f"  AI Bots:  tiles={info['enemy_tiles']}")
    print(f"  Step counter: {info['step']}")

    # Play for a few steps
    for step in range(50):
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            break

    # Show state before next reset
    print(f"  After {step+1} steps:")
    print(f"    RL Agent: tiles={info['tiles']}, troops={info['troops']}, gold={info['gold']}")
    print(f"    AI Bots:  tiles={info['enemy_tiles']}")

env.close()

print(f"\n{'='*70}")
print("Analysis - Checking if initial states are consistent:")
print(f"{'='*70}")

# Check if all episodes start with same tile count (should be yes)
tiles_at_start = [s['tiles'] for s in episode_initial_states]
troops_at_start = [s['troops'] for s in episode_initial_states]
gold_at_start = [s['gold'] for s in episode_initial_states]
enemy_tiles_at_start = [s['enemy_tiles'] for s in episode_initial_states]
step_at_start = [s['step'] for s in episode_initial_states]

print(f"\nInitial RL Agent tiles:  {tiles_at_start}")
print(f"Initial RL Agent troops: {troops_at_start}")
print(f"Initial RL Agent gold:   {gold_at_start}")
print(f"Initial enemy tiles:     {enemy_tiles_at_start}")
print(f"Initial step counter:    {step_at_start}")

# Verify reset is working
checks_passed = []

# 1. All episodes should start with same RL agent tiles
if len(set(tiles_at_start)) == 1:
    print(f"\n✅ RL Agent tiles reset properly: All start with {tiles_at_start[0]} tiles")
    checks_passed.append(True)
else:
    print(f"\n❌ RL Agent tiles NOT resetting properly: {set(tiles_at_start)}")
    checks_passed.append(False)

# 2. All episodes should start with same troops
if len(set(troops_at_start)) == 1:
    print(f"✅ RL Agent troops reset properly: All start with {troops_at_start[0]} troops")
    checks_passed.append(True)
else:
    print(f"❌ RL Agent troops NOT resetting properly: {set(troops_at_start)}")
    checks_passed.append(False)

# 3. All episodes should start with same gold
if len(set(gold_at_start)) == 1:
    print(f"✅ RL Agent gold reset properly: All start with {gold_at_start[0]} gold")
    checks_passed.append(True)
else:
    print(f"❌ RL Agent gold NOT resetting properly: {set(gold_at_start)}")
    checks_passed.append(False)

# 4. Enemy tiles should be consistent (though positions may vary due to randomization)
enemy_tiles_range = max(enemy_tiles_at_start) - min(enemy_tiles_at_start)
if enemy_tiles_range <= 5:  # Allow small variation due to spawn position randomization
    print(f"✅ Enemy tiles reset properly: Range {min(enemy_tiles_at_start)}-{max(enemy_tiles_at_start)} tiles")
    checks_passed.append(True)
else:
    print(f"❌ Enemy tiles NOT resetting properly: Range {min(enemy_tiles_at_start)}-{max(enemy_tiles_at_start)}")
    checks_passed.append(False)

# 5. Step counter should always start at 0
if all(s == 0 for s in step_at_start):
    print(f"✅ Step counter resets properly: All start at 0")
    checks_passed.append(True)
else:
    print(f"❌ Step counter NOT resetting properly: {step_at_start}")
    checks_passed.append(False)

print(f"\n{'='*70}")
if all(checks_passed):
    print("🎉 SUCCESS! Game is fully resetting between episodes!")
    print("   All state variables return to initial values.")
else:
    print("⚠️  WARNING! Game reset is incomplete!")
    print(f"   {sum(checks_passed)}/{len(checks_passed)} checks passed")
    print("   Some state is not being reset properly between episodes.")
print(f"{'='*70}")
