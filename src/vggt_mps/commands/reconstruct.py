"""
3D reconstruction command for VGGT-MPS
"""

import sys
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import argparse

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DEVICE, OUTPUT_DIR, CAMERA_CONFIG, PROCESSING_CONFIG,
    SPARSE_CONFIG, EXPORT_FORMATS, get_model_path, is_model_available
)
from vggt_core import VGGTProcessor
from vggt_sparse_attention import make_vggt_sparse
from visualization import create_visualizations
from utils.export import export_point_cloud


def run_reconstruction(args):
    """Run 3D reconstruction on specified images"""
    print("=" * 60)
    print("🔮 VGGT 3D Reconstruction")
    print("=" * 60)

    # Parse image paths
    image_paths = []
    for pattern in args.images:
        path = Path(pattern)
        if path.is_file():
            image_paths.append(path)
        elif path.is_dir():
            # Get all images in directory
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']:
                image_paths.extend(path.glob(ext))
        else:
            # Try glob pattern
            from glob import glob
            image_paths.extend([Path(p) for p in glob(pattern)])

    if not image_paths:
        print("❌ No images found!")
        return

    image_paths = sorted(set(image_paths))  # Remove duplicates and sort
    print(f"📸 Found {len(image_paths)} images")

    # Setup output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load images
    print("\n📂 Loading images...")
    images = []
    for path in image_paths[:PROCESSING_CONFIG["max_images"]]:
        print(f"  • {path.name}")
        img = Image.open(path).convert('RGB')
        img_resized = img.resize((CAMERA_CONFIG["image_width"], CAMERA_CONFIG["image_height"]))
        images.append(np.array(img_resized))

    if len(image_paths) > PROCESSING_CONFIG["max_images"]:
        print(f"  ⚠️ Limited to {PROCESSING_CONFIG['max_images']} images")

    # Check model availability
    if not is_model_available():
        print("\n❌ VGGT model not found!")
        print("Run: python main.py download")
        return

    # Initialize processor
    print(f"\n🚀 Initializing VGGT on {DEVICE}")
    processor = VGGTProcessor(device=DEVICE)

    # Apply sparse attention if requested
    if args.sparse:
        print(f"⚡ Enabling sparse attention (O(n) memory scaling)")
        print(f"  • Covisibility threshold: {SPARSE_CONFIG['covisibility_threshold']}")
        processor.model = make_vggt_sparse(processor.model, device=DEVICE)

    # Process images
    print("\n🔄 Processing images...")
    if args.sparse and len(images) > 10:
        print(f"  💡 Sparse attention enabled - handling {len(images)} images efficiently")

    try:
        results = processor.process_images(images)

        # Extract results
        if isinstance(results, dict):
            depth_maps = results.get('depth_maps', [])
            camera_poses = results.get('camera_poses', None)
            point_cloud = results.get('point_cloud', None)
        else:
            depth_maps = results
            camera_poses = None
            point_cloud = None

        # Create visualizations
        print("\n📊 Creating visualizations...")
        viz_files = create_visualizations(
            images, depth_maps, output_dir,
            camera_poses=camera_poses,
            point_cloud=point_cloud
        )

        # Export if requested
        if args.export and point_cloud is not None:
            export_format = EXPORT_FORMATS.get(args.export, {})
            export_path = output_dir / f"reconstruction{export_format.get('extension', '.ply')}"

            print(f"\n💾 Exporting to {args.export.upper()}...")
            export_point_cloud(
                point_cloud,
                export_path,
                format=args.export
            )
            print(f"  ✅ Saved to: {export_path}")

        print("\n" + "=" * 60)
        print("✅ Reconstruction complete!")
        print(f"📁 Results saved to: {output_dir}")
        for viz_file in viz_files:
            print(f"  • {viz_file.name}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during reconstruction: {e}")
        import traceback
        traceback.print_exc()