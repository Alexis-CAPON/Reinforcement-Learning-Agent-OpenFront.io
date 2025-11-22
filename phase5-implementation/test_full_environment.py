#!/usr/bin/env python3
"""
Comprehensive test for full-game environment
Tests all action types, state observations, and action masking
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
import numpy as np
from environment_full_game import OpenFrontEnvFullGame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_environment_creation():
    """Test environment can be created"""
    logger.info("=" * 80)
    logger.info("TEST 1: Environment Creation")
    logger.info("=" * 80)

    env = OpenFrontEnvFullGame(map_name='australia_256x256', num_bots=10, frame_stack=4)
    logger.info(f"✅ Environment created successfully")
    logger.info(f"   Action space: {env.action_space}")
    logger.info(f"   Observation space: {env.observation_space}")

    return env


def test_reset(env):
    """Test environment reset"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Environment Reset")
    logger.info("=" * 80)

    obs, info = env.reset()

    # Check observation structure
    assert 'map' in obs, "Missing 'map' in observation"
    assert 'global' in obs, "Missing 'global' in observation"
    assert 'clusters' in obs, "Missing 'clusters' in observation"

    logger.info(f"✅ Reset successful")
    logger.info(f"   Map shape: {obs['map'].shape}")
    logger.info(f"   Global shape: {obs['global'].shape}")
    logger.info(f"   Clusters shape: {obs['clusters'].shape}")
    logger.info(f"   Info keys: {list(info.keys())}")

    # Check map observation has correct shape (with frame_stack=4)
    expected_map = (128, 128, 64)  # 16 channels × 4 frames
    assert obs['map'].shape == expected_map, f"Expected map shape {expected_map}, got {obs['map'].shape}"

    # Check global observation has correct shape (with frame_stack=4)
    expected_global = (128,)  # 32 features × 4 frames
    assert obs['global'].shape == expected_global, f"Expected global shape {expected_global}, got {obs['global'].shape}"

    # Check clusters observation
    expected_clusters = (5, 6)  # 5 clusters, 6 features each
    assert obs['clusters'].shape == expected_clusters, f"Expected clusters shape {expected_clusters}, got {obs['clusters'].shape}"

    logger.info(f"   ✓ Map observation shape correct: {obs['map'].shape}")
    logger.info(f"   ✓ Global observation shape correct: {obs['global'].shape}")
    logger.info(f"   ✓ Clusters observation shape correct: {obs['clusters'].shape}")

    return obs, info


def test_action_masks(env):
    """Test action masking"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Action Masking")
    logger.info("=" * 80)

    masks = env.action_masks()
    expected_shape = (38500,)  # Flattened action space for Discrete

    assert masks.shape == expected_shape, f"Expected mask shape {expected_shape}, got {masks.shape}"
    logger.info(f"✅ Action masks shape correct: {masks.shape}")

    # Count valid actions
    total_actions = masks.size
    valid_actions = masks.sum()
    invalid_actions = total_actions - valid_actions

    logger.info(f"   Total action space: {total_actions:,}")
    logger.info(f"   Valid actions: {int(valid_actions):,}")
    logger.info(f"   Masked actions: {int(invalid_actions):,}")
    logger.info(f"   Masking ratio: {invalid_actions/total_actions:.1%}")

    # Verify at least some actions are valid
    assert valid_actions > 0, "No valid actions available!"
    logger.info(f"   ✓ At least some actions are valid")

    # Check action distribution (sample per-cluster)
    logger.info("\n   Action space structure verified:")
    logger.info(f"   5 clusters × 11 action types × 5 intensities × 7 building types × 2 nuke types × 10 tiles")
    logger.info(f"   = {5*11*5*7*2*10:,} total actions")

    return masks


def test_attack_actions(env):
    """Test attack actions"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Attack Actions")
    logger.info("=" * 80)

    success_count = 0
    action_shape = (5, 11, 5, 7, 2, 10)  # Correct shape

    # Try attacks from different clusters and directions
    for cluster_id in range(1):  # Only test first cluster
        for direction in range(5):  # Test a few directions
            # Create attack action: (cluster_id, action_type=0 (attack), direction, intensity=2 (50%), 0, 0)
            multi_action = (cluster_id, 0, direction, 2, 0, 0)
            flat_action = np.ravel_multi_index(multi_action, action_shape)

            try:
                obs, reward, terminated, truncated, info = env.step(flat_action)
                logger.info(f"   Cluster {cluster_id}, Direction {direction}: reward={reward:.3f}")
                success_count += 1

                if success_count >= 3:  # Test a few attacks
                    break
            except Exception as e:
                logger.warning(f"   Cluster {cluster_id}, Direction {direction}: {e}")

        if success_count >= 3:
            break

    assert success_count > 0, "No attack actions succeeded!"
    logger.info(f"✅ Attack actions working ({success_count} successful)")

    return True


