"""
Integration Test for Phase 3 - Game Bridge + Environment

Tests the complete pipeline:
1. GameWrapper (Python) ↔ game_bridge.ts (TypeScript)
2. OpenFrontEnv using GameWrapper
3. Random policy for a few episodes
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from game_wrapper import GameWrapper
from environment import OpenFrontEnv


def test_game_wrapper():
    """Test GameWrapper directly"""
    print("=" * 60)
    print("Test 1: GameWrapper Direct Test")
    print("=" * 60)

    try:
        print("\n1.1 Creating GameWrapper...")
        wrapper = GameWrapper(map_name='plains', num_players=11)  # 1 RL + 10 bots
        print("    ✓ GameWrapper created")

        print("\n1.2 Starting new game...")
        wrapper.start_new_game()
        state = wrapper.get_state()
        print("    ✓ Game started")
        print(f"    Tick: {state.tick}")
        print(f"    Territory: {state.tiles_owned} / {state.total_tiles} ({state.territory_pct:.2%})")
        print(f"    Population: {state.population} / {state.max_population}")
        print(f"    Rank: {state.rank} / {state.total_players}")

        print("\n1.3 Testing spatial maps...")
        print(f"    Territory map shape: {state.territory_map.shape}")
        print(f"    Your territory mask: {state.your_territory_mask.shape}")
        print(f"    Enemy density: {state.enemy_count_map.shape}")

        if state.territory_map.size > 0:
            print("    ✓ Spatial maps extracted")
        else:
            print("    ⚠ Spatial maps are empty")

        print("\n1.4 Running 20 game ticks...")
        for i in range(20):
            wrapper.update()
            state = wrapper.get_state()
            if i % 5 == 0:
                print(f"    Tick {state.tick:3d}: "
                      f"tiles={state.tiles_owned:4d}, "
                      f"pop={state.population:5d}, "
                      f"rank={state.rank}/{state.total_players}")

        print("    ✓ Game ticks executed")

        print("\n1.5 Testing direction-based attack...")
        # Try attacking north (direction 0)
        success = wrapper.attack(direction=0, troops=int(state.population * 0.5))
        print(f"    Attack north with 50% troops: {'✓ success' if success else '✗ failed'}")

        print("\n1.6 Closing wrapper...")
        wrapper.close()
        print("    ✓ Wrapper closed")

        print("\n✓ GameWrapper test passed!")
        return True

    except Exception as e:
        print(f"\n✗ GameWrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test OpenFrontEnv with GameWrapper"""
    print("\n" + "=" * 60)
    print("Test 2: OpenFrontEnv Integration Test")
    print("=" * 60)

    try:
        print("\n2.1 Creating environment...")
        env = OpenFrontEnv(game_interface=None, num_bots=10, map_name='plains')
        print("    ✓ Environment created")

        print("\n2.2 Resetting environment...")
        obs, info = env.reset()
        print("    ✓ Environment reset")
        print(f"    Observation map shape: {obs['map'].shape}")
        print(f"    Observation global shape: {obs['global'].shape}")

        # Verify shapes
        assert obs['map'].shape == (128, 128, 5), "Map shape incorrect"
        assert obs['global'].shape == (16,), "Global shape incorrect"
        print("    ✓ Observation shapes correct")

        print("\n2.3 Testing random actions...")
        total_reward = 0
        for step in range(30):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward

            if step % 10 == 0:
                direction = action // 10
                print(f"    Step {step:2d}: "
                      f"action={action:2d} "
                      f"(dir={env.directions[direction]:4s}), "
                      f"reward={reward:7.2f}, "
                      f"done={done}")

            if done:
                print(f"    Episode ended after {step+1} steps")
                break

        print(f"    Total reward: {total_reward:.2f}")
        print("    ✓ Random actions executed")

        print("\n2.4 Closing environment...")
        env.close()
        print("    ✓ Environment closed")

        print("\n✓ Environment test passed!")
        return True

    except Exception as e:
        print(f"\n✗ Environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_episode():
    """Run a complete episode with random policy"""
    print("\n" + "=" * 60)
    print("Test 3: Full Episode Test")
    print("=" * 60)

    try:
        print("\n3.1 Creating environment...")
        env = OpenFrontEnv(game_interface=None, num_bots=10, map_name='plains')

        print("\n3.2 Running full episode...")
        obs, info = env.reset()

        episode_reward = 0
        episode_steps = 0
        max_steps = 100

        while episode_steps < max_steps:
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)

            episode_reward += reward
            episode_steps += 1

            if episode_steps % 25 == 0:
                print(f"    Step {episode_steps:3d}: "
                      f"reward={episode_reward:8.1f}, "
                      f"done={done}")

            if done:
                print(f"\n    Episode ended after {episode_steps} steps")
                print(f"    Final reward: {episode_reward:.2f}")
                break

        if episode_steps >= max_steps:
            print(f"\n    Reached max steps ({max_steps})")

        print("\n3.3 Closing environment...")
        env.close()

        print("\n✓ Full episode test passed!")
        return True

    except Exception as e:
        print(f"\n✗ Full episode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("Phase 3 Integration Tests")
    print("=" * 60)
    print("\nTesting game bridge integration...")
    print("This will start the TypeScript game bridge via IPC")
    print()

    results = []

    # Test 1: GameWrapper
    print("\nStarting Test 1...")
    time.sleep(1)
    results.append(("GameWrapper", test_game_wrapper()))

    # Test 2: Environment
    print("\nStarting Test 2...")
    time.sleep(1)
    results.append(("OpenFrontEnv", test_environment()))

    # Test 3: Full Episode
    print("\nStarting Test 3...")
    time.sleep(1)
    results.append(("Full Episode", test_full_episode()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:20s}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start training: python src/train.py --device cpu --n-envs 4")
        print("  2. Monitor with TensorBoard: tensorboard --logdir runs/")
    else:
        print("SOME TESTS FAILED ✗")
        print("=" * 60)
        print("\nPlease fix the issues above before training.")
        print("\nCommon issues:")
        print("  - TypeScript not compiled: cd game_bridge && npm install")
        print("  - Game bridge not found: check game_bridge/game_bridge.ts")
        print("  - Map files missing: check base-game/ directory")

    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
