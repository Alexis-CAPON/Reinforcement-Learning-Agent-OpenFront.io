"""
Check MPS (Metal Performance Shaders) availability and benchmark performance.

This script verifies that your M4 Max GPU is properly configured for PyTorch
and provides a simple benchmark.
"""

import torch
import time
import numpy as np

def check_mps():
    """Check if MPS is available and working"""
    print("=" * 60)
    print("MPS (Metal Performance Shaders) Status Check")
    print("=" * 60)
    print()

    # Check availability
    print("1. MPS Availability:")
    mps_available = torch.backends.mps.is_available()
    mps_built = torch.backends.mps.is_built()

    print(f"   MPS Available: {mps_available}")
    print(f"   MPS Built:     {mps_built}")

    if not mps_available:
        print("\n   ❌ MPS not available!")
        print("   Make sure you have:")
        print("   - macOS 12.3+")
        print("   - PyTorch 1.12+")
        print("   - Apple Silicon Mac (M1/M2/M3/M4)")
        return False

    print("   ✓ MPS is available!")
    print()

    # Get device info
    print("2. Device Information:")
    print(f"   PyTorch Version: {torch.__version__}")
    print(f"   Device: M4 Max (assumed)")
    print()

    # Test basic operations
    print("3. Testing MPS Operations:")
    try:
        device = torch.device("mps")
        x = torch.randn(100, 100).to(device)
        y = torch.randn(100, 100).to(device)
        z = torch.matmul(x, y)
        print("   ✓ Basic tensor operations work")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    print()

    # Benchmark
    print("4. Performance Benchmark:")
    benchmark_mps()

    print()
    print("=" * 60)
    print("MPS Check Complete!")
    print("=" * 60)
    print()
    print("You can now train with: python src/train.py --device mps")
    print()

    return True


def benchmark_mps():
    """Simple benchmark comparing CPU vs MPS performance"""

    # Test parameters
    size = (1024, 1024)
    iterations = 100

    print(f"   Running {iterations} iterations of matrix multiplication ({size[0]}×{size[1]})...")
    print()

    # CPU benchmark
    print("   CPU Benchmark:")
    x_cpu = torch.randn(size)
    y_cpu = torch.randn(size)

    start = time.time()
    for _ in range(iterations):
        z = torch.matmul(x_cpu, y_cpu)
    cpu_time = time.time() - start
    print(f"     Time: {cpu_time:.3f}s")
    print(f"     Throughput: {iterations/cpu_time:.1f} ops/sec")

    # MPS benchmark
    print()
    print("   MPS (GPU) Benchmark:")
    device = torch.device("mps")
    x_mps = torch.randn(size).to(device)
    y_mps = torch.randn(size).to(device)

    # Warmup
    for _ in range(10):
        z = torch.matmul(x_mps, y_mps)

    start = time.time()
    for _ in range(iterations):
        z = torch.matmul(x_mps, y_mps)
    torch.mps.synchronize()  # Wait for GPU to finish
    mps_time = time.time() - start
    print(f"     Time: {mps_time:.3f}s")
    print(f"     Throughput: {iterations/mps_time:.1f} ops/sec")

    # Speedup
    speedup = cpu_time / mps_time
    print()
    print(f"   Speedup: {speedup:.2f}× faster with MPS")

    if speedup > 1.5:
        print("   ✓ Good GPU acceleration!")
    elif speedup > 1.0:
        print("   ⚠ Moderate GPU acceleration")
    else:
        print("   ⚠ GPU slower than CPU (might be overhead for small operations)")


def test_model_forward():
    """Test CNN forward pass on MPS"""
    print()
    print("5. Testing CNN Model on MPS:")

    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from model import BattleRoyalePolicy

        device = torch.device("mps")
        model = BattleRoyalePolicy().to(device)

        # Create test input
        batch_size = 4
        test_obs = {
            'map': torch.randn(batch_size, 128, 128, 5).to(device),
            'global': torch.randn(batch_size, 16).to(device)
        }

        # Forward pass
        start = time.time()
        with torch.no_grad():
            action_logits, value = model(test_obs)
        torch.mps.synchronize()
        forward_time = (time.time() - start) * 1000  # Convert to ms

        print(f"   Forward pass time: {forward_time:.2f}ms")
        print(f"   Target: <10ms per decision")

        if forward_time < 10:
            print("   ✓ Excellent inference speed!")
        elif forward_time < 20:
            print("   ✓ Good inference speed")
        else:
            print("   ⚠ Inference slower than target")

        return True

    except Exception as e:
        print(f"   ⚠ Could not test model: {e}")
        return False


if __name__ == "__main__":
    success = check_mps()

    if success:
        test_model_forward()

        print()
        print("=" * 60)
        print("Recommendations for M4 Max Training:")
        print("=" * 60)
        print()
        print("1. Use MPS device:")
        print("   python src/train.py --device mps --n-envs 12")
        print()
        print("2. Increase parallel environments:")
        print("   M4 Max can handle 12-16 environments efficiently")
        print()
        print("3. Expected training time:")
        print("   - Phase 1 (100K steps): ~8-10 hours")
        print("   - Phase 2 (300K steps): ~1 day")
        print("   - Phase 3 (500K steps): ~1.5-2 days")
        print("   - Total: 2-3 days")
        print()
        print("4. Monitor with TensorBoard:")
        print("   tensorboard --logdir runs/")
        print()
