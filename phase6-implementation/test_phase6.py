#!/usr/bin/env python3
"""
Test script for Phase 6 - Cities Only environment

Verifies:
- Environment creation
- Action space size (2,500)
- Observation space shapes
- Action masking functionality
- Basic episode run
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from environment_cities import OpenFrontEnvCities

def test_environment():
    """Test Phase 6 environment creation and basic functionality."""

    print("=" * 80)
    print("PHASE 6 ENVIRONMENT TEST")
    print("=" * 80)

    # Test 1: Environment creation
    print("\n[TEST 1] Creating environment...")

    # Create a simple stub game interface for testing
    class StubGame:
        def get_state(self):
            class State:
                territory_pct = 0.1
                tiles_owned = 100
                total_tiles = 1000
                neutral_tiles = 800
                border_tiles = 50
                territory_change = 0.0
                population = 1000
                max_population = 10000
                population_growth_rate = 0.01
                border_pressure = 0.5
                rank = 5
                total_players = 11
                alive_players = 10
                time_alive = 100
                gold = 500
                cities_count = 2
                can_build_city = True
                territory_map = [[0] * 256 for _ in range(256)]
                our_cities_positions = []
                clusters = [
                    {'tiles': [1, 2, 3], 'troop_count': 500, 'border_tiles': [1, 2],
                     'center_x': 100, 'center_y': 100}
                ]
                game_over = False
                has_won = False
                has_lost = False
            return State()

        def start_new_game(self, num_bots=10):
            pass

        def attack_cluster(self, cluster_id, direction, troops_pct):
            return True

        def build_unit(self, unit_type, tile_x, tile_y):
            return True

        def update(self):
            pass

        def close(self):
            pass

    try:
        env = OpenFrontEnvCities(
            game_interface=StubGame(),
            num_bots=10,
            map_name='australia_256x256',
            frame_stack=4
        )
        print("✓ Environment created successfully")
    except Exception as e:
        print(f"✗ Failed to create environment: {e}")
        return False

    # Test 2: Action space size
    print("\n[TEST 2] Checking action space...")
    expected_action_space = 2500
    actual_action_space = env.action_space.n
    if actual_action_space == expected_action_space:
        print(f"✓ Action space correct: {actual_action_space:,} actions")
    else:
        print(f"✗ Action space incorrect: expected {expected_action_space:,}, got {actual_action_space:,}")
        return False

    # Test 3: Action dimensions
    print("\n[TEST 3] Checking action dimensions...")
    expected_dims = (5, 10, 5, 10)
    actual_dims = env.action_dims
    if actual_dims == expected_dims:
        print(f"✓ Action dimensions correct: {actual_dims}")
        print(f"  - Clusters: {actual_dims[0]}")
        print(f"  - Action types: {actual_dims[1]} (0-7=attack, 8=WAIT, 9=BUILD_CITY)")
        print(f"  - Intensities: {actual_dims[2]}")
        print(f"  - Tiles: {actual_dims[3]}")
    else:
        print(f"✗ Action dimensions incorrect: expected {expected_dims}, got {actual_dims}")
        return False

    # Test 4: Observation space
    print("\n[TEST 4] Checking observation space...")
    obs_space = env.observation_space

    # Check map space
    expected_map_shape = (128, 128, 8 * 4)  # 8 channels × 4 frame stack
    actual_map_shape = obs_space['map'].shape
    if actual_map_shape == expected_map_shape:
        print(f"✓ Map observation shape correct: {actual_map_shape}")
        print(f"  - Spatial: 128×128")
        print(f"  - Channels: 8 (simplified from 16)")
        print(f"  - Frame stack: 4")
    else:
        print(f"✗ Map shape incorrect: expected {expected_map_shape}, got {actual_map_shape}")
        return False

    # Check global features
    expected_global_shape = (16 * 4,)  # 16 features × 4 frame stack
    actual_global_shape = obs_space['global'].shape
    if actual_global_shape == expected_global_shape:
        print(f"✓ Global features shape correct: {actual_global_shape}")
        print(f"  - Features: 16 (simplified from 32)")
        print(f"  - Frame stack: 4")
    else:
        print(f"✗ Global shape incorrect: expected {expected_global_shape}, got {actual_global_shape}")
        return False

    # Check cluster features
    expected_cluster_shape = (5, 4)  # 5 clusters × 4 features
    actual_cluster_shape = obs_space['clusters'].shape
    if actual_cluster_shape == expected_cluster_shape:
        print(f"✓ Cluster features shape correct: {actual_cluster_shape}")
        print(f"  - Clusters: 5")
        print(f"  - Features per cluster: 4 (simplified from 6)")
    else:
        print(f"✗ Cluster shape incorrect: expected {expected_cluster_shape}, got {actual_cluster_shape}")
        return False

    # Test 5: Action masking
    print("\n[TEST 5] Testing action masking...")
    try:
        mask = env.action_masks()
        if len(mask) == expected_action_space:
            print(f"✓ Action mask shape correct: {len(mask):,} elements")
            num_valid = np.sum(mask)
            print(f"  - Valid actions: {num_valid:,} ({num_valid/len(mask)*100:.1f}%)")
        else:
            print(f"✗ Action mask size incorrect: expected {expected_action_space:,}, got {len(mask):,}")
            return False
    except Exception as e:
        print(f"✗ Action masking failed: {e}")
        return False

    # Test 6: Reset and observation
    print("\n[TEST 6] Testing reset and observation...")
    try:
        obs, info = env.reset()
        print(f"✓ Environment reset successfully")
        print(f"  - Observation keys: {list(obs.keys())}")
        print(f"  - Map shape: {obs['map'].shape}")
        print(f"  - Global shape: {obs['global'].shape}")
        print(f"  - Clusters shape: {obs['clusters'].shape}")
    except Exception as e:
        print(f"✗ Reset failed: {e}")
        return False

    # Test 7: Step execution
    print("\n[TEST 7] Testing step execution...")
    try:
        # Take a random valid action
        valid_actions = np.where(mask)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"✓ Step executed successfully")
        print(f"  - Action: {action}")
        print(f"  - Reward: {reward:.2f}")
        print(f"  - Terminated: {terminated}")
        print(f"  - Truncated: {truncated}")
    except Exception as e:
        print(f"✗ Step failed: {e}")
        return False

    # Test 8: Compare with Phase 5
    print("\n[TEST 8] Comparison with Phase 5...")
    phase5_actions = 38500
    phase5_channels = 16
    phase5_global = 32
    phase5_cluster_features = 6

    reduction = (1 - expected_action_space / phase5_actions) * 100
    print(f"✓ Action space reduced by {reduction:.1f}%: {phase5_actions:,} → {expected_action_space:,}")

    channel_reduction = (1 - 8 / phase5_channels) * 100
    print(f"✓ Spatial channels reduced by {channel_reduction:.1f}%: {phase5_channels} → 8")

    global_reduction = (1 - 16 / phase5_global) * 100
    print(f"✓ Global features reduced by {global_reduction:.1f}%: {phase5_global} → 16")

    cluster_reduction = (1 - 4 / phase5_cluster_features) * 100
    print(f"✓ Cluster features reduced by {cluster_reduction:.1f}%: {phase5_cluster_features} → 4")

    # Cleanup
    env.close()

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print("\nPhase 6 environment is ready for training!")
    print(f"Action space: 5 × 10 × 5 × 10 = 2,500 actions")
    print(f"Observation: 128×128×8 channels + 16 global + 5×4 clusters")
    print(f"Features: Cities only, Territory control, Gold accumulation")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = test_environment()
    sys.exit(0 if success else 1)
