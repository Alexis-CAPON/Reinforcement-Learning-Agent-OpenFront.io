"""
Test Game Bridge V2 with real game

This tests the actual OpenFront.io game integration.
"""

import subprocess
import json
import sys
import os

print("=" * 60)
print("Testing Game Bridge V2 (Real Game)")
print("=" * 60)

# Path to bridge (TypeScript file) - relative to base-game dir
bridge_path_abs = os.path.join(
    os.path.dirname(__file__),
    'game_bridge/game_bridge_v3.ts'
)
# Make it relative to base-game
bridge_path = '../phase1-implementation/game_bridge/game_bridge_v3.ts'

print(f"\n1. Starting Node.js game bridge V3 with ts-node")
print(f"   Bridge: {bridge_path_abs}")

try:
    # Start Node.js process with ts-node ESM loader
    # Run from base-game directory so ts-node can find node_modules
    process = subprocess.Popen(
        ['node', '--loader', 'ts-node/esm', '--experimental-specifier-resolution=node', bridge_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd='/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/base-game'  # Run from base-game dir
    )

    print("✓ Node.js process started")

    # Helper function
    def send_command(command):
        """Send a command and receive response"""
        print(f"\n  Sending: {command['type']}")
        process.stdin.write(json.dumps(command) + '\n')
        process.stdin.flush()

        response_line = process.stdout.readline()
        if not response_line:
            # Check if process died
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise RuntimeError(f"Process died. Stderr:\n{stderr}")
            raise RuntimeError("No response from bridge")

        response = json.loads(response_line.strip())
        if response.get('type') == 'error':
            raise RuntimeError(f"Bridge error: {response.get('message')}")

        return response

    # Test 1: Reset game
    print("\n2. Testing game reset with 'plains' map...")
    response = send_command({
        'type': 'reset',
        'map_name': 'plains',
        'difficulty': 'easy',
        'tick_interval': 100
    })

    assert 'state' in response
    state = response['state']

    print(f"  Initial state:")
    print(f"    Tiles owned: {state['tiles_owned']}")
    print(f"    Troops: {state['troops']}")
    print(f"    Enemy tiles: {state['enemy_tiles']}")
    print(f"    Tick: {state['tick']}")

    assert state['tiles_owned'] >= 1, "Should own at least spawn tile"
    assert state['troops'] > 0, "Should have troops"
    print("✓ Game reset works")

    # Test 2: Get state
    print("\n3. Testing get_state...")
    response = send_command({'type': 'get_state'})

    assert 'state' in response
    print("✓ Get state works")

    # Test 3: Get attackable neighbors
    print("\n4. Testing get_attackable_neighbors...")
    response = send_command({'type': 'get_attackable_neighbors'})

    assert 'neighbors' in response
    neighbors = response['neighbors']
    print(f"  Found {len(neighbors)} attackable neighbors")

    if len(neighbors) > 0:
        print(f"  First neighbor: ({neighbors[0]['tile_x']}, {neighbors[0]['tile_y']})")
    print("✓ Get neighbors works")

    # Test 4: Execute a few ticks
    print("\n5. Testing game tick execution...")
    for i in range(5):
        response = send_command({'type': 'tick'})
        state = response['state']

        if i == 0 or i == 4:
            print(f"  Tick {state['tick']}: tiles={state['tiles_owned']}, troops={state['troops']}")

    print("✓ Tick execution works")

    # Test 5: Attack (if we have neighbors)
    if len(neighbors) > 0:
        print("\n6. Testing attack...")
        target = neighbors[0]
        response = send_command({
            'type': 'attack_tile',
            'tile_x': target['tile_x'],
            'tile_y': target['tile_y']
        })

        assert response.get('success') == True
        print(f"✓ Attack tile ({target['tile_x']}, {target['tile_y']}) works")

    # Test 6: Run game for a few more ticks
    print("\n7. Running game for 10 more ticks...")
    for i in range(10):
        response = send_command({'type': 'tick'})
        state = response['state']

        if state['game_over']:
            print(f"  Game ended at tick {state['tick']}")
            print(f"  Won: {state['has_won']}, Lost: {state['has_lost']}")
            break

    final_state = state
    print(f"  Final state:")
    print(f"    Tick: {final_state['tick']}")
    print(f"    Tiles: {final_state['tiles_owned']}")
    print(f"    Troops: {final_state['troops']}")
    print(f"    Enemy tiles: {final_state['enemy_tiles']}")
    print("✓ Game loop works")

    # Shutdown
    print("\n8. Shutting down...")
    response = send_command({'type': 'shutdown'})
    process.wait(timeout=2)
    print("✓ Clean shutdown")

    print("\n" + "=" * 60)
    print("Game Bridge V2 Test PASSED!")
    print("=" * 60)
    print("\n✓ Full game integration is working!")
    print("✓ Ready for RL training")

except subprocess.TimeoutExpired:
    print("\n✗ Process didn't exit in time")
    process.kill()
    sys.exit(1)

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

    # Print stderr for debugging
    if process.poll() is None:
        process.kill()

    try:
        stderr = process.stderr.read()
        if stderr:
            print("\n" + "=" * 60)
            print("Node.js stderr output:")
            print("=" * 60)
            print(stderr)
    except:
        pass

    sys.exit(1)
