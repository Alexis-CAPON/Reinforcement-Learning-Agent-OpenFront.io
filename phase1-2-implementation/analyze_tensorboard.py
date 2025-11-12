"""
Analyze TensorBoard event files to understand training dynamics
"""
import os
from pathlib import Path
from tensorboard.backend.event_processing import event_accumulator
import numpy as np

# Find latest run
runs_dir = Path('runs')
latest_run = sorted(runs_dir.glob('run_*'))[-1]

print("=" * 80)
print(f"TENSORBOARD ANALYSIS: {latest_run.name}")
print("=" * 80)

# Find tensorboard event file
tb_dir = latest_run / 'tensorboard'
event_files = list(tb_dir.rglob('events.out.tfevents.*'))

if not event_files:
    print("\n❌ No TensorBoard event files found!")
    exit(1)

# Load the first event file (there should only be one for PPO_1)
event_file = event_files[0]
print(f"\nLoading: {event_file.name}")

ea = event_accumulator.EventAccumulator(str(event_file))
ea.Reload()

# Get available tags
print(f"\nAvailable scalar tags:")
for tag in sorted(ea.Tags()['scalars']):
    print(f"  - {tag}")

# Analyze key metrics
print("\n" + "=" * 80)
print("KEY TRAINING METRICS")
print("=" * 80)

def print_metric(tag, description):
    if tag in ea.Tags()['scalars']:
        events = ea.Scalars(tag)
        values = [e.value for e in events]
        steps = [e.step for e in events]

        print(f"\n[{description}]")
        print(f"  Tag: {tag}")
        print(f"  Initial: {values[0]:.4f} (step {steps[0]})")
        print(f"  Final: {values[-1]:.4f} (step {steps[-1]})")
        print(f"  Min: {min(values):.4f}")
        print(f"  Max: {max(values):.4f}")
        print(f"  Trend: {values[-1] - values[0]:+.4f}")

        # Check if decreasing (good for losses)
        if "loss" in tag.lower():
            if values[-1] < values[0]:
                status = "✅ Decreasing (good)"
            else:
                status = "❌ Increasing (bad)"
        elif "reward" in tag.lower() or "ep_rew" in tag.lower():
            if values[-1] > values[0]:
                status = "✅ Increasing (good)"
            else:
                status = "❌ Not improving (bad)"
        else:
            status = ""

        if status:
            print(f"  Status: {status}")

        return values, steps
    else:
        print(f"\n[{description}]")
        print(f"  ❌ Metric not found: {tag}")
        return None, None

# Critical metrics
print_metric('rollout/ep_rew_mean', 'Episode Reward Mean')
print_metric('rollout/ep_len_mean', 'Episode Length Mean')
print_metric('train/value_loss', 'Value Loss')
print_metric('train/policy_gradient_loss', 'Policy Gradient Loss')
print_metric('train/entropy_loss', 'Entropy Loss')
print_metric('train/approx_kl', 'Approximate KL Divergence')
print_metric('train/clip_fraction', 'Clip Fraction')
print_metric('train/explained_variance', 'Explained Variance')
print_metric('train/learning_rate', 'Learning Rate')

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

# Check for common failure modes
if 'train/value_loss' in ea.Tags()['scalars']:
    value_loss_events = ea.Scalars('train/value_loss')
    value_losses = [e.value for e in value_loss_events]

    print("\n[Value Loss Analysis]")
    if value_losses[-1] > 10000:
        print("  ❌ CRITICAL: Value loss is EXTREMELY high (>10,000)")
        print("     This means the value function is completely failing to learn")
        print("     The agent cannot predict episode returns")
    elif value_losses[-1] > 1000:
        print("  ⚠️  WARNING: Value loss is very high (>1,000)")
        print("     Value function is struggling")
    else:
        print("  ✅ Value loss is reasonable")

if 'train/approx_kl' in ea.Tags()['scalars']:
    kl_events = ea.Scalars('train/approx_kl')
    kl_values = [e.value for e in kl_events]

    print("\n[KL Divergence Analysis]")
    if max(kl_values) > 0.05:
        print(f"  ⚠️  WARNING: KL divergence spiked above 0.05 (max={max(kl_values):.4f})")
        print("     Policy updates are too aggressive")
    else:
        print(f"  ✅ KL divergence stayed reasonable (max={max(kl_values):.4f})")

