#!/usr/bin/env python3
"""Extract all images from a Jupyter notebook."""

import json
import base64
import os
from pathlib import Path
import sys

def extract_images_from_notebook(notebook_path, output_dir):
    """Extract all images from a Jupyter notebook.
    
    Args:
        notebook_path: Path to the .ipynb file
        output_dir: Directory to save extracted images
    """
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load notebook
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)
    
    image_count = 0
    
    # Iterate through cells
    for cell_idx, cell in enumerate(notebook['cells']):
        if 'outputs' in cell:
            for output_idx, output in enumerate(cell['outputs']):
                # Check for image data in different formats
                if 'data' in output:
                    data = output['data']
                    
                    # PNG images
                    if 'image/png' in data:
                        image_count += 1
                        image_data = data['image/png']
                        # Decode base64
                        image_bytes = base64.b64decode(image_data)
                        # Save image
                        filename = f"cell_{cell_idx+1}_output_{output_idx+1}_fig_{image_count}.png"
                        filepath = output_dir / filename
                        with open(filepath, 'wb') as img_file:
                            img_file.write(image_bytes)
                        print(f"Saved: {filename}")
                    
                    # JPEG images
                    elif 'image/jpeg' in data:
                        image_count += 1
                        image_data = data['image/jpeg']
                        # Decode base64
                        image_bytes = base64.b64decode(image_data)
                        # Save image
                        filename = f"cell_{cell_idx+1}_output_{output_idx+1}_fig_{image_count}.jpg"
                        filepath = output_dir / filename
                        with open(filepath, 'wb') as img_file:
                            img_file.write(image_bytes)
                        print(f"Saved: {filename}")
                    
                    # SVG images
                    elif 'image/svg+xml' in data:
                        image_count += 1
                        svg_data = data['image/svg+xml']
                        # SVG is usually not base64 encoded
                        if isinstance(svg_data, list):
                            svg_data = ''.join(svg_data)
                        filename = f"cell_{cell_idx+1}_output_{output_idx+1}_fig_{image_count}.svg"
                        filepath = output_dir / filename
                        with open(filepath, 'w') as img_file:
                            img_file.write(svg_data)
                        print(f"Saved: {filename}")
    
    print(f"\nTotal images extracted: {image_count}")
    return image_count

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_notebook_images.py <notebook.ipynb> <output_dir>")
        sys.exit(1)
    
    notebook_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    extract_images_from_notebook(notebook_path, output_dir)