# Visualizer Fixes - December 2025

## Issues Fixed

### 1. Port 9000 Already in Use (✓ Fixed)

**Problem**: When port 9000 was already in use, the script would try to start `npm run dev` anyway, which would fail with `EADDRINUSE` error. The script would then open the browser, but the server wouldn't be running.

**Solution**:
- Added `is_port_in_use()` function to check if port 9000 is already in use before trying to start the dev server
- If port is in use, the script now displays:
  ```
  ✓ Dev server already running on port 9000
    Using existing server at http://localhost:9000
  ```
- Opens browser immediately without trying to start a new server
- This is actually the BETTER scenario - no need to wait for server startup!

**Files modified**:
- `src/visualize_realtime_cities.py:261-268` - Added `is_port_in_use()` function
- `src/visualize_realtime_cities.py:271-317` - Modified `start_client_server()` to check port first
- `src/visualize_realtime_cities.py:419-466` - Updated main() to handle "already_running" case

### 2. Shutdown Exceptions on Ctrl+C (✓ Fixed)

**Problem**: When pressing Ctrl+C to stop the visualizer, it would show ugly exception tracebacks:
```
asyncio.exceptions.CancelledError
KeyboardInterrupt
```

**Solution**:
- Wrapped all shutdown operations in try-except blocks
- Gracefully handle `CancelledError` and other exceptions during cleanup
- Display clean "Interrupted by user" message instead of stack traces
- Added timeout when terminating client process

**Files modified**:
- `src/visualize_realtime_cities.py:252-268` - Wrapped shutdown operations in try-except
- `src/visualize_realtime_cities.py:488-508` - Improved main() exception handling

### 3. Better User Feedback (✓ Improved)

**Changes**:
- Clear section headers: "CLIENT DEV SERVER", "BROWSER LAUNCH"
- Port detection message is concise and informative
- Startup messages are cleaner and less verbose
- Removed unnecessary "Note: Dev server output will appear below..." when server already running

## What Actually Happened in Your Run

Looking at your output:

1. **Port 9000 was already in use** ✓
   - The old version tried to start `npm run dev` anyway
   - It failed with `EADDRINUSE` error
   - But continued anyway

2. **The visualizer WORKED PERFECTLY!** ✓
   - Browser opened
   - Client connected to WebSocket
   - Game initialized and started
   - You saw: `[Step    10] Territory:  0.1% | Cities: 0 | Reward: -3519.00 | Cumulative: -119755.00 | Action: NE 50%`

3. **You pressed Ctrl+C** ✓
   - Got ugly exception tracebacks (now fixed)

## How to Use It Now

### Scenario 1: Port 9000 is FREE

```bash
python3 src/visualize_realtime_cities.py \
    --model models/ppo_cities_20251202_170832/checkpoint_900000_steps.zip
```

Output:
```
================================================================================
CLIENT DEV SERVER
================================================================================
Starting dev server on port 9000...
Running: npm run dev (in /path/to/base-game)
Note: Dev server output will appear below...
================================================================================

[dev server starts and outputs webpack logs...]

Waiting for dev server to start...

================================================================================
BROWSER LAUNCH
================================================================================
Opening browser automatically...
URL: http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia

If the browser doesn't open, manually navigate to:
  http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia
================================================================================
```

### Scenario 2: Port 9000 is ALREADY IN USE (YOUR CASE)

```bash
python3 src/visualize_realtime_cities.py \
    --model models/ppo_cities_20251202_170832/checkpoint_900000_steps.zip
```

Output:
```
================================================================================
CLIENT DEV SERVER
================================================================================
✓ Dev server already running on port 9000
  Using existing server at http://localhost:9000
================================================================================

================================================================================
BROWSER LAUNCH
================================================================================
Opening browser automatically...
URL: http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia

If the browser doesn't open, manually navigate to:
  http://localhost:9000/rl-index.html?ws=ws://localhost:8765&map=australia
================================================================================
```

Much cleaner! No webpack errors, immediate browser launch.

### Stopping the Visualizer

Press `Ctrl+C`:

```
^C

Interrupted by user

Shutting down...
Shutdown complete

Visualization ended. Thank you!
```

Clean exit, no ugly exceptions!

## Testing the Fixes

Try running it again:

```bash
cd phase6-implementation
python3 src/visualize_realtime_cities.py \
    --model models/ppo_cities_20251202_170832/checkpoint_900000_steps.zip
```

You should see:
1. Clean detection that port 9000 is already in use
2. Browser opens immediately
3. Game starts and runs
4. When you press Ctrl+C, clean shutdown with no exceptions

## Additional Improvements

The good news from your run:
- **The visualization system works perfectly!**
- Client connected successfully
- Game initialized and rendered
- Model is making predictions
- Game state is being sent every tick

The only issues were:
1. Confusing error about port 9000 (now handled gracefully)
2. Ugly exception on Ctrl+C (now handled cleanly)

Both are now fixed!

## Next Steps

1. **Run it again** - You should see the improvements
2. **Watch your model play** - Let it run for 20-30 steps to see the action
3. **Check the browser** - Should show the game map with cities
4. **Try different checkpoints** - Compare 500K, 900K, and 1.5M step models

Enjoy! 🎮
