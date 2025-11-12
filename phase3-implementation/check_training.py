"""
Quick script to check training run metrics
"""
import os
import sys
from pathlib import Path

try:
    from tensorboard.backend.event_processing import event_accumulator
    HAS_TB = True
except ImportError:
    HAS_TB = False
    print("⚠️  TensorBoard not available - install with: pip install tensorboard")

def check_training_run(run_dir: str):
    """Analyze a training run"""
    run_path = Path(run_dir)

    print("=" * 80)
    print(f"TRAINING RUN ANALYSIS: {run_path.name}")
    print("=" * 80)

    # Check checkpoints
    checkpoint_dir = run_path / "checkpoints"
    if checkpoint_dir.exists():
        checkpoints = list(checkpoint_dir.glob("**/*.zip"))
        print(f"\n📁 Checkpoints: {len(checkpoints)} found")
        for cp in checkpoints:
            size_mb = cp.stat().st_size / (1024 * 1024)
            print(f"  - {cp.name}: {size_mb:.1f} MB")

    # Check logs
    log_dir = run_path / "logs"
    if log_dir.exists():
        print(f"\n📊 TensorBoard Logs:")
        event_files = list(log_dir.glob("**/events.out.tfevents.*"))

        if not event_files:
            print("  No TensorBoard event files found")
        else:
            for event_file in event_files:
                size_kb = event_file.stat().st_size / 1024
                print(f"  - {event_file.parent.name}: {size_kb:.1f} KB")

                if HAS_TB:
                    try:
                        # Load TensorBoard events
                        ea = event_accumulator.EventAccumulator(str(event_file.parent))
                        ea.Reload()

                        # Get available scalars
                        scalars = ea.Tags()['scalars']
                        print(f"    Available metrics: {len(scalars)}")

                        # Extract key metrics
                        key_metrics = [
                            'rollout/ep_rew_mean',
                            'rollout/ep_len_mean',
                            'train/value_loss',
                            'train/policy_loss',
                            'time/fps'
                        ]

                        print("\n    Latest values:")
                        for metric in key_metrics:
                            if metric in scalars:
                                events = ea.Scalars(metric)
                                if events:
                                    latest = events[-1]
                                    print(f"      {metric}: {latest.value:.4f} (step {latest.step})")

                        # Show training progress
                        if 'time/total_timesteps' in scalars:
                            timesteps = ea.Scalars('time/total_timesteps')
                            if timesteps:
                                total = timesteps[-1].value
                                print(f"\n    Total timesteps completed: {int(total):,}")

                    except Exception as e:
                        print(f"    Error reading TensorBoard data: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_training.py <run_dir>")
        print("Example: python check_training.py runs/run_20251101_194915")
        sys.exit(1)

    check_training_run(sys.argv[1])
