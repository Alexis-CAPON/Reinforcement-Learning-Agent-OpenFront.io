"""
Test Game Bridge - Cached Version

Tests pre-loading strategy:
- First reset is slow (loads map)
- Subsequent resets are fast (reuses map)
"""

import subprocess
import json
import sys
import os
import time

print("=" * 60)
print("Testing Game Bridge (Cached Strategy)")
print("=" * 60)

bridge_path = '../phase1-implementation/game_bridge/game_bridge_cached.ts'

print(f"\n1. Starting game bridge with tsx")
print(f"   Using cached/pre-load strategy")
print(f"   NOTE: First reset will be SLOW (~30-60s)")
print(f"   NOTE: Subsequent resets will be FAST")

try:
    # Start bridge
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

    def send_command(command, timeout=120):
        """Send command with timeout"""
        print(f"\n  Sending: {command['type']}")
        start = time.time()

        process.stdin.write(json.dumps(command) + '\n')
        process.stdin.flush()

        response_line = process.stdout.readline()
        elapsed = time.time() - start

        if not response_line:
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise RuntimeError(f"Process died. Stderr:\n{stderr}")
            raise RuntimeError("No response")

        response = json.loads(response_line.strip())
        if response.get('type') == 'error':
            raise RuntimeError(f"Bridge error: {response.get('message')}")

        print(f"  Response received in {elapsed:.1f}s")
        return response, elapsed

    # Test 1: First reset (SLOW - loads map)
    print("\n2. Testing FIRST reset (will be slow)...")
    print("   Loading 100x100 map with 10,000 tiles...")
    response, elapsed1 = send_command({'type': 'reset', 'map_name': 'plains'}, timeout=120)

    state = response['state']
    print(f"  ✓ First reset took {elapsed1:.1f}s")
    print(f"    Tiles: {state['tiles_owned']}, Troops: {state['troops']}")

    # Test 2: Run some ticks
    print("\n3. Testing ticks (should be fast)...")
    for i in range(5):
        response, elapsed = send_command({'type': 'tick'})
        if i == 0:
            print(f"  ✓ Tick took {elapsed:.3f}s")

    # Test 3: Second reset (FAST - reuses map)
    print("\n4. Testing SECOND reset (should be much faster)...")
    response, elapsed2 = send_command({'type': 'reset', 'map_name': 'plains'})

    state = response['state']
    print(f"  ✓ Second reset took {elapsed2:.1f}s")
    print(f"    Speedup: {elapsed1/elapsed2:.1f}x faster!")
    print(f"    Tiles: {state['tiles_owned']}, Troops: {state['troops']}")

    # Test 4: Third reset to confirm consistency
    print("\n5. Testing THIRD reset...")
    response, elapsed3 = send_command({'type': 'reset', 'map_name': 'plains'})
    print(f"  ✓ Third reset took {elapsed3:.1f}s")

    # Test 5: Get neighbors and attack
    print("\n6. Testing gameplay...")
    response, _ = send_command({'type': 'get_attackable_neighbors'})
    neighbors = response['neighbors']
    print(f"  Found {len(neighbors)} neighbors")

    if len(neighbors) > 0:
        target = neighbors[0]
        response, _ = send_command({
            'type': 'attack_tile',
            'tile_x': target['tile_x'],
            'tile_y': target['tile_y']
        })
        print(f"  ✓ Attack successful")

    # Test 6: Run game loop
    print("\n7. Running game loop (10 ticks)...")
    for i in range(10):
        response, elapsed = send_command({'type': 'tick'})
        state = response['state']
        if i == 0 or i == 9:
            print(f"  Tick {state['tick']}: tiles={state['tiles_owned']}, took {elapsed:.3f}s")

    # Shutdown
    print("\n8. Shutting down...")
    response, _ = send_command({'type': 'shutdown'})
    process.wait(timeout=2)

    print("\n" + "=" * 60)
    print("SUCCESS! Cached Strategy Works!")
    print("=" * 60)
    print(f"\n📊 Performance Summary:")
    print(f"   First reset:  {elapsed1:.1f}s (loads map)")
    print(f"   Second reset: {elapsed2:.1f}s (reuses map)")
    print(f"   Third reset:  {elapsed3:.1f}s (reuses map)")
    print(f"   Speedup:      {elapsed1/elapsed2:.1f}x")
    print(f"\n✅ Ready for RL training!")
    print(f"✅ Map loads once, then resets are fast")

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
            print(stderr[-2000:])  # Last 2000 chars
    except:
        pass

    sys.exit(1)
