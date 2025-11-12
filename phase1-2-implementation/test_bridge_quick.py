"""Quick test to check player states"""

import subprocess
import json
import time

bridge_path = '../phase1-implementation/game_bridge/game_bridge_cached.ts'

print("Starting bridge...")
process = subprocess.Popen(
    ['npx', 'tsx', bridge_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    cwd='/Users/alexis/Dev/Lehigh/projects/openfrontio-rl/base-game'
)

time.sleep(0.5)  # Let it start

print("Sending reset command...")
process.stdin.write(json.dumps({'type': 'reset', 'map_name': 'plains'}) + '\n')
process.stdin.flush()

response = process.stdout.readline()
print(f"Response: {response}")

time.sleep(0.1)  # Let stderr accumulate

print("\nSending shutdown...")
process.stdin.write(json.dumps({'type': 'shutdown'}) + '\n')
process.stdin.flush()

process.wait(timeout=2)

print("\n=== STDERR ===")
stderr = process.stderr.read()
print(stderr)
