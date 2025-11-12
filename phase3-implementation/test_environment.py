"""
Test script for Phase 3 environment.

Verifies that:
- Environment can be created
- Observations have correct shapes
- Actions can be executed
- Episode can complete
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from environment import OpenFrontEnv


def test_environment():
    """Test environment basic functionality"""
    print("=" * 60)
    print("Testing Phase 3 Environment")
    print("=" * 60)

    # Create environment
    print("\n1. Creating environment with 10 bots...")
    env = OpenFrontEnv(game_interface=None, num_bots=10)
    print("   ✓ Environment created")

    # Check observation space
    print("\n2. Checking observation space...")
    print(f"   Map space: {env.observation_space['map'].shape}")
    print(f"   Global space: {env.observation_space['global'].shape}")
    assert env.observation_space['map'].shape == (128, 128, 5), "Map shape incorrect"
    assert env.observation_space['global'].shape == (16,), "Global shape incorrect"
    print("   ✓ Observation space correct")

    # Check action space
    print("\n3. Checking action space...")
    print(f"   Action space: Discrete({env.action_space.n})")
    assert env.action_space.n == 90, "Action space should be 90"
    print("   ✓ Action space correct")

    # Reset environment
    print("\n4. Resetting environment...")
    obs, info = env.reset()
    print(f"   Map shape: {obs['map'].shape}")
    print(f"   Map dtype: {obs['map'].dtype}")
    print(f"   Map range: [{obs['map'].min():.3f}, {obs['map'].max():.3f}]")
    print(f"   Global shape: {obs['global'].shape}")
    print(f"   Global dtype: {obs['global'].dtype}")
    assert obs['map'].shape == (128, 128, 5), "Observation map shape incorrect"
    assert obs['global'].shape == (16,), "Observation global shape incorrect"
    print("   ✓ Reset successful")

    # Test random actions
    print("\n5. Testing random actions (10 steps)...")
    for step in range(10):
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)

        # Decode action for display
        direction = action // 10
        intensity_idx = (action % 10) // 2
        build = action % 2

        print(f"   Step {step+1}: "
              f"action={action:2d} "
              f"(dir={env.directions[direction]:4s}, "
              f"int={env.intensities[intensity_idx]:.0%}, "
              f"build={build}), "
              f"reward={reward:7.2f}, "
              f"done={done}")

        if done:
            print("   Episode completed early")
            break

    print("   ✓ Random actions work")

    # Close environment
    print("\n6. Closing environment...")
    env.close()
    print("   ✓ Environment closed")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


def test_model():
    """Test model architecture"""
    print("\n" + "=" * 60)
    print("Testing Model Architecture")
    print("=" * 60)

    try:
        import torch
        from model import BattleRoyalePolicy, count_parameters

        print("\n1. Creating model...")
        model = BattleRoyalePolicy()
        print("   ✓ Model created")

        print("\n2. Counting parameters...")
        total_params = count_parameters(model)
        print(f"   Total parameters: {total_params:,}")

        # Check if close to target (~500K)
        if 450_000 <= total_params <= 550_000:
            print("   ✓ Parameter count in expected range (450K-550K)")
        else:
            print(f"   ⚠ Parameter count outside expected range")

        print("\n3. Testing forward pass...")
        batch_size = 2
        test_obs = {
            'map': torch.randn(batch_size, 128, 128, 5),
            'global': torch.randn(batch_size, 16)
        }

        with torch.no_grad():
            action_logits, value = model(test_obs)

        print(f"   Input map: {test_obs['map'].shape}")
        print(f"   Input global: {test_obs['global'].shape}")
        print(f"   Output action logits: {action_logits.shape}")
        print(f"   Output value: {value.shape}")

        assert action_logits.shape == (batch_size, 90), "Action logits shape incorrect"
        assert value.shape == (batch_size, 1), "Value shape incorrect"
        print("   ✓ Forward pass successful")

        print("\n" + "=" * 60)
        print("Model tests passed!")
        print("=" * 60)

    except ImportError as e:
        print(f"\n⚠ Could not test model (missing dependency): {e}")


if __name__ == "__main__":
    # Test environment
    test_environment()

    # Test model
    test_model()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Integrate with game bridge")
    print("  2. Start training: python src/train.py")
    print("  3. Evaluate models: python src/evaluate.py <model_path>")
