"""
Detailed training analysis with trend visualization
"""
import os
import sys
from pathlib import Path

try:
    from tensorboard.backend.event_processing import event_accumulator
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("⚠️  Install tensorboard and matplotlib for full analysis:")
    print("   pip install tensorboard matplotlib")


def analyze_training(run_dir: str, output_dir: str = None):
    """Detailed training analysis"""
    run_path = Path(run_dir)

    if output_dir is None:
        output_dir = run_path / "analysis"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 80)
    print(f"DETAILED TRAINING ANALYSIS: {run_path.name}")
    print("=" * 80)

    # Find event files
    log_dir = run_path / "logs"
    event_files = list(log_dir.glob("**/events.out.tfevents.*"))

    if not event_files:
        print("❌ No TensorBoard logs found!")
        return

    if not HAS_PLOTTING:
        print("⚠️  Plotting unavailable - showing text summary only")
        return

    # Load events
    event_file = event_files[0]
    ea = event_accumulator.EventAccumulator(str(event_file.parent))
    ea.Reload()

    scalars = ea.Tags()['scalars']
    print(f"\n📊 Found {len(scalars)} metrics")

    # Extract time series data
    metrics = {}
    for metric in scalars:
        events = ea.Scalars(metric)
        metrics[metric] = {
            'steps': [e.step for e in events],
            'values': [e.value for e in events],
            'times': [e.wall_time for e in events]
        }

    # Key metrics to analyze
    key_metrics = [
        ('rollout/ep_rew_mean', 'Episode Reward', 'Reward'),
        ('rollout/ep_len_mean', 'Episode Length', 'Steps'),
        ('train/value_loss', 'Value Loss', 'Loss'),
        ('train/policy_loss', 'Policy Loss', 'Loss'),
        ('train/entropy_loss', 'Entropy Loss', 'Loss'),
        ('time/fps', 'Training Speed', 'FPS'),
    ]

    # Create plots
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle(f'Training Analysis: {run_path.name}', fontsize=16, fontweight='bold')

    for idx, (metric_key, title, ylabel) in enumerate(key_metrics):
        if idx >= len(axes.flat):
            break

        ax = axes.flat[idx]

        if metric_key in metrics:
            data = metrics[metric_key]
            steps = data['steps']
            values = data['values']

            # Plot
            ax.plot(steps, values, linewidth=2, alpha=0.7)
            ax.set_xlabel('Timesteps')
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.grid(True, alpha=0.3)

            # Add statistics
            if len(values) > 0:
                latest = values[-1]
                mean = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)

                stats_text = f'Latest: {latest:.2f}\nMean: {mean:.2f}\nMin: {min_val:.2f}\nMax: {max_val:.2f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                       verticalalignment='top', fontsize=8,
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

                # Trend indicator
                if len(values) >= 2:
                    trend = "↗️" if values[-1] > values[0] else "↘️" if values[-1] < values[0] else "➡️"
                    ax.set_title(f'{title} {trend}')
        else:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)

    plt.tight_layout()

    # Save plot
    plot_path = output_dir / "training_analysis.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n📈 Saved training plots to: {plot_path}")

    # Text summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if 'rollout/ep_rew_mean' in metrics:
        rewards = metrics['rollout/ep_rew_mean']['values']
        if len(rewards) >= 2:
            print(f"\n📊 Episode Rewards:")
            print(f"   Initial: {rewards[0]:.2f}")
            print(f"   Final:   {rewards[-1]:.2f}")
            print(f"   Change:  {rewards[-1] - rewards[0]:+.2f}")
            print(f"   Mean:    {sum(rewards)/len(rewards):.2f}")

            # Learning progress
            if len(rewards) >= 10:
                first_10pct = sum(rewards[:len(rewards)//10]) / (len(rewards)//10)
                last_10pct = sum(rewards[-len(rewards)//10:]) / (len(rewards)//10)
                improvement = ((last_10pct - first_10pct) / abs(first_10pct)) * 100

                print(f"   First 10%: {first_10pct:.2f}")
                print(f"   Last 10%:  {last_10pct:.2f}")
                print(f"   Improvement: {improvement:+.1f}%")

                if improvement > 10:
                    print(f"   ✅ Agent is learning! ({improvement:.0f}% improvement)")
                elif improvement > 0:
                    print(f"   ⚠️  Slow learning ({improvement:.0f}% improvement)")
                else:
                    print(f"   ❌ No learning detected ({improvement:.0f}% change)")

    if 'rollout/ep_len_mean' in metrics:
        lengths = metrics['rollout/ep_len_mean']['values']
        if len(lengths) >= 2:
            print(f"\n⏱️  Episode Lengths:")
            print(f"   Initial: {lengths[0]:.0f} steps")
            print(f"   Final:   {lengths[-1]:.0f} steps")
            print(f"   Change:  {lengths[-1] - lengths[0]:+.0f} steps")

            if lengths[-1] > lengths[0] * 1.2:
                print(f"   ✅ Agent surviving longer!")
            elif lengths[-1] > lengths[0]:
                print(f"   ⚠️  Slightly longer survival")
            else:
                print(f"   ❌ Not improving survival time")

    if 'train/value_loss' in metrics:
        v_loss = metrics['train/value_loss']['values']
        if len(v_loss) >= 2:
            print(f"\n📉 Value Loss:")
            print(f"   Initial: {v_loss[0]:.2f}")
            print(f"   Final:   {v_loss[-1]:.2f}")
            print(f"   Change:  {v_loss[-1] - v_loss[0]:+.2f}")

            if v_loss[-1] < v_loss[0]:
                print(f"   ✅ Decreasing (good!)")
            else:
                print(f"   ⚠️  Increasing (may need tuning)")

    if 'time/fps' in metrics:
        fps = metrics['time/fps']['values']
        if fps:
            avg_fps = sum(fps) / len(fps)
            print(f"\n⚡ Training Speed:")
            print(f"   Average FPS: {avg_fps:.0f}")
            print(f"   Latest FPS:  {fps[-1]:.0f}")

    if 'time/total_timesteps' in metrics:
        total = int(metrics['time/total_timesteps']['values'][-1])
        print(f"\n🎯 Training Progress:")
        print(f"   Total timesteps: {total:,}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_training.py <run_dir> [output_dir]")
        print("Example: python analyze_training.py runs/run_20251101_194915")
        sys.exit(1)

    run_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    analyze_training(run_dir, output_dir)
