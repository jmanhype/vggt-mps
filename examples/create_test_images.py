#!/usr/bin/env python3
"""
Create test images for VGGT 3D reconstruction demo
"""

from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path

# Create output directories
input_dir = Path("/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs")
input_dir.mkdir(parents=True, exist_ok=True)

print("Creating test images for VGGT...")

# Create a simple 3D scene with different viewpoints
for i in range(4):
    # Create base image
    img = Image.new('RGB', (640, 480), color='skyblue')
    draw = ImageDraw.Draw(img)

    # Draw ground plane
    draw.rectangle([0, 300, 640, 480], fill='green')

    # Draw a "building" from different angles
    angle = i * 30  # Different viewing angles

    # Calculate building position based on angle
    x_offset = 200 + angle

    # Draw building (simple rectangles)
    # Main structure
    draw.rectangle([x_offset, 150, x_offset+150, 300], fill='gray')

    # Windows
    for row in range(3):
        for col in range(3):
            wx = x_offset + 20 + col * 40
            wy = 170 + row * 40
            draw.rectangle([wx, wy, wx+25, wy+25], fill='lightblue')

    # Draw a tree
    tree_x = 100 + i * 50
    # Trunk
    draw.rectangle([tree_x, 250, tree_x+20, 300], fill='brown')
    # Leaves
    draw.ellipse([tree_x-20, 200, tree_x+40, 260], fill='darkgreen')

    # Draw sun
    draw.ellipse([500 - i*20, 50, 550 - i*20, 100], fill='yellow')

    # Save image
    filename = input_dir / f"test_scene_{i+1:03d}.jpg"
    img.save(filename, quality=95)
    print(f"Created: {filename}")

print(f"\n✅ Created 4 test images in {input_dir}")
print("These simulate different viewpoints of a simple 3D scene")