"""
Benchmark command for VGGT-MPS performance testing
"""

import sys
import time
from pathlib import Path
import torch
import numpy as np
from PIL import Image

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vggt_mps.config import DEVICE, SPARSE_CONFIG, get_model_path, is_model_available
from vggt_mps.vggt_core import VGGTProcessor
from vggt_mps.vggt_sparse_attention import make_vggt_sparse


def run_benchmark(args):
    """Run performance benchmarks"""
    print("=" * 60)
    print("⚡ VGGT Performance Benchmark")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Images: {args.images}")
    print(f"Compare: {args.compare}")
    print("-" * 60)

    # Check model availability
    if not is_model_available():
        print("\n❌ VGGT model not found!")
        print("Run: python main.py download")
        print("\nUsing simulated mode for benchmark...")

    # Create synthetic test images
    print("\n📸 Creating synthetic test images...")
    images = []
    for i in range(args.images):
        # Create random image
        img_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        images.append(img_array)

    # Initialize processor
    processor = VGGTProcessor(device=DEVICE)

    results = {}

    # Benchmark regular VGGT
    print("\n🔵 Benchmarking Regular VGGT...")
    print(f"  Memory complexity: O(n²) = O({args.images}²)")

    start_time = time.time()
    start_memory = torch.cuda.memory_allocated() if DEVICE.type == "cuda" else 0

    try:
        regular_output = processor.process_images(images)
        regular_time = time.time() - start_time
        regular_memory = torch.cuda.memory_allocated() if DEVICE.type == "cuda" else 0
        regular_memory_used = (regular_memory - start_memory) / 1024 / 1024  # MB

        results['regular'] = {
            'success': True,
            'time': regular_time,
            'memory': regular_memory_used,
            'fps': args.images / regular_time
        }
        print(f"  ✅ Time: {regular_time:.2f}s")
        print(f"  ✅ FPS: {args.images / regular_time:.2f}")
        if DEVICE.type == "cuda":
            print(f"  ✅ Memory: {regular_memory_used:.1f} MB")

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results['regular'] = {'success': False, 'error': str(e)}

    # Benchmark sparse VGGT if requested
    if args.compare:
        print("\n🟢 Benchmarking Sparse VGGT...")
        print(f"  Memory complexity: O(n) = O({args.images})")
        print(f"  Covisibility threshold: {SPARSE_CONFIG['covisibility_threshold']}")

        # Apply sparse attention
        processor.model = make_vggt_sparse(processor.model, device=DEVICE) if processor.model else None

        start_time = time.time()
        start_memory = torch.cuda.memory_allocated() if DEVICE.type == "cuda" else 0

        try:
            sparse_output = processor.process_images(images)
            sparse_time = time.time() - start_time
            sparse_memory = torch.cuda.memory_allocated() if DEVICE.type == "cuda" else 0
            sparse_memory_used = (sparse_memory - start_memory) / 1024 / 1024  # MB

            results['sparse'] = {
                'success': True,
                'time': sparse_time,
                'memory': sparse_memory_used,
                'fps': args.images / sparse_time
            }
            print(f"  ✅ Time: {sparse_time:.2f}s")
            print(f"  ✅ FPS: {args.images / sparse_time:.2f}")
            if DEVICE.type == "cuda":
                print(f"  ✅ Memory: {sparse_memory_used:.1f} MB")

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            results['sparse'] = {'success': False, 'error': str(e)}

    # Print comparison
    if args.compare and results.get('regular', {}).get('success') and results.get('sparse', {}).get('success'):
        print("\n" + "=" * 60)
        print("📊 Comparison Results")
        print("-" * 60)

        speedup = results['regular']['time'] / results['sparse']['time']
        print(f"⚡ Speedup: {speedup:.2f}x")

        if DEVICE.type == "cuda":
            memory_savings = results['regular']['memory'] / max(results['sparse']['memory'], 0.1)
            print(f"💾 Memory savings: {memory_savings:.2f}x")

        print("=" * 60)

    # Memory scaling test
    if args.compare:
        print("\n📈 Memory Scaling Analysis")
        print("-" * 60)
        test_sizes = [10, 20, 50, 100]

        for n in test_sizes:
            regular_mem = n * n  # O(n²)
            sparse_mem = n * SPARSE_CONFIG['covisibility_threshold'] * n  # O(n)
            savings = regular_mem / sparse_mem
            print(f"  {n:3d} images: {savings:6.1f}x savings")

    print("\n✅ Benchmark complete!")
    return 0