if 'train/explained_variance' in ea.Tags()['scalars']:
    expl_var_events = ea.Scalars('train/explained_variance')
    expl_var = [e.value for e in expl_var_events]

    print("\n[Explained Variance Analysis]")
    if expl_var[-1] < 0:
        print(f"  ❌ CRITICAL: Explained variance is NEGATIVE ({expl_var[-1]:.4f})")
        print("     Value function is worse than predicting zero!")
    elif expl_var[-1] < 0.3:
        print(f"  ⚠️  WARNING: Explained variance is low ({expl_var[-1]:.4f})")
        print("     Value function is not capturing episode returns well")
    else:
        print(f"  ✅ Explained variance is reasonable ({expl_var[-1]:.4f})")

if 'rollout/ep_rew_mean' in ea.Tags()['scalars']:
    reward_events = ea.Scalars('rollout/ep_rew_mean')
    rewards = [e.value for e in reward_events]

    print("\n[Reward Analysis]")
    if all(r < -10000 for r in rewards):
        print("  ❌ CRITICAL: Agent ALWAYS loses (all rewards < -10,000)")
        print("     The agent is not learning any useful behavior")
        print("     Win bonus: +10,000, Loss penalty: -10,000")
    elif max(rewards) > 5000:
        print(f"  ✅ Agent achieved some wins (max reward: {max(rewards):.1f})")
    else:
        print(f"  ⚠️  Agent never won but may be improving (max reward: {max(rewards):.1f})")

print("\n" + "=" * 80)
print("LIKELY ROOT CAUSES")
print("=" * 80)

# Based on the evaluation results showing constant losses
print("\n1. ❌ REWARD STRUCTURE ISSUE")
print("   - Agent loses EVERY episode (0% win rate)")
print("   - Mean reward ~-13,000 = -10,000 (loss) + ~-3,000 (time penalty)")
print("   - Episodes last ~2,500-3,500 steps × -1 per step = -2,500 to -3,500")
print("   - Total: -10,000 - 3,000 = -13,000 ✓ matches observed")
print()
print("   Problem: Rewards are MASSIVELY dominated by terminal outcomes")
print("   - Win bonus: +10,000 is only obtained at episode END")
print("   - All intermediate steps give tiny rewards (-1 per step, ±10 per tile)")
print("   - Agent gets almost NO intermediate feedback for 3,000+ steps!")

print("\n2. ❌ SPARSE REWARD PROBLEM")
print("   - Agent takes 3,000+ actions before getting meaningful reward")
print("   - This is EXTREMELY hard for PPO to learn from")
print("   - Credit assignment problem: which of 3,000 actions led to loss?")

print("\n3. ⚠️  OBSERVATION SPACE TOO SIMPLE")
print("   - Only 5 features: tiles, troops, gold, enemy_tiles, tick")
print("   - Agent has almost no spatial/tactical information")
print("   - Cannot distinguish between \"expand here\" vs \"expand there\"")

print("\n4. ⚠️  ACTION SPACE LIMITATIONS")
print("   - Can only attack 1 tile per step")
print("   - Takes 3,000+ steps per episode")
print("   - Game may require coordinated multi-tile strategy")

print("\n" + "=" * 80)
print("RECOMMENDED FIXES")
print("=" * 80)

print("\n[IMMEDIATE - Reward Shaping]")
print("  1. Add DENSE intermediate rewards:")
print("     - Reward for tile ownership at EVERY step (not just changes)")
print("     - Reward for troop accumulation")
print("     - Reward for territorial advantage (tiles_owned - enemy_tiles)")
print()
print("  2. Reduce terminal reward magnitude:")
print("     - Win bonus: 10,000 → 1,000")
print("     - Loss penalty: -10,000 → -1,000")
print("     - Makes intermediate rewards more impactful")
print()
print("  3. Increase per-tile rewards:")
print("     - Per tile gained: 10 → 50 or 100")
print("     - Per tile lost: -10 → -50 or -100")

print("\n[MEDIUM TERM - Environment]")
print("  1. Shorten episodes:")
print("     - Reduce max_steps from 5,000 to 1,000-2,000")
print("     - Faster feedback cycles")
print()
print("  2. Add more observation features:")
print("     - Border tiles count")
print("     - Number of cities")
print("     - Troops distribution")
print()
print("  3. Curriculum learning:")
print("     - Start with 2-player games (easier)")
print("     - Gradually increase to 6 players")

print("\n[LONG TERM - Architecture]")
print("  1. Improve action space (see previous critique)")
print("  2. Add spatial observations (convolutional network)")
print("  3. Use recurrent policy (LSTM) for temporal reasoning")

print("\n" + "=" * 80)
