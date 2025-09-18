#!/usr/bin/env python3
"""Test real VGGT with actual model weights on MPS"""

import torch
import sys
from pathlib import Path
from PIL import Image
import numpy as np

print("=" * 60)
print("🍎 VGGT Real Model Test on MPS")
print("=" * 60)

# Setup
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device: {device}")

# Add VGGT to path
sys.path.insert(0, str(Path(__file__).parent / "repo" / "vggt"))

from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images

# Check if model file exists
model_path = Path(__file__).parent / "repo" / "vggt" / "vggt_model.pt"
if not model_path.exists():
    print(f"❌ Model file not found at {model_path}")
    print("Please download from: https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt")
    exit(1)

print(f"✅ Model file found: {model_path} ({model_path.stat().st_size / 1e9:.1f} GB)")

# Load model
print("\n🔄 Loading model weights...")
model = VGGT()
checkpoint = torch.load(model_path, map_location=device, weights_only=True)
model.load_state_dict(checkpoint)
model = model.to(device)
model.eval()
print("✅ Model loaded!")

# Create test images if needed
test_dir = Path(__file__).parent / "tmp" / "inputs"
test_dir.mkdir(parents=True, exist_ok=True)

test_images = list(test_dir.glob("*.jpg"))[:2]  # Use only 2 images for speed
if not test_images:
    print("\n📸 Creating test images...")
    for i in range(2):
        img = Image.new('RGB', (640, 480), color=(100 + i*50, 150, 200 - i*30))
        img_path = test_dir / f"quick_test_{i+1}.jpg"
        img.save(img_path)
        test_images.append(img_path)

# Convert to strings
image_paths = [str(p) for p in test_images]
print(f"\n🖼️ Using images: {image_paths}")

# Load and preprocess
print("\n🔄 Preprocessing images...")
input_images = load_and_preprocess_images(image_paths).to(device)
print(f"✅ Input shape: {input_images.shape}")

# Run inference
print("\n🧠 Running VGGT inference on MPS...")
with torch.no_grad():
    predictions = model(input_images)

print("\n✅ Inference complete!")
print(f"   - Depth: {predictions['depth'].shape}")
print(f"   - Camera poses: {predictions['pose_enc'].shape}")
print(f"   - World points: {predictions['world_points'].shape}")

# Save one depth map
depth = predictions['depth'][0, 0, :, :, 0].cpu().numpy()
output_dir = Path(__file__).parent / "tmp" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
plt.figure(figsize=(8, 6))
plt.imshow(depth, cmap='viridis')
plt.colorbar()
plt.title('VGGT Depth Map (Real Model on MPS)')
plt.savefig(output_dir / "real_depth_mps.png", dpi=100, bbox_inches='tight')
print(f"\n💾 Saved depth map to {output_dir}/real_depth_mps.png")

print("\n" + "=" * 60)
print("✅ VGGT Real Model Test Complete!")
print("🍎 Running on Apple Silicon with MPS acceleration")
print("=" * 60)