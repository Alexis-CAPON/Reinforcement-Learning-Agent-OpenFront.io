"""
Test Python environment without game bridge

This tests the environment logic without needing the TypeScript bridge compiled.
"""

import sys
import os
sys.path.insert(0, 'rl_env')

import numpy as np
from gymnasium import spaces

print("=" * 60)
print("Testing Phase 1 Environment (Python Only)")
print("=" * 60)

# First, set up mock BEFORE importing environment
print("\n1. Setting up mock game wrapper...")

class MockGameWrapper:
    """Mock game wrapper for testing without TypeScript"""

    def __init__(self, *args, **kwargs):
        print(f"  Mock game initialized with tick_interval={kwargs.get('tick_interval_ms', 100)}ms")
        self.tick_count = 0
        self.map_name = kwargs.get('map_name', 'test')
        self.difficulty = kwargs.get('difficulty', 'Easy')

    def reset(self):
        self.tick_count = 0
        return {
            'tiles_owned': 5,
            'troops': 25000,
            'gold': 0,
            'max_troops': 50000,
            'enemy_tiles': 8,
            'border_tiles': 3,
            'cities': 0,
            'tick': 0,
            'has_won': False,
            'has_lost': False,
            'game_over': False
        }

    def tick(self):
        self.tick_count += 1
        return {
            'tiles_owned': 5 + self.tick_count,
            'troops': 25000 + self.tick_count * 100,
            'gold': self.tick_count * 100,
            'max_troops': 50000,
            'enemy_tiles': max(0, 8 - self.tick_count // 10),
            'border_tiles': 3,
            'cities': 0,
            'tick': self.tick_count,
            'has_won': self.tick_count >= 50,
            'has_lost': False,
            'game_over': self.tick_count >= 50
        }

    def get_state(self, player_id=1):
        return {
            'tiles_owned': 5 + self.tick_count,
            'troops': 25000 + self.tick_count * 100,
            'gold': self.tick_count * 100,
            'max_troops': 50000,
            'enemy_tiles': max(0, 8 - self.tick_count // 10),
            'border_tiles': 3,
            'cities': 0,
            'tick': self.tick_count,
            'has_won': False,
            'has_lost': False,
            'game_over': self.tick_count >= 50
        }

    def get_attackable_neighbors(self, player_id=1):
        # Return 3 mock neighbors
        return [
            {'neighbor_idx': 0, 'enemy_player_id': 2, 'tile_x': 10, 'tile_y': 15, 'enemy_troops': 10000},
            {'neighbor_idx': 1, 'enemy_player_id': 2, 'tile_x': 11, 'tile_y': 15, 'enemy_troops': 8000},
            {'neighbor_idx': 2, 'enemy_player_id': 2, 'tile_x': 10, 'tile_y': 16, 'enemy_troops': 12000},
        ]

    def attack_tile(self, player_id, tile_x, tile_y):
        print(f"    Mock attack: player {player_id} attacks ({tile_x}, {tile_y})")

    def close(self):
        pass

# Create a mock module
class MockGameWrapperModule:
    GameWrapper = MockGameWrapper

# Replace the game_wrapper module BEFORE importing openfrontio_env
sys.modules['game_wrapper'] = MockGameWrapperModule()

print("✓ Mock configured")

# Test 2: Import environment
print("\n2. Testing imports...")
try:
    from openfrontio_env import OpenFrontIOEnv
    print("✓ Environment imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check observation space
print("\n3. Testing observation space...")
try:
    env = OpenFrontIOEnv()
    obs_space = env.observation_space

    assert isinstance(obs_space, spaces.Dict)
    assert 'features' in obs_space.spaces
    assert 'action_mask' in obs_space.spaces

    features_shape = obs_space.spaces['features'].shape
    mask_shape = obs_space.spaces['action_mask'].shape

    print(f"✓ Observation space: Dict")
    print(f"  - features: Box{features_shape}")
    print(f"  - action_mask: Box{mask_shape}")

except Exception as e:
    print(f"✗ Observation space test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check action space
print("\n4. Testing action space...")
try:
    action_space = env.action_space
    print(f"✓ Action space: Discrete({action_space.n})")
    assert action_space.n == 9, f"Expected 9 actions, got {action_space.n}"
except Exception as e:
    print(f"✗ Action space test failed: {e}")
    sys.exit(1)

# Test 5: Testing environment with mock game
print("\n5. Testing environment with mock game...")
try:
    # Test reset
    print("  - Testing reset...")
    obs, info = env.reset()

    print(f"    Features shape: {obs['features'].shape}")
    print(f"    Features: {obs['features']}")
    print(f"    Action mask: {obs['action_mask']}")
    print(f"    Valid actions: {np.where(obs['action_mask'] == 1)[0]}")
    print(f"    Info: tiles={info['tiles']}, troops={info['troops']}, neighbors={info['num_neighbors']}")

    # Test step
    print("  - Testing step with IDLE action...")
    obs, reward, terminated, truncated, info = env.step(0)

    print(f"    Action: 0 (IDLE), Reward: {reward:.1f}")
    print(f"    New tiles: {info['tiles']}, Step: {info['step']}")
    print(f"    Terminated: {terminated}, Truncated: {truncated}")

    # Test attack action
    print("  - Testing step with attack action...")
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    if len(valid_actions) > 1:
        attack_action = valid_actions[1]  # First attack action
        obs, reward, terminated, truncated, info = env.step(attack_action)
        print(f"    Action: {attack_action} (Attack), Reward: {reward:.1f}")
        print(f"    Tiles: {info['tiles']}, Terminated: {terminated}")

    # Test multiple steps
    print("  - Testing 10 more steps...")
    for i in range(10):
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        if i % 3 == 0:  # Print every 3rd step
            print(f"    Step {info['step']}: tiles={info['tiles']}, reward={reward:.1f}")

        if terminated or truncated:
            print(f"    Episode ended at step {info['step']}: won={terminated and reward > 0}")
            break

    print("✓ Environment works with mock game!")

except Exception as e:
    print(f"✗ Environment test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test full episode
print("\n6. Testing full episode...")
try:
    obs, info = env.reset()
    total_reward = 0
    steps = 0

    while steps < 100:
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        total_reward += reward
        steps += 1

        if terminated or truncated:
            break

    print(f"✓ Episode completed:")
    print(f"  - Steps: {steps}")
    print(f"  - Total reward: {total_reward:.1f}")
    print(f"  - Final tiles: {info['tiles']}")
    print(f"  - Terminated: {terminated}, Truncated: {truncated}")

except Exception as e:
    print(f"✗ Full episode test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Python-only tests complete!")
print("=" * 60)
print("\nAll tests passed! Environment logic is working correctly.")
print("\nNext step: Compile TypeScript bridge and test full integration")
