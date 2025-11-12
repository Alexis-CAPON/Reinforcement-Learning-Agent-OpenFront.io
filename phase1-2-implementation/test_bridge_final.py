"""
Test Game Bridge - Final Version with tsx

Uses tsx (TypeScript runner) which is simpler than ts-node/esm
"""

import subprocess
import json
import sys
import os

print("=" * 60)
print("Testing Game Bridge (Final - with tsx)")
print("=" * 60)

bridge_path = '../phase1-implementation/game_bridge/game_bridge_final.ts'

print(f"\n1. Starting game bridge with tsx")
print(f"   Bridge: {bridge_path}")

try:
    # Start with tsx - much simpler than ts-node/esm!
    process = subprocess.Popen(
        ['npx', 'tsx', bridge_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd='/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/base-game'
    )

    print("✓ Process started")

    def send_command(command):
        print(f"\n  Sending: {command['type']}")
        process.stdin.write(json.dumps(command) + '\n')
        process.stdin.flush()

        response_line = process.stdout.readline()
        if not response_line:
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise RuntimeError(f"Process died. Stderr:\n{stderr}")
            raise RuntimeError("No response")

        response = json.loads(response_line.strip())
        if response.get('type') == 'error':
            raise RuntimeError(f"Bridge error: {response.get('message')}")

        return response

    # Test 1: Reset
    print("\n2. Testing game reset...")
    response = send_command({'type': 'reset', 'map_name': 'plains', 'difficulty': 'easy'})

    assert 'state' in response
    state = response['state']

    print(f"  Initial state:")
    print(f"    Tiles: {state['tiles_owned']}")
    print(f"    Troops: {state['troops']}")
    print(f"    Enemy tiles: {state['enemy_tiles']}")
    print(f"    Tick: {state['tick']}")

    assert state['tiles_owned'] >= 1
    assert state['troops'] > 0
    print("✓ Reset works")

    # Test 2: Get neighbors
    print("\n3. Testing get_attackable_neighbors...")
    response = send_command({'type': 'get_attackable_neighbors'})

    neighbors = response['neighbors']
    print(f"  Found {len(neighbors)} attackable neighbors")
    if len(neighbors) > 0:
        print(f"  First: ({neighbors[0]['tile_x']}, {neighbors[0]['tile_y']})")
    print("✓ Get neighbors works")

    # Test 3: Execute ticks
    print("\n4. Testing game ticks...")
    for i in range(5):
        response = send_command({'type': 'tick'})
        state = response['state']
        if i == 0 or i == 4:
            print(f"  Tick {state['tick']}: tiles={state['tiles_owned']}, troops={state['troops']}")
    print("✓ Tick execution works")

    # Test 4: Attack if possible
    if len(neighbors) > 0:
        print("\n5. Testing attack...")
        target = neighbors[0]
        response = send_command({
            'type': 'attack_tile',
            'tile_x': target['tile_x'],
            'tile_y': target['tile_y']
        })
        assert response.get('success') == True
        print(f"✓ Attack works")

    # Test 5: Run more ticks
    print("\n6. Running 10 more ticks...")
    for i in range(10):
        response = send_command({'type': 'tick'})
        state = response['state']
        if state['game_over']:
            print(f"  Game ended at tick {state['tick']}")
            break

    final_state = state
    print(f"  Final: tick={final_state['tick']}, tiles={final_state['tiles_owned']}")
    print("✓ Game loop works")

    # Shutdown
    print("\n7. Shutting down...")
    response = send_command({'type': 'shutdown'})
    process.wait(timeout=2)
    print("✓ Clean shutdown")

    print("\n" + "=" * 60)
    print("SUCCESS! Game Bridge is Working!")
    print("=" * 60)
    print("\n✅ Full game integration complete")
    print("✅ Ready for RL training")

except subprocess.TimeoutExpired:
    print("\n✗ Timeout")
    process.kill()
    sys.exit(1)

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

    if process.poll() is None:
        process.kill()

    try:
        stderr = process.stderr.read()
        if stderr:
            print("\n" + "=" * 60)
            print("Stderr:")
            print("=" * 60)
            print(stderr)
    except:
        pass

    sys.exit(1)
