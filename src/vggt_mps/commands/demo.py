"""
Demo command for VGGT-MPS
"""

import sys
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vggt_mps.config import (
    DEVICE, DATA_DIR, OUTPUT_DIR, TEST_DATA,
    CAMERA_CONFIG, PROCESSING_CONFIG, get_model_path, is_model_available
)
from vggt_mps.vggt_core import VGGTProcessor
from vggt_mps.visualization import create_visualizations


def run_demo(args) -> None:
    """
    Run demo with sample images.

    Args:
        args: Command-line arguments containing:
            - images: Number of images to process
            - kitchen: Whether to use kitchen dataset
    """
    print("=" * 60)
    print("🚀 VGGT 3D Reconstruction Demo")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Images: {args.images}")
    print(f"Dataset: {'Kitchen' if args.kitchen else 'Test'}")
    print("-" * 60)

    # Select images
    if args.kitchen and TEST_DATA["kitchen_path"].exists():
        image_dir = TEST_DATA["kitchen_path"]
        image_paths = sorted(image_dir.glob("*.png"))[:args.images]
        print(f"📸 Using kitchen dataset: {len(image_paths)} images")
    else:
        # Create test images if they don't exist
        test_dir = DATA_DIR / "test"
        test_dir.mkdir(exist_ok=True)

        if not list(test_dir.glob("*.jpg")):
            print("Creating test images...")
            try:
                from utils.create_test_images import create_test_scenes
                create_test_scenes(test_dir)
            except Exception as e:
                print(f"⚠️ Could not create test images: {e}")
                print("   Please provide your own images in the data/ directory.")
                return

        image_paths = sorted(test_dir.glob("*.jpg"))[:args.images]
        if not image_paths:
            print("❌ No images found! Please add images to the data/ directory.")
            return
        print(f"📸 Using test images: {len(image_paths)} images")

    # Load and process images
    images = []
    for path in image_paths:
        try:
            img = Image.open(path).convert('RGB')
            img_resized = img.resize((CAMERA_CONFIG["image_width"], CAMERA_CONFIG["image_height"]))
            images.append(np.array(img_resized))
        except Exception as e:
            print(f"⚠️ Could not load image {path}: {e}")
            continue

    if not images:
        print("❌ No valid images could be loaded!")
        return

    # Check if model is available
    if not is_model_available():
        print("\n⚠️ VGGT model not found!")
        print("Run: python main.py download")
        print("\nUsing simulated depth for demo...")

        # Simulate depth maps
        depth_maps = []
        for img in images:
            h, w, _ = img.shape
            depth = np.random.randn(h, w) * 2 + 5
            depth_maps.append(depth)
    else:
        # Process with real model
        print("\n🔮 Running VGGT reconstruction...")
        processor = VGGTProcessor(device=DEVICE)
        depth_maps = processor.process_images(images)

    # Create visualizations
    print("\n📊 Creating visualizations...")
    try:
        output_files = create_visualizations(images, depth_maps, OUTPUT_DIR)

        print("\n" + "=" * 60)
        print("✅ Demo complete!")
        print(f"📁 Results saved to: {OUTPUT_DIR}")
        for file_path in output_files:
            print(f"   - {file_path.name}")
        print("=" * 60)
    except Exception as e:
        print(f"\n⚠️ Error creating visualizations: {e}")
        print("   Results may be incomplete.")
        print("=" * 60)