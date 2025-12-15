#!/bin/bash
# Training Monitor Script - Helps detect and prevent process buildup
# Usage: ./monitor_training.sh

echo "======================================================================"
echo "Phase 6 Training Monitor"
echo "======================================================================"
echo ""

# Check for training processes
echo "[1] Training Processes:"
TRAIN_COUNT=$(ps aux | grep -E "train_cities\.py|train_full_game\.py" | grep -v grep | wc -l)
if [ "$TRAIN_COUNT" -eq 0 ]; then
    echo "  ✗ No training running"
else
    echo "  ✓ Training running ($TRAIN_COUNT process(es))"
    ps aux | grep -E "train_cities\.py|train_full_game\.py" | grep -v grep | awk '{print "    PID:", $2, " CPU:", $3"% ", "MEM:", $4"% ", "TIME:", $10}'
fi

echo ""

# Check for game bridge processes
echo "[2] Game Bridge Processes:"
BRIDGE_COUNT=$(ps aux | grep -E "tsx.*game_bridge|npx tsx" | grep -v grep | wc -l)
if [ "$BRIDGE_COUNT" -eq 0 ]; then
    echo "  ✓ No orphaned bridges"
elif [ "$BRIDGE_COUNT" -eq 1 ]; then
    echo "  ✓ Normal: 1 bridge process"
elif [ "$BRIDGE_COUNT" -le 3 ]; then
    echo "  ⚠ Warning: $BRIDGE_COUNT bridge processes (should be 1)"
else
    echo "  ✗ ALERT: $BRIDGE_COUNT bridge processes! Memory leak detected!"
    echo "  Run: pkill -9 -f 'tsx.*game_bridge' to clean up"
fi

echo ""

# Check GPU usage (if on GPU server)
if command -v nvidia-smi &> /dev/null; then
    echo "[3] GPU Status:"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader | \
    while IFS=, read -r idx name mem_used mem_total util; do
        echo "  GPU $idx: $util utilization, $mem_used / $mem_total"
    done
    echo ""
fi

# Check training logs (if they exist)
echo "[4] Latest Training Logs:"
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/*/events.out.tfevents.* 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        LOG_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LATEST_LOG" 2>/dev/null || stat -c "%y" "$LATEST_LOG" 2>/dev/null | cut -d. -f1)
        echo "  Last update: $LOG_TIME"
    else
        echo "  No TensorBoard logs found"
    fi
else
    echo "  No logs directory"
fi

echo ""

# Recommendations
echo "[5] Recommendations:"
if [ "$BRIDGE_COUNT" -gt 3 ]; then
    echo "  ⚠ Clean up game bridges: pkill -9 -f 'tsx.*game_bridge'"
fi
if [ "$TRAIN_COUNT" -eq 0 ]; then
    echo "  → Start training with: bash train_cities_gpu.sh"
fi
if [ "$TRAIN_COUNT" -gt 1 ]; then
    echo "  ⚠ Multiple training processes detected - may want to kill extras"
fi

echo ""
echo "======================================================================"
echo "Run this script periodically to monitor training health"
echo "======================================================================"
