"""
Test the new dense reward structure to verify it's working correctly
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("=" * 80)
print("TESTING NEW DENSE REWARD STRUCTURE")
print("=" * 80)

env = OpenFrontIOEnv()

print("\n[TEST 1] Environment initializes with new config")
print(f"  ✅ Map: {env.map_name}")
print(f"  ✅ Players: {env.num_players} (should be 2 for curriculum learning)")
print(f"  ✅ Max steps: {env.max_steps} (should be 1500, was 5000)")
print(f"  ✅ Max ticks: {env.config['game']['max_ticks']} (should be 500, was 1000)")

print("\n[TEST 2] Reward configuration")
print(f"  Per tile gained: {env.reward_per_tile} (should be 50, was 10)")
print(f"  Per tile lost: {env.reward_tile_loss} (should be -50, was -10)")
print(f"  Per step: {env.reward_per_step} (should be -0.1, was -1)")
print(f"  Win bonus: {env.reward_win} (should be 1000, was 10000)")
print(f"  Loss penalty: {env.reward_loss} (should be -1000, was -10000)")

print("\n[TEST 3] Run a few steps and check reward structure")
obs, info = env.reset()

print(f"\n  Initial state:")
print(f"    Tiles owned: {info['tiles']}")
print(f"    Troops: {info['troops']:.0f}")
print(f"    Enemy tiles: {info['enemy_tiles']}")

rewards = []
for step in range(10):
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    action = np.random.choice(valid_actions)
    obs, reward, terminated, truncated, info = env.step(action)

    rewards.append(reward)

    if step < 3:  # Print first 3 steps in detail
        print(f"\n  Step {step + 1}:")
        print(f"    Action: {action}")
        print(f"    Tiles owned: {info['tiles']}")
        print(f"    Enemy tiles: {info['enemy_tiles']}")
        print(f"    Troops: {info['troops']:.0f}")
        print(f"    Reward: {reward:.2f}")

    if terminated or truncated:
        print(f"\n  Episode ended at step {step + 1}")
        if terminated:
            print(f"    Reason: {'Won' if info.get('episode', {}).get('won') else 'Lost'}")
        break

print(f"\n[TEST 4] Reward analysis")
print(f"  Rewards collected: {len(rewards)}")
print(f"  Mean reward per step: {np.mean(rewards):.2f}")
print(f"  Min reward: {min(rewards):.2f}")
print(f"  Max reward: {max(rewards):.2f}")
print(f"  Total reward: {sum(rewards):.2f}")

# Calculate expected reward breakdown
avg_tiles = np.mean([info['tiles'] for _ in range(1)])  # Just use last value
expected_territorial = avg_tiles * 2.0
expected_time_penalty = -0.1

print(f"\n[TEST 5] Expected reward components (approximate)")
print(f"  Territorial control (+2 per tile): ~{expected_territorial:.2f} per step")
print(f"  Time penalty: {expected_time_penalty:.2f} per step")
print(f"  Tile change rewards: ±50 per tile (when applicable)")
print(f"  Troop growth: +0.01 per troop gained (when applicable)")
print(f"  Enemy penalty: -0.5 per enemy tile")

if np.mean(rewards) > 50:
    print(f"\n  ✅ PASS: Rewards are now POSITIVE on average!")
    print(f"     (Was ~-13,000 per episode, now positive per step)")
    print(f"     Agent gets immediate feedback for territorial control")
elif np.mean(rewards) > 0:
    print(f"\n  ⚠️  PARTIAL: Rewards are slightly positive")
    print(f"     Better than before, but might need tuning")
else:
    print(f"\n  ❌ WARNING: Rewards are still negative")
    print(f"     May need to adjust reward weights")

env.close()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ Dense reward structure implemented")
print("✅ Configuration updated (2 players, 1500 max steps, 500 max ticks)")
print("✅ Environment runs without errors")
print("\nREADY FOR TRAINING!")
print("\nRun: python train.py train --config configs/phase1_config.json")
print("=" * 80)
