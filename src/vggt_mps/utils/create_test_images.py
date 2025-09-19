"""
Create test images for VGGT demos
"""

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path


def create_test_scenes(output_dir: Path, num_images: int = 4):
    """
    Create simple test images for testing VGGT

    Args:
        output_dir: Directory to save test images
        num_images: Number of test images to create
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple 3D scene from different viewpoints
    for i in range(num_images):
        # Create image with geometric shapes
        img = Image.new('RGB', (640, 480), color='skyblue')
        draw = ImageDraw.Draw(img)

        # Draw ground plane
        ground_color = (100, 150, 100)  # Green
        draw.rectangle([0, 300, 640, 480], fill=ground_color)

        # Draw buildings/boxes from different angles
        angle = (i / num_images) * 360
        offset = int(100 * np.sin(np.radians(angle)))

        # Building 1
        x1 = 150 + offset
        draw.rectangle([x1, 200, x1+100, 300], fill=(150, 100, 100))
        draw.rectangle([x1+10, 210, x1+30, 230], fill=(200, 200, 255))  # Window
        draw.rectangle([x1+70, 210, x1+90, 230], fill=(200, 200, 255))  # Window

        # Building 2
        x2 = 350 + offset // 2
        draw.rectangle([x2, 180, x2+80, 300], fill=(100, 100, 150))
        draw.rectangle([x2+20, 190, x2+35, 210], fill=(200, 200, 255))  # Window
        draw.rectangle([x2+45, 190, x2+60, 210], fill=(200, 200, 255))  # Window

        # Add some depth cues with overlapping
        if i % 2 == 0:
            # Tree in foreground
            tree_x = 450 - offset
            draw.ellipse([tree_x, 250, tree_x+60, 310], fill=(50, 120, 50))
            draw.rectangle([tree_x+25, 280, tree_x+35, 320], fill=(100, 70, 50))

        # Save image
        img_path = output_dir / f"test_view_{i+1:02d}.jpg"
        img.save(img_path, quality=95)
        print(f"  Created: {img_path.name}")

    print(f"✅ Created {num_images} test images in {output_dir}")


def create_kitchen_style_images(output_dir: Path, num_images: int = 4):
    """
    Create kitchen-style interior test images

    Args:
        output_dir: Directory to save test images
        num_images: Number of test images to create
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(num_images):
        # Create image with interior scene
        img = Image.new('RGB', (640, 480), color=(240, 240, 230))
        draw = ImageDraw.Draw(img)

        # Viewing angle
        angle = (i / num_images) * 45 - 22.5
        offset = int(50 * np.sin(np.radians(angle)))

        # Draw floor
        draw.polygon([0, 480, 0, 350, 640, 300, 640, 480], fill=(180, 150, 120))

        # Draw back wall
        draw.rectangle([0, 0, 640, 350], fill=(250, 245, 240))

        # Kitchen cabinets
        cabinet_color = (150, 120, 90)

        # Upper cabinets
        for j in range(3):
            x = 100 + j * 180 + offset
            draw.rectangle([x, 80, x+150, 180], fill=cabinet_color)
            draw.rectangle([x+10, 90, x+140, 170], fill=(130, 100, 70))

        # Lower cabinets
        for j in range(3):
            x = 100 + j * 180 + offset
            draw.rectangle([x, 280, x+150, 350], fill=cabinet_color)
            draw.rectangle([x+10, 290, x+140, 340], fill=(130, 100, 70))

        # Countertop
        draw.rectangle([90 + offset, 270, 550 + offset, 280], fill=(200, 200, 200))

        # Save image
        img_path = output_dir / f"kitchen_view_{i+1:02d}.jpg"
        img.save(img_path, quality=95)
        print(f"  Created: {img_path.name}")

    print(f"✅ Created {num_images} kitchen-style images in {output_dir}")