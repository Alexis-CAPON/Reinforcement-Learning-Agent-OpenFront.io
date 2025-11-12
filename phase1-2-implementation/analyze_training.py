"""
Analyze training results from the latest run
"""
import numpy as np
import json
import os
from pathlib import Path

# Find latest run
runs_dir = Path('runs')
latest_run = sorted(runs_dir.glob('run_*'))[-1]

print("=" * 80)
print(f"TRAINING ANALYSIS: {latest_run.name}")
print("=" * 80)

# Load config
with open(latest_run / 'config.json', 'r') as f:
    config = json.load(f)

print("\n[CONFIGURATION]")
print(f"  Total timesteps: {config['training']['total_timesteps']:,}")
print(f"  Learning rate: {config['training']['learning_rate']}")
print(f"  Batch size: {config['training']['batch_size']}")
print(f"  Map: {config['game']['map_name']} ({config['game']['map_size'][0]}x{config['game']['map_size'][1]})")
print(f"  Difficulty: {config['game']['opponent_difficulty']}")
print(f"  Players: {config['game']['num_players']}")

# Load evaluation results
eval_file = latest_run / 'logs' / 'evaluations.npz'
if eval_file.exists():
    data = np.load(eval_file)

    timesteps = data['timesteps']
    results = data['results']  # Shape: (n_evals, n_episodes)
    ep_lengths = data['ep_lengths']

    print(f"\n[EVALUATION RESULTS]")
    print(f"  Total evaluations: {len(timesteps)}")
    print(f"  Episodes per eval: {results.shape[1]}")

    print("\n[PERFORMANCE OVER TIME]")
    print(f"{'Timestep':<12} {'Mean Reward':<15} {'Std Reward':<15} {'Mean Length':<15} {'Win Rate':<12}")
    print("-" * 80)

    for i, ts in enumerate(timesteps):
        mean_reward = results[i].mean()
        std_reward = results[i].std()
        mean_length = ep_lengths[i].mean()

        # Estimate win rate based on reward (win bonus = 10000)
        # If reward > 5000, likely won
        wins = np.sum(results[i] > 5000)
        win_rate = (wins / len(results[i])) * 100

        print(f"{ts:<12,} {mean_reward:<15.1f} {std_reward:<15.1f} {mean_length:<15.1f} {win_rate:<12.1f}%")

    print("\n[FINAL PERFORMANCE SUMMARY]")
    final_mean = results[-1].mean()
    final_std = results[-1].std()
    final_length = ep_lengths[-1].mean()
    final_wins = np.sum(results[-1] > 5000)
    final_win_rate = (final_wins / len(results[-1])) * 100

    print(f"  Final mean reward: {final_mean:.1f} ± {final_std:.1f}")
    print(f"  Final mean length: {final_length:.1f} steps")
    print(f"  Final win rate: {final_win_rate:.1f}% ({final_wins}/{len(results[-1])} episodes)")

    # Learning progress
    initial_mean = results[0].mean()
    improvement = final_mean - initial_mean
    improvement_pct = (improvement / abs(initial_mean)) * 100 if initial_mean != 0 else 0

    print(f"\n[LEARNING PROGRESS]")
    print(f"  Initial mean reward: {initial_mean:.1f}")
    print(f"  Final mean reward: {final_mean:.1f}")
    print(f"  Improvement: {improvement:+.1f} ({improvement_pct:+.1f}%)")

    # Check if Phase 1 target achieved
    print(f"\n[PHASE 1 TARGET]")
    print(f"  Target: 40-50% win rate vs Easy AI")
    if final_win_rate >= 40:
        print(f"  Status: ✅ TARGET ACHIEVED! ({final_win_rate:.1f}%)")
    elif final_win_rate >= 20:
        print(f"  Status: ⚠️  PARTIAL PROGRESS ({final_win_rate:.1f}%) - needs more training")
    else:
        print(f"  Status: ❌ NOT ACHIEVED ({final_win_rate:.1f}%) - needs investigation")

    # Detailed episode analysis
    print(f"\n[FINAL EVALUATION EPISODES]")
    for i, (reward, length) in enumerate(zip(results[-1], ep_lengths[-1])):
        won = "✅ WIN" if reward > 5000 else "❌ LOSS"
        print(f"  Episode {i+1:2d}: reward={reward:8.1f}, length={length:4.0f} steps - {won}")

else:
    print("\n❌ No evaluation results found!")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if eval_file.exists():
    if final_win_rate >= 40:
        print("✅ Phase 1 complete! Ready for Phase 2 (extended training to 500k steps)")
    elif final_win_rate >= 20:
        print("⚠️  Continue training or adjust hyperparameters")
    else:
        print("❌ Check for issues:")
        print("   - Review TensorBoard (value_loss should be decreasing)")
        print("   - Verify reward structure is appropriate")
        print("   - Consider adjusting learning rate or exploration")

print("\nView detailed metrics with TensorBoard:")
print(f"  tensorboard --logdir={latest_run}/tensorboard")
print("=" * 80)
