#!/bin/bash
# Training Monitor Script for Mac
# Usage: ./monitor_training_mac.sh

echo "======================================================================"
echo "Phase 6 Training Monitor (Mac)"
echo "======================================================================"
echo ""

# Check for training processes
echo "[1] Training Processes:"
TRAIN_COUNT=$(ps aux | grep -E "train_cities\.py|train_full_game\.py" | grep -v grep | wc -l | tr -d ' ')
if [ "$TRAIN_COUNT" -eq 0 ]; then
    echo "  ✗ No training running"
else
    echo "  ✓ Training running ($TRAIN_COUNT process(es))"
    ps aux | grep -E "train_cities\.py|train_full_game\.py" | grep -v grep | awk '{print "    PID:", $2, " CPU:", $3"% ", "MEM:", $4"% ", "TIME:", $10}'
fi

echo ""

# Check for game bridge processes
echo "[2] Game Bridge Processes:"
BRIDGE_COUNT=$(ps aux | grep -E "tsx.*game_bridge|npx tsx" | grep -v grep | wc -l | tr -d ' ')

# Try to detect expected bridges from training command
if [ "$TRAIN_COUNT" -gt 0 ]; then
    EXPECTED_BRIDGES=$(ps aux | grep -E "train_cities\.py.*--n-envs" | grep -v grep | sed -n 's/.*--n-envs \([0-9]*\).*/\1/p' | head -1)
    if [ -z "$EXPECTED_BRIDGES" ]; then
        EXPECTED_BRIDGES=8  # Default if can't detect
    fi
else
    EXPECTED_BRIDGES=8  # Assume default
fi

if [ "$BRIDGE_COUNT" -eq 0 ]; then
    if [ "$TRAIN_COUNT" -eq 0 ]; then
        echo "  ✓ No orphaned bridges (no training running)"
    else
        echo "  ⚠ Warning: Training running but no bridges found"
    fi
elif [ "$BRIDGE_COUNT" -le $((EXPECTED_BRIDGES + 2)) ]; then
    echo "  ✓ Normal: $BRIDGE_COUNT bridge processes (expected: ~$EXPECTED_BRIDGES)"
elif [ "$BRIDGE_COUNT" -le $((EXPECTED_BRIDGES * 2)) ]; then
    echo "  ⚠ Warning: $BRIDGE_COUNT bridge processes (expected: ~$EXPECTED_BRIDGES)"
    echo "    Some orphaned processes may exist. Monitor closely."
else
    echo "  ✗ ALERT: $BRIDGE_COUNT bridge processes! Memory leak detected!"
    echo "    Expected: ~$EXPECTED_BRIDGES (based on n-envs)"
    echo "    Run: pkill -9 -f 'tsx.*game_bridge' to clean up"
    echo "    Then restart training"
fi

# Show process details if there are too many
if [ "$BRIDGE_COUNT" -gt $((EXPECTED_BRIDGES * 2)) ]; then
    echo ""
    echo "  Game bridge process details:"
    ps aux | grep -E "tsx.*game_bridge|npx tsx" | grep -v grep | awk '{print "    PID:", $2, " CPU:", $3"% ", "MEM:", $4"%"}'
fi

echo ""

# Check system memory
echo "[3] System Memory:"
if command -v vm_stat &> /dev/null; then
    # Mac memory info
    VM_STAT=$(vm_stat)

    # Parse memory stats (pages are 4096 bytes on Mac)
    PAGE_SIZE=4096
    PAGES_FREE=$(echo "$VM_STAT" | grep "Pages free" | awk '{print $3}' | tr -d '.')
    PAGES_ACTIVE=$(echo "$VM_STAT" | grep "Pages active" | awk '{print $3}' | tr -d '.')
    PAGES_INACTIVE=$(echo "$VM_STAT" | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
    PAGES_WIRED=$(echo "$VM_STAT" | grep "Pages wired down" | awk '{print $4}' | tr -d '.')

    MEM_FREE_GB=$(echo "scale=2; $PAGES_FREE * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    MEM_USED_GB=$(echo "scale=2; ($PAGES_ACTIVE + $PAGES_WIRED) * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)

    echo "  Free: ${MEM_FREE_GB} GB"
    echo "  Active/Wired: ${MEM_USED_GB} GB"

    # Check if memory is getting tight
    if (( $(echo "$MEM_FREE_GB < 2.0" | bc -l) )); then
        echo "  ⚠ Warning: Low free memory! Consider reducing n-envs or restarting"
    fi
fi

echo ""

# Check CPU usage
echo "[4] CPU Usage:"
CPU_USAGE=$(ps aux | grep -E "train_cities\.py|tsx.*game_bridge" | grep -v grep | awk '{sum+=$3} END {print sum}')
if [ -n "$CPU_USAGE" ]; then
    echo "  Training + Bridges: ${CPU_USAGE}% CPU"

    # Get total CPU count
    CPU_COUNT=$(sysctl -n hw.ncpu)
    echo "  Available CPUs: $CPU_COUNT"

    # Warn if using too much CPU
    CPU_THRESHOLD=$((CPU_COUNT * 100))
    if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD * 0.9" | bc -l) )); then
        echo "  ⚠ Warning: High CPU usage (>90% of available)"
    fi
else
    echo "  No training processes consuming CPU"
fi

echo ""

# Check training logs (if they exist)
echo "[5] Latest Training Logs:"
if [ -d "logs" ]; then
    LATEST_LOG=$(find logs -name "events.out.tfevents.*" -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        LOG_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LATEST_LOG" 2>/dev/null)
        echo "  Last update: $LOG_TIME"

        # Check if log is recent (within last 5 minutes)
        if [ -n "$LOG_TIME" ]; then
            LOG_AGE=$(( $(date +%s) - $(stat -f "%m" "$LATEST_LOG" 2>/dev/null || echo 0) ))
            if [ "$LOG_AGE" -gt 300 ]; then
                MINUTES_AGO=$((LOG_AGE / 60))
                echo "  ⚠ Warning: Last update was $MINUTES_AGO minutes ago. Training may be stuck."
            fi
        fi
    else
        echo "  No TensorBoard logs found"
    fi
else
    echo "  No logs directory"
fi

echo ""

# Recommendations
echo "[6] Recommendations:"
if [ "$BRIDGE_COUNT" -gt $((EXPECTED_BRIDGES * 2)) ]; then
    echo "  ⚠ URGENT: Clean up game bridges: pkill -9 -f 'tsx.*game_bridge'"
    echo "            Then restart training: ./train_cities_mac.sh"
fi
if [ "$TRAIN_COUNT" -eq 0 ]; then
    echo "  → Start training with: ./train_cities_mac.sh"
fi
if [ "$TRAIN_COUNT" -gt 1 ]; then
    echo "  ⚠ Multiple training processes detected - may want to kill extras"
fi
if [ -n "$CPU_USAGE" ] && (( $(echo "$CPU_USAGE < 50" | bc -l) )); then
    echo "  ℹ Low CPU usage - training may be I/O bound or waiting"
fi

echo ""
echo "======================================================================"
echo "💡 Monitoring Tips:"
echo "  - Check occasionally (every 30-60 minutes)"
echo "  - Phase 3 ran successfully with 10 envs"
echo "  - Only restart if bridges >2x expected or memory critical"
echo "======================================================================"
