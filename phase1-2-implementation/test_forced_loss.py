"""
Test forced loss scenario - agent takes aggressive random actions
to verify loss detection when agent gets eliminated
"""
import sys
sys.path.insert(0, 'rl_env')

from openfrontio_env import OpenFrontIOEnv
import numpy as np

print("Testing forced loss scenario (aggressive random actions)...")
print("=" * 60)

env = OpenFrontIOEnv()
obs, info = env.reset()

print(f"\nInitial state:")
print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
print(f"  AI Bots  - Tiles: {info['enemy_tiles']}")

# Run aggressive random actions to provoke combat and potential loss
print(f"\nRunning aggressive random actions until agent loses or 2000 steps...")
print(f"Agent will attack randomly to create combat situations.\n")

max_steps = 2000
tiles_history = [info['tiles']]

for i in range(max_steps):
    # Sample random valid action (preferring attacks over IDLE)
    valid_actions = np.where(obs['action_mask'] == 1)[0]

    # Prefer attack actions (1-8) over IDLE (0)
    attack_actions = [a for a in valid_actions if a > 0]
    if len(attack_actions) > 0:
        action = np.random.choice(attack_actions)
    else:
        action = 0  # IDLE if no attacks available

    obs, reward, terminated, truncated, info = env.step(action)
    tiles_history.append(info['tiles'])

    # Print status when tiles change significantly or every 100 steps
    if (i > 0 and abs(info['tiles'] - tiles_history[-2]) > 5) or i % 100 == 99 or info['tiles'] <= 10 or terminated:
        print(f"Step {i+1}:")
        print(f"  RL Agent - Tiles: {info['tiles']}, Troops: {info['troops']}")
        print(f"  AI Bots  - Tiles: {info['enemy_tiles']}")
        print(f"  Action taken: {action}, Reward: {reward:.1f}")

        if info['tiles'] == 0:
            print(f"  ⚠️  Agent has 0 tiles - should trigger loss!")

        if info['tiles'] <= 10 and info['tiles'] > 0:
            print(f"  ⚠️  Agent down to {info['tiles']} tiles - close to elimination!")

    if terminated or truncated:
        print(f"\n{'='*60}")
        print(f"Episode ended at step {i+1}!")
        print(f"{'='*60}")

        # Check the episode info
        if 'episode' in info:
            episode_info = info['episode']
            print(f"\nEpisode Summary:")
            print(f"  Final tiles: {episode_info['tiles_final']}")
            print(f"  Won: {episode_info['won']}")
            print(f"  Total reward: {episode_info['r']:.1f}")
            print(f"  Episode length: {episode_info['l']}")

        print(f"\nFinal state:")
        print(f"  Tiles: {info['tiles']}")
        print(f"  Terminated: {terminated}")
        print(f"  Truncated: {truncated}")

        # Verify loss detection worked
        if info['tiles'] == 0:
            if terminated:
                print(f"\n✅ SUCCESS! Loss detected properly:")
                print(f"   - Agent has 0 tiles")
                print(f"   - Episode terminated immediately")
                print(f"   - Loss penalty (-10,000) should have been applied")
            else:
                print(f"\n❌ FAILURE! Loss detection NOT working:")
                print(f"   - Agent has 0 tiles")
                print(f"   - Episode did NOT terminate (terminated={terminated})")
                print(f"   - This is the bug!")
        elif terminated and info['tiles'] > 0:
            print(f"\n✅ Episode terminated with tiles remaining")
            print(f"   - Agent either won or other condition met")

        # Show tile history
        print(f"\nTile history (last 20 steps):")
        print(f"  {tiles_history[-20:]}")

        break
else:
    print(f"\n{'='*60}")
    print(f"Reached {max_steps} steps without termination")
    print(f"Final tiles: {info['tiles']}")
    print(f"\nTile history (last 20 steps):")
    print(f"  {tiles_history[-20:]}")
    print(f"{'='*60}")

env.close()
print("\nTest complete!")
