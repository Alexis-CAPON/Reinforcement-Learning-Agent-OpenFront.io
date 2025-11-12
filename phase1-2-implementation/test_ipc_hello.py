"""
Test IPC Communication - Hello World

This tests basic JSON IPC between Python and Node.js
"""

import subprocess
import json
import sys
import os

print("=" * 60)
print("Testing IPC Communication (Hello World)")
print("=" * 60)

# Path to test bridge
bridge_path = os.path.join(
    os.path.dirname(__file__),
    'game_bridge/test_hello.js'
)

print(f"\n1. Starting Node.js process: {bridge_path}")

try:
    # Start Node.js process
    process = subprocess.Popen(
        ['node', bridge_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    print("✓ Node.js process started")

    # Helper function to send command and receive response
    def send_command(command):
        """Send a command and receive response"""
        print(f"\n  Sending: {json.dumps(command)}")
        process.stdin.write(json.dumps(command) + '\n')
        process.stdin.flush()

        response_line = process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from bridge")

        response = json.loads(response_line.strip())
        print(f"  Received: {json.dumps(response)}")
        return response

    # Test 1: Hello command
    print("\n2. Testing 'hello' command...")
    response = send_command({
        'type': 'hello',
        'name': 'Python'
    })

    assert response['type'] == 'response'
    assert 'Hello Python' in response['message']
    print("✓ Hello command works")

    # Test 2: Echo command
    print("\n3. Testing 'echo' command...")
    test_data = {'foo': 'bar', 'numbers': [1, 2, 3]}
    response = send_command({
        'type': 'echo',
        'data': test_data
    })

    assert response['type'] == 'response'
    assert response['echo'] == test_data
    print("✓ Echo command works")

    # Test 3: Add command
    print("\n4. Testing 'add' command...")
    response = send_command({
        'type': 'add',
        'a': 42,
        'b': 58
    })

    assert response['type'] == 'response'
    assert response['result'] == 100
    print("✓ Add command works")

    # Test 4: Unknown command
    print("\n5. Testing error handling...")
    response = send_command({
        'type': 'unknown_command'
    })

    assert response['type'] == 'error'
    assert 'Unknown command' in response['message']
    print("✓ Error handling works")

    # Test 5: Shutdown
    print("\n6. Testing 'shutdown' command...")
    response = send_command({
        'type': 'shutdown'
    })

    assert response['type'] == 'response'
    assert 'Goodbye' in response['message']
    print("✓ Shutdown command works")

    # Wait for process to exit
    process.wait(timeout=2)
    print("\n✓ Process exited cleanly")

    print("\n" + "=" * 60)
    print("IPC Communication Test Passed!")
    print("=" * 60)
    print("\nThe Python ↔ Node.js IPC is working correctly.")
    print("Next: Implement actual game bridge using this pattern")

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
    stderr = process.stderr.read()
    if stderr:
        print("\nNode.js stderr:")
        print(stderr)

    sys.exit(1)