def test_build_actions(env):
    """Test building actions"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Building Actions")
    logger.info("=" * 80)

    action_shape = (5, 11, 5, 7, 2, 10)  # Correct shape
    building_types = [
        (1, "City"),
        (2, "Port"),
        (3, "Silo"),
        (4, "SAM Launcher"),
        (5, "Defense Post"),
        (6, "Factory")
    ]

    for build_type_idx, build_name in building_types:
        # Create build action: (cluster_id=0, action_type=9 (build), 0, build_type, 0, tile=5)
        multi_action = (0, 9, 0, build_type_idx, 0, 5)
        flat_action = np.ravel_multi_index(multi_action, action_shape)

        try:
            obs, reward, terminated, truncated, info = env.step(flat_action)
            logger.info(f"   Build {build_name}: reward={reward:.3f}, terminated={terminated}")
        except Exception as e:
            logger.error(f"   Build {build_name} failed: {e}")
            raise

    logger.info(f"✅ All building action types executed (may fail due to resources)")
    return True


def test_nuke_actions(env):
    """Test nuke actions"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Nuke Actions")
    logger.info("=" * 80)

    action_shape = (5, 11, 5, 7, 2, 10)  # Correct shape
    nuke_types = [
        (0, "Atom Bomb"),
        (1, "Hydrogen Bomb")
    ]

    for nuke_idx, nuke_name in nuke_types:
        # Create nuke action: (cluster_id=0, action_type=10 (nuke), 0, 0, nuke_type, tile=5)
        multi_action = (0, 10, 0, 0, nuke_idx, 5)
        flat_action = np.ravel_multi_index(multi_action, action_shape)

        try:
            obs, reward, terminated, truncated, info = env.step(flat_action)
            logger.info(f"   Launch {nuke_name}: reward={reward:.3f}, terminated={terminated}")
        except Exception as e:
            logger.error(f"   Launch {nuke_name} failed: {e}")
            raise

    logger.info(f"✅ All nuke action types executed (may fail due to availability)")
    return True


def test_state_observations(env):
    """Test state observation features"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: State Observations")
    logger.info("=" * 80)

    state = env.game.get_state()

    # Check core state
    logger.info(f"   Tick: {state.tick}")
    logger.info(f"   Game over: {state.game_over}")
    logger.info(f"   Tiles owned: {state.tiles_owned}")
    logger.info(f"   Population: {state.population}")
    logger.info(f"   Gold: {state.gold}")
    logger.info(f"   Rank: {state.rank}/{state.total_players}")

    # Check clusters
    logger.info(f"   Clusters: {len(state.clusters)}")
    for i, cluster in enumerate(state.clusters[:3]):
        logger.info(f"      Cluster {i}: {len(cluster['tiles'])} tiles, {cluster['troop_count']} troops")

    # Check buildings
    logger.info(f"   Cities: {state.cities_count}")
    logger.info(f"   Ports: {state.ports_count}")
    logger.info(f"   Silos: {state.silos_count}")
    logger.info(f"   SAM Launchers: {state.sam_launchers_count}")
    logger.info(f"   Defense Posts: {state.defense_posts_count}")
    logger.info(f"   Factories: {state.factories_count}")

    # Check nukes
    logger.info(f"   Atom Bombs: {state.atom_bombs_available}")
    logger.info(f"   Hydrogen Bombs: {state.hydrogen_bombs_available}")
    logger.info(f"   Can launch nuke: {state.can_launch_nuke}")

    # Check spatial maps
    logger.info(f"   Territory map: {state.territory_map.shape}")
    logger.info(f"   Troop map: {state.troop_map.shape}")

    logger.info(f"✅ All state features accessible")
    return True


def test_full_episode(env):
    """Test running a full episode"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 8: Full Episode (100 steps)")
    logger.info("=" * 80)

    obs, info = env.reset()

    total_reward = 0
    step_count = 0
    max_steps = 100

    while step_count < max_steps:
        # Get valid action mask
        masks = env.action_masks()

        # Sample random valid action
        flat_mask = masks.flatten()
        valid_indices = np.where(flat_mask)[0]

        if len(valid_indices) == 0:
            logger.warning(f"   No valid actions at step {step_count}!")
            break

        # Choose random valid action (already a flat index)
        action = int(np.random.choice(valid_indices))

        # Take step
        obs, reward, terminated, truncated, info = env.step(action)

        total_reward += reward
        step_count += 1

        if step_count % 20 == 0:
            state = env.game.get_state()
            logger.info(f"   Step {step_count}: reward={reward:.3f}, tiles={state.tiles_owned}, "
                       f"pop={state.population}, clusters={len(state.clusters)}")

        if terminated or truncated:
            logger.info(f"   Episode ended at step {step_count} (terminated={terminated}, truncated={truncated})")
            break

    logger.info(f"✅ Completed {step_count} steps")
    logger.info(f"   Total reward: {total_reward:.3f}")
    logger.info(f"   Average reward: {total_reward/step_count:.3f}")

    return True


def run_all_tests():
    """Run all tests"""
    logger.info("\n\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "FULL ENVIRONMENT COMPREHENSIVE TEST" + " " * 28 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")

    try:
        # Test 1: Creation
        env = test_environment_creation()

        # Test 2: Reset
        obs, info = test_reset(env)

        # Test 3: Action masks
        masks = test_action_masks(env)

        # Test 4: Attack actions
        test_attack_actions(env)

        # Test 5: Build actions
        test_build_actions(env)

        # Test 6: Nuke actions
        test_nuke_actions(env)

        # Test 7: State observations
        test_state_observations(env)

        # Test 8: Full episode
        test_full_episode(env)

        # Success!
        logger.info("\n\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "✅ ALL TESTS PASSED" + " " * 34 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("\n")
        logger.info("The environment is fully functional and ready for training!")
        logger.info("\n")

        env.close()
        return True

    except Exception as e:
        logger.error("\n\n")
        logger.error("╔" + "=" * 78 + "╗")
        logger.error("║" + " " * 30 + "❌ TEST FAILED" + " " * 34 + "║")
        logger.error("╚" + "=" * 78 + "╝")
        logger.error(f"\nError: {e}")
        logger.error("\n", exc_info=True)

        if 'env' in locals():
            env.close()

        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
