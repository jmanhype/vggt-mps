#!/usr/bin/env python3
"""
Test sparse attention VGGT with real images
Compare memory usage and results between regular and sparse
"""

import torch
import sys
from pathlib import Path
import time
import tracemalloc

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "repo" / "vggt"))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
from vggt_sparse_attention import make_vggt_sparse

def test_vggt_mode(images, model, mode_name):
    """Test VGGT with memory tracking"""

    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"Testing {mode_name}")
    print(f"{'='*60}")

    # Run inference
    with torch.no_grad():
        predictions = model(images)

    # Get memory stats
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    elapsed = time.time() - start_time

    print(f"✅ Inference complete!")
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Peak memory: {peak / 1024 / 1024:.1f} MB")
    print(f"   Output shapes:")
    print(f"      - Depth: {predictions['depth'].shape}")
    print(f"      - Camera poses: {predictions['pose_enc'].shape}")

    return predictions, peak

def main():
    print("="*70)
    print("🧪 VGGT Sparse Attention Test with Real Images")
    print("="*70)

    # Setup
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    # Check for test images
    test_dir = Path(__file__).parent / "tmp" / "inputs"
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))

    if not image_files:
        print("❌ No test images found!")
        print("Creating test images...")
        from PIL import Image
        for i in range(10):  # Create 10 images for better testing
            img = Image.new('RGB', (640, 480),
                          color=(100 + i*15, 150 - i*5, 200 - i*10))
            img_path = test_dir / f"sparse_test_{i+1:03d}.jpg"
            img.save(img_path)
            image_files.append(img_path)

    # Use different numbers of images
    test_counts = [4, 8, 16]

    for num_images in test_counts:
        print(f"\n{'='*70}")
        print(f"📸 Testing with {num_images} images")
        print(f"{'='*70}")

        # Load images
        image_paths = [str(f) for f in image_files[:num_images]]
        print(f"Loading images: {[p.name for p in Path(image_paths[0]).parent.glob('*.jpg')][:num_images]}")

        images = load_and_preprocess_images(image_paths).to(device)
        print(f"Images shape: {images.shape}")

        # Test 1: Regular VGGT
        print("\n1️⃣ Regular VGGT (O(n²) attention)")
        model_regular = VGGT()

        # Try to load weights
        model_path = Path(__file__).parent / "repo" / "vggt" / "vggt_model.pt"
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=device, weights_only=True)
            model_regular.load_state_dict(checkpoint)

        model_regular = model_regular.to(device).eval()

        try:
            pred_regular, mem_regular = test_vggt_mode(images, model_regular, "Regular VGGT")
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"❌ OOM with regular attention!")
                mem_regular = float('inf')
                pred_regular = None
            else:
                raise

        # Test 2: Sparse VGGT
        print("\n2️⃣ Sparse VGGT (O(n) attention)")
        model_sparse = VGGT()

        if model_path.exists():
            model_sparse.load_state_dict(checkpoint)

        model_sparse = model_sparse.to(device).eval()

        # Convert to sparse
        model_sparse = make_vggt_sparse(model_sparse, device=str(device))

        try:
            pred_sparse, mem_sparse = test_vggt_mode(images, model_sparse, "Sparse VGGT")
        except Exception as e:
            print(f"❌ Error with sparse attention: {e}")
            import traceback
            traceback.print_exc()
            continue

        # Compare results
        print(f"\n📊 Comparison for {num_images} images:")
        print(f"{'='*50}")

        if mem_regular != float('inf'):
            savings = mem_regular / mem_sparse if mem_sparse > 0 else 1
            print(f"Memory savings: {savings:.1f}x")

            if pred_regular and pred_sparse:
                # Compare outputs
                depth_diff = (pred_regular['depth'] - pred_sparse['depth']).abs().mean()
                print(f"Depth difference: {depth_diff:.4f}")
        else:
            print("Regular VGGT: Out of Memory")
            print(f"Sparse VGGT: {mem_sparse / 1024 / 1024:.1f} MB")
            print("✅ Sparse attention enables processing!")

    print("\n" + "="*70)
    print("✨ Test Complete!")
    print("="*70)

if __name__ == "__main__":
    main()