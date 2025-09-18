#!/usr/bin/env python3
"""
Demo: VGGT 3D Reconstruction on Apple Silicon with MPS
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

print("=" * 60)
print("🚀 VGGT 3D Reconstruction Demo on Apple Silicon")
print("=" * 60)

# Check MPS availability
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ Using MPS (Metal Performance Shaders) for GPU acceleration")
else:
    device = torch.device("cpu")
    print("⚠️ MPS not available, using CPU")

print(f"Device: {device}")
print("-" * 60)

# Load test images
input_dir = Path("/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs")
output_dir = Path("/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

image_paths = sorted(input_dir.glob("test_scene_*.jpg"))[:4]
print(f"\n📸 Found {len(image_paths)} test images")

# Load and display images
fig, axes = plt.subplots(1, len(image_paths), figsize=(16, 4))
images = []

for i, path in enumerate(image_paths):
    img = Image.open(path).convert('RGB')
    img_resized = img.resize((640, 480))
    images.append(np.array(img_resized))

    axes[i].imshow(img_resized)
    axes[i].set_title(f"View {i+1}")
    axes[i].axis('off')

plt.suptitle("Input Views for 3D Reconstruction")
plt.tight_layout()
plt.savefig(output_dir / "input_views.png", dpi=150, bbox_inches='tight')
plt.show()

print("\n🔮 Running VGGT 3D Reconstruction...")
print("-" * 60)

# Use real VGGT model
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "repo" / "vggt"))
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images

# MPS doesn't support bfloat16, use float32
dtype = torch.float32 if device.type == "mps" else torch.float16

# Load the real VGGT model
print("📥 Loading VGGT-1B model (5GB)...")
model_path = Path(__file__).parent.parent / "repo" / "vggt" / "vggt_model.pt"
if model_path.exists():
    print(f"📂 Loading from local: {model_path}")
    model = VGGT()
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint)
    model = model.to(device)
else:
    print("📥 Downloading from HuggingFace...")
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)

model.eval()
print("✅ Model loaded successfully!")

# Save images temporarily for VGGT loader
temp_paths = []
for i, img in enumerate(images):
    temp_path = output_dir / f"temp_input_{i:03d}.jpg"
    Image.fromarray(img).save(temp_path)
    temp_paths.append(str(temp_path))

# Load and preprocess with VGGT's loader
print("🖼️ Preprocessing images...")
input_images = load_and_preprocess_images(temp_paths).to(device)

# Run real VGGT inference
print("🧠 Running VGGT inference on MPS...")
with torch.no_grad():
    if device.type == "mps":
        # MPS doesn't support autocast
        predictions = model(input_images)
    else:
        with torch.cuda.amp.autocast(dtype=dtype):
            predictions = model(input_images)

# Extract real depth maps from predictions
depth_tensor = predictions['depth'].cpu().numpy()
depth_maps = [depth_tensor[0, i, :, :, 0] for i in range(depth_tensor.shape[1])]

# Clean up temp files
for path in temp_paths:
    Path(path).unlink()

print("✅ Real VGGT inference complete!")

# Display depth maps
fig, axes = plt.subplots(1, len(depth_maps), figsize=(16, 4))
for i, depth in enumerate(depth_maps):
    im = axes[i].imshow(depth, cmap='viridis')
    axes[i].set_title(f"Depth Map {i+1}")
    axes[i].axis('off')
    plt.colorbar(im, ax=axes[i], fraction=0.046)

plt.suptitle("Estimated Depth Maps")
plt.tight_layout()
plt.savefig(output_dir / "depth_maps.png", dpi=150, bbox_inches='tight')
plt.show()

print("✅ Depth estimation complete")

# Generate 3D point cloud (simplified)
print("\n🏗️ Generating 3D point cloud...")

all_points = []
all_colors = []

for i, (img, depth) in enumerate(zip(images, depth_maps)):
    h, w = depth.shape

    # Camera parameters (simplified)
    fx = fy = 500
    cx, cy = w/2, h/2

    # Create pixel grid
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))

    # Back-project to 3D
    z = depth
    x = (xx - cx) * z / fx + i * 2  # Offset each view
    y = (yy - cy) * z / fy

    # Sample points (for visualization)
    step = 10
    points = np.stack([x[::step, ::step], y[::step, ::step], z[::step, ::step]], axis=-1)
    colors = img[::step, ::step]

    all_points.append(points.reshape(-1, 3))
    all_colors.append(colors.reshape(-1, 3))

# Combine all points
combined_points = np.concatenate(all_points, axis=0)
combined_colors = np.concatenate(all_colors, axis=0) / 255.0

print(f"✅ Generated {len(combined_points)} 3D points")

# Create 3D visualization
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Subsample for visualization
indices = np.random.choice(len(combined_points), min(5000, len(combined_points)), replace=False)
vis_points = combined_points[indices]
vis_colors = combined_colors[indices]

scatter = ax.scatter(
    vis_points[:, 0],
    vis_points[:, 1],
    vis_points[:, 2],
    c=vis_colors,
    s=1,
    alpha=0.6
)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z (Depth)')
ax.set_title('3D Point Cloud Reconstruction')

# Set view angle
ax.view_init(elev=20, azim=45)

plt.tight_layout()
plt.savefig(output_dir / "3d_reconstruction.png", dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "=" * 60)
print("✅ VGGT 3D Reconstruction Demo Complete!")
print(f"📁 Results saved to: {output_dir}")
print("   - input_views.png")
print("   - depth_maps.png")
print("   - 3d_reconstruction.png")
print("\n🍎 Powered by Apple Silicon with MPS acceleration")
print("=" * 60)