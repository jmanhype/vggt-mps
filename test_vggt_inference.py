#!/usr/bin/env python3
"""
Test VGGT quick start inference with MPS support
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent / "src"))

from tools.readme import vggt_quick_start_inference

print("=" * 60)
print("Testing VGGT Quick Start Inference with MPS")
print("=" * 60)

# Run inference
result = vggt_quick_start_inference(
    image_directory="/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs",
    image_format="jpg",
    model_id="vggt",
    output_directory="/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/outputs",
    max_images=4,
    save_outputs=True,
    device="auto"  # Will auto-detect MPS
)

print("\nResult:")
print(f"Message: {result['message']}")
print(f"Reference: {result['reference']}")

if 'artifacts' in result:
    print("\nGenerated artifacts:")
    for artifact in result['artifacts']:
        print(f"  - {artifact['description']}")
        print(f"    Path: {artifact['path']}")

print("=" * 60)