"""
Debug script to check if actions are actually being executed
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from visualize_game import VisualGameWrapper

def test_visual_game():
    """Test if visual game bridge works correctly"""

    print("=" * 80)
    print("DEBUGGING VISUAL GAME BRIDGE")
    print("=" * 80)

    # Create wrapper
    print("\n1. Creating game...")
    game = VisualGameWrapper(num_bots=5, map_name='plains')

    # Reset
    print("2. Resetting game...")
    response = game.reset()
    print(f"   Initial state received: {response.get('success', False)}")

    # Get initial state
    print("\n3. Getting initial visual state...")
    state_response = game.get_visual_state()
    state = state_response['state']

    print(f"   Initial tiles: {state['rl_player']['tiles_owned']}")
    print(f"   Initial troops: {state['rl_player']['troops']}")
    print(f"   Initial territory: {state['rl_player']['territory_pct']*100:.1f}%")
    print(f"   Map size: {state['map_width']}x{state['map_height']}")

    # Try some actions
    print("\n4. Testing actions...")

    for i in range(10):
        # Try attacking North with 50% troops
        direction = 'N' if i % 2 == 0 else 'E'
        intensity = 0.5
        build = False

        print(f"\n   Step {i+1}: Action = {direction} @ {intensity*100:.0f}%")

        # Execute action
        game.attack_direction(direction, intensity, build)

        # Tick game
        game.tick()

        # Get state after
        state_response = game.get_visual_state()
        state_after = state_response['state']

        tiles_change = state_after['rl_player']['tiles_owned'] - state['rl_player']['tiles_owned']
        troops_change = state_after['rl_player']['troops'] - state['rl_player']['troops']

        print(f"      → Tiles: {state_after['rl_player']['tiles_owned']} (change: {tiles_change:+d})")
        print(f"      → Troops: {state_after['rl_player']['troops']:.0f} (change: {troops_change:+.0f})")
        print(f"      → Territory: {state_after['rl_player']['territory_pct']*100:.1f}%")
        print(f"      → Rank: {state_after['rl_player']['rank']}/{len(state_after['players'])}")

        if tiles_change != 0:
            print(f"      ✅ TERRITORY CHANGED!")
        elif troops_change > 0:
            print(f"      ⚠️ Troops growing but no territory gain")
        elif troops_change < 0:
            print(f"      ⚠️ Lost troops but no territory gain (attack failed?)")
        else:
            print(f"      ❌ Nothing changed")

        state = state_after

    # Clean up
    print("\n5. Cleaning up...")
    game.close()

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_visual_game()
