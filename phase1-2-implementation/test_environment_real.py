"""
Test OpenFrontIO Environment with Real Game Bridge

This tests the full integration: Python → GameWrapper → TypeScript Bridge → Game Engine
"""

import sys
import os
sys.path.insert(0, 'rl_env')

import numpy as np
from gymnasium import spaces

print("=" * 60)
print("Testing Phase 1 Environment (Real Game Integration)")
print("=" * 60)

# Test 1: Import environment
print("\n1. Testing imports...")
try:
    from openfrontio_env import OpenFrontIOEnv
    print("✓ Environment imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create environment
print("\n2. Creating environment with real game bridge...")
print("   NOTE: First reset will be slow (~0.3s) as map loads")
try:
    env = OpenFrontIOEnv()
    print("✓ Environment created")
except Exception as e:
    print(f"✗ Environment creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check spaces
print("\n3. Testing observation and action spaces...")
try:
    obs_space = env.observation_space
    action_space = env.action_space

    assert isinstance(obs_space, spaces.Dict)
    assert 'features' in obs_space.spaces
    assert 'action_mask' in obs_space.spaces

    features_shape = obs_space.spaces['features'].shape
    mask_shape = obs_space.spaces['action_mask'].shape

    print(f"✓ Observation space: Dict")
    print(f"  - features: Box{features_shape}")
    print(f"  - action_mask: Box{mask_shape}")
    print(f"✓ Action space: Discrete({action_space.n})")

except Exception as e:
    print(f"✗ Space check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Reset environment
print("\n4. Testing reset (loading map)...")
try:
    obs, info = env.reset()

    print(f"✓ Reset successful")
    print(f"  Features shape: {obs['features'].shape}")
    print(f"  Features: {obs['features']}")
    print(f"  Action mask: {obs['action_mask']}")
    print(f"  Valid actions: {np.where(obs['action_mask'] == 1)[0]}")
    print(f"  Info: tiles={info['tiles']}, troops={info['troops']}, neighbors={info['num_neighbors']}")

except Exception as e:
    print(f"✗ Reset failed: {e}")
    import traceback
    traceback.print_exc()
    env.close()
    sys.exit(1)

# Test 5: Take steps
print("\n5. Testing game steps...")
try:
    # Test IDLE action
    print("  - Testing IDLE action (0)...")
    obs, reward, terminated, truncated, info = env.step(0)
    print(f"    Reward: {reward:.1f}, Tiles: {info['tiles']}, Step: {info['step']}")

    # Test attack if available
    valid_actions = np.where(obs['action_mask'] == 1)[0]
    print(f"  - Valid actions: {valid_actions}")

    if len(valid_actions) > 1:
        attack_action = valid_actions[1]  # First non-IDLE action
        print(f"  - Testing attack action ({attack_action})...")
        obs, reward, terminated, truncated, info = env.step(attack_action)
        print(f"    Reward: {reward:.1f}, Tiles: {info['tiles']}")

    print("✓ Step execution works")

except Exception as e:
    print(f"✗ Step test failed: {e}")
    import traceback
    traceback.print_exc()
    env.close()
    sys.exit(1)

# Test 6: Run game loop
print("\n6. Running 20 steps...")
try:
    for i in range(20):
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        if i % 5 == 0 or terminated or truncated:
            print(f"  Step {info['step']}: tiles={info['tiles']}, troops={info['troops']}, reward={reward:.1f}")

        if terminated or truncated:
            print(f"  Episode ended: {'WON' if reward > 0 else 'LOST/TIMEOUT'}")
            break

    print("✓ Game loop works")

except Exception as e:
    print(f"✗ Game loop failed: {e}")
    import traceback
    traceback.print_exc()
    env.close()
    sys.exit(1)

# Test 7: Test second reset (should be fast)
print("\n7. Testing second reset (should be fast with caching)...")
try:
    obs, info = env.reset()
    print(f"✓ Second reset successful")
    print(f"  Tiles: {info['tiles']}, Troops: {info['troops']}")

except Exception as e:
    print(f"✗ Second reset failed: {e}")
    import traceback
    traceback.print_exc()
    env.close()
    sys.exit(1)

# Test 8: Run another episode
print("\n8. Running second episode (5 steps)...")
try:
    for i in range(5):
        valid_actions = np.where(obs['action_mask'] == 1)[0]
        action = np.random.choice(valid_actions)
        obs, reward, terminated, truncated, info = env.step(action)

        if i == 0 or i == 4:
            print(f"  Step {info['step']}: tiles={info['tiles']}, reward={reward:.1f}")

        if terminated or truncated:
            break

    print("✓ Second episode works")

except Exception as e:
    print(f"✗ Second episode failed: {e}")
    import traceback
    traceback.print_exc()
    env.close()
    sys.exit(1)

# Cleanup
print("\n9. Cleaning up...")
try:
    env.close()
    print("✓ Environment closed")
except Exception as e:
    print(f"✗ Cleanup failed: {e}")

print("\n" + "=" * 60)
print("SUCCESS! Full Integration Working!")
print("=" * 60)
print("\n✅ Python environment works with real game bridge")
print("✅ All game operations functional")
print("✅ Ready for RL training!")
