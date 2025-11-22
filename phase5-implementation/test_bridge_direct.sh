#!/bin/bash
# Direct test of game bridge to see initialization logs

cd "$(dirname "$0")"

# Send reset command to game bridge
echo '{"type":"reset","map_name":"australia_256x256","num_players":11}' | npx tsx game_bridge/game_bridge.ts
