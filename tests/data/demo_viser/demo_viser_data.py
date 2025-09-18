"""
Data setup script for demo_viser tests.

This script prepares test data by copying example images from the VGGT repository
to the test data directory, following the exact tutorial setup.
"""

import os
import shutil
from pathlib import Path

def setup_demo_viser_test_data():
    """
    Set up test data for demo_viser tests using VGGT repository example images.

    Returns:
        dict: Paths to test data directories and files
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    test_data_dir = Path(__file__).parent

    # VGGT repo examples directory (from tutorial)
    vggt_examples_dir = project_root / "repo" / "vggt" / "examples"

    # Create test input directory
    test_images_dir = test_data_dir / "images"
    test_images_dir.mkdir(parents=True, exist_ok=True)

    print(f"Setting up demo_viser test data...")
    print(f"Test data directory: {test_data_dir}")
    print(f"VGGT examples directory: {vggt_examples_dir}")

    # Check if VGGT examples exist
    if not vggt_examples_dir.exists():
        raise FileNotFoundError(f"VGGT examples directory not found: {vggt_examples_dir}")

    # Find scene directories (from tutorial, use first available scene)
    scene_dirs = [d for d in vggt_examples_dir.iterdir() if d.is_dir()]

    if not scene_dirs:
        raise ValueError(f"No scene directories found in {vggt_examples_dir}")

    # Use the first available scene (matching tutorial behavior)
    scene_dir = scene_dirs[0]
    source_images_dir = scene_dir / "images"

    if not source_images_dir.exists():
        raise ValueError(f"No images directory found in {scene_dir}")

    # Find image files (matching tutorial file filtering)
    image_paths = list(source_images_dir.glob("*"))
    image_paths = [p for p in image_paths if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]

    if len(image_paths) == 0:
        raise ValueError(f"No valid images found in {source_images_dir}")

    print(f"Found {len(image_paths)} images in {scene_dir.name}")
    print(f"Source images: {[p.name for p in image_paths[:5]]}{'...' if len(image_paths) > 5 else ''}")

    # Copy images to test directory
    copied_files = []
    for img_path in image_paths:
        dest_path = test_images_dir / img_path.name
        shutil.copy2(img_path, dest_path)
        copied_files.append(dest_path)

    print(f"Copied {len(copied_files)} images to test directory")

    # Return paths for test use
    return {
        "test_data_dir": test_data_dir,
        "test_images_dir": test_images_dir,
        "scene_name": scene_dir.name,
        "num_images": len(copied_files),
        "image_files": copied_files
    }

if __name__ == "__main__":
    # Run setup when script is executed directly
    result = setup_demo_viser_test_data()
    print(f"\nSetup completed successfully!")
    print(f"Scene: {result['scene_name']}")
    print(f"Images directory: {result['test_images_dir']}")
    print(f"Number of images: {result['num_images']}")