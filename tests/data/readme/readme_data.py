"""
Data preparation for readme tests.
Downloads and prepares test images from the VGGT repository examples.
"""

import os
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

def setup_test_images():
    """
    Setup test images for VGGT readme tests.
    Uses actual example images from the VGGT repository.
    """
    # Project root and paths
    project_root = Path(__file__).parent.parent.parent.parent
    vggt_repo_path = project_root / "repo" / "vggt"
    examples_path = vggt_repo_path / "examples"

    # Test data directory
    test_data_dir = Path(__file__).parent
    test_images_dir = test_data_dir / "images"

    # Create test images directory
    test_images_dir.mkdir(exist_ok=True)

    # Try to find example images from VGGT repo
    if examples_path.exists():
        # Look for room example (from the notebook)
        room_path = examples_path / "room"
        if room_path.exists():
            room_images_path = room_path / "images"
            if room_images_path.exists():
                # Copy first 3 images from room example
                image_files = [f for f in os.listdir(room_images_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                image_files = sorted(image_files)[:3]  # Take first 3 as per tutorial

                for i, img_file in enumerate(image_files):
                    src_path = room_images_path / img_file
                    # Use consistent naming for tests
                    dst_path = test_images_dir / f"test_image_{i+1}.jpg"
                    shutil.copy2(src_path, dst_path)
                    print(f"Copied {img_file} to {dst_path.name}")

                return str(test_images_dir)

    # Fallback: Create dummy images if examples not found
    print("VGGT examples not found, creating dummy test images...")
    for i in range(3):
        # Create a simple test image (256x256 RGB)
        dummy_img = Image.fromarray(np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8))
        dummy_path = test_images_dir / f"test_image_{i+1}.jpg"
        dummy_img.save(dummy_path)
        print(f"Created dummy test image: {dummy_path.name}")

    return str(test_images_dir)

if __name__ == "__main__":
    images_dir = setup_test_images()
    print(f"Test images setup complete in: {images_dir}")