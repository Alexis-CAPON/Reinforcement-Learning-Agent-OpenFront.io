#!/usr/bin/env python3
"""
Quick test to verify cluster detection is working
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from game_wrapper import GameWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_clusters():
    """Test that clusters are detected after game initialization"""
    logger.info("Creating game wrapper...")
    wrapper = GameWrapper(map_name='australia_256x256', num_players=11)

    logger.info("Starting new game...")
    wrapper.start_new_game()

    logger.info("Getting initial state...")
    state = wrapper.get_state()

    logger.info(f"RL Agent stats:")
    logger.info(f"  Tiles owned: {state.tiles_owned}")
    logger.info(f"  Population: {state.population}")
    logger.info(f"  Number of clusters: {len(state.clusters)}")

    if len(state.clusters) == 0:
        logger.error("❌ FAIL: No clusters detected!")
        wrapper.close()
        return False

    logger.info("✅ PASS: Clusters detected!")
    for i, cluster in enumerate(state.clusters):
        logger.info(f"  Cluster {i}: {len(cluster['tiles'])} tiles, {cluster['troop_count']} troops")

    # Test a few ticks
    logger.info("\nRunning 5 game ticks...")
    for i in range(5):
        wrapper.update()
        state = wrapper.get_state()
        logger.info(f"  Tick {state.tick}: {state.tiles_owned} tiles, {len(state.clusters)} cluster(s)")

        if len(state.clusters) == 0 and state.tiles_owned > 0:
            logger.error(f"❌ FAIL: Have tiles but no clusters at tick {state.tick}!")
            wrapper.close()
            return False

    logger.info("\n✅ All tests passed!")
    wrapper.close()
    return True

if __name__ == "__main__":
    success = test_clusters()
    sys.exit(0 if success else 1)
