"""
Data setup for demo_gradio tests.
Prepares test data from VGGT examples directory matching tutorial execution.
"""

from pathlib import Path
import shutil
import os

def setup_test_images():
    """Copy test images from VGGT examples to test data directory."""
    # Source: VGGT examples room scene (used in tutorial)
    source_dir = Path(__file__).parent.parent.parent.parent / "repo" / "vggt" / "examples" / "room" / "images"
    
    # Destination: test data directory
    dest_dir = Path(__file__).parent / "room_images"
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Source images not found: {source_dir}")
    
    # Create destination directory
    dest_dir.mkdir(exist_ok=True)
    
    # Copy images
    image_files = list(source_dir.glob("*"))
    image_files = [f for f in image_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    for img_file in image_files:
        dest_file = dest_dir / img_file.name
        if not dest_file.exists():
            shutil.copy2(img_file, dest_file)
    
    return dest_dir, len(image_files)

if __name__ == "__main__":
    images_dir, count = setup_test_images()
    print(f"Copied {count} test images to: {images_dir}")