#!/usr/bin/env python3
"""
Portable VGGT 3D Reconstruction Demo
Works on any system with proper setup
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("🚀 VGGT 3D Reconstruction Demo")
print("=" * 60)

# Detect device
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ Using MPS (Apple Silicon)")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("✅ Using CUDA GPU")
else:
    device = torch.device("cpu")
    print("⚠️ Using CPU (slower)")

print(f"Device: {device}")
print("-" * 60)

# Use relative paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DATA_DIR = PROJECT_ROOT / "examples" / "sample_data" / "kitchen"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Check for test images
input_images = list(DATA_DIR.glob("*.jpg")) + list(DATA_DIR.glob("*.png"))
if not input_images:
    sample_images = sorted(SAMPLE_DATA_DIR.glob("*.png"))
    if sample_images:
        print("⚠️ No images found in data/ directory")
        print("   Falling back to examples/sample_data/kitchen")
        input_images = sample_images[:4]
    else:
        print("⚠️ No images found in data/ or examples/sample_data/kitchen")
        print("Please add images to:", DATA_DIR)
        sys.exit(1)

# Limit to 4 images for demo
input_images = sorted(input_images)[:4]
print(f"\n📸 Found {len(input_images)} images")

# Try to import VGGT
try:
    # First try local installation
    from src.vggt_sparse_attention import PatchedVGGT as VGGT
    print("✅ Using local VGGT with sparse attention")
except ImportError:
    try:
        # Try system VGGT
        from vggt.models.vggt import VGGT
        print("✅ Using system VGGT")
    except ImportError:
        print("❌ VGGT not found. Please install it first:")
        print("   pip install -r legacy/requirements.txt")
        print("   or follow installation instructions in README")
        sys.exit(1)

# Load and display images
n_images = len(input_images)
fig, axes = plt.subplots(1, n_images, figsize=(4*n_images, 4))
if n_images == 1:
    axes = [axes]

images = []
for i, path in enumerate(input_images):
    img = Image.open(path).convert('RGB')
    img_resized = img.resize((640, 480))
    images.append(np.array(img_resized))

    axes[i].imshow(img_resized)
    axes[i].set_title(f"View {i+1}")
    axes[i].axis('off')

plt.suptitle("Input Views for 3D Reconstruction")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "input_views.png", dpi=150, bbox_inches='tight')
print(f"✅ Saved input views to {OUTPUT_DIR / 'input_views.png'}")

print("\n🔮 Running VGGT 3D Reconstruction...")
print("-" * 60)

# Check for model
model_path = MODEL_DIR / "vggt_model.pt"
if not model_path.exists():
    print("📥 Model not found locally. Options:")
    print("1. Download from HuggingFace (5GB):")
    print("   python scripts/download_model.py")
    print("2. Place model manually in:", model_path)

    # For demo, create fake depth maps
    print("\n⚠️ Running in demo mode with simulated depth")
    depth_maps = []
    for i, img in enumerate(images):
        h, w, _ = img.shape
        # Simple gradient depth
        depth = np.linspace(1, 10, h*w).reshape(h, w)
        depth_maps.append(depth)
else:
    print(f"📂 Loading model from: {model_path}")
    model = VGGT()
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint)
    model = model.to(device).eval()
    print("✅ Model loaded successfully!")

    # Process images
    print("🧠 Running inference...")
    with torch.no_grad():
        # Convert images to tensor
        img_tensor = torch.stack([
            torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            for img in images
        ]).to(device)

        # Run model
        predictions = model(img_tensor)

    # Extract depth maps
    depth_tensor = predictions['depth'].cpu().numpy()
    depth_maps = [depth_tensor[0, i, :, :, 0] for i in range(depth_tensor.shape[1])]
    print("✅ Real inference complete!")

# Display depth maps
fig, axes = plt.subplots(1, len(depth_maps), figsize=(4*len(depth_maps), 4))
if len(depth_maps) == 1:
    axes = [axes]

for i, depth in enumerate(depth_maps):
    im = axes[i].imshow(depth, cmap='viridis')
    axes[i].set_title(f"Depth Map {i+1}")
    axes[i].axis('off')
    plt.colorbar(im, ax=axes[i], fraction=0.046)

plt.suptitle("Estimated Depth Maps")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "depth_maps.png", dpi=150, bbox_inches='tight')
print(f"✅ Saved depth maps to {OUTPUT_DIR / 'depth_maps.png'}")

# Generate 3D point cloud
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
    x = (xx - cx) * z / fx + i * 2
    y = (yy - cy) * z / fy

    # Sample points
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
ax.view_init(elev=20, azim=45)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "3d_reconstruction.png", dpi=150, bbox_inches='tight')
print(f"✅ Saved 3D reconstruction to {OUTPUT_DIR / '3d_reconstruction.png'}")

# Export point cloud
ply_path = OUTPUT_DIR / "point_cloud.ply"
with open(ply_path, 'w') as f:
    f.write("ply\n")
    f.write("format ascii 1.0\n")
    f.write(f"element vertex {len(combined_points)}\n")
    f.write("property float x\n")
    f.write("property float y\n")
    f.write("property float z\n")
    f.write("property uchar red\n")
    f.write("property uchar green\n")
    f.write("property uchar blue\n")
    f.write("end_header\n")

    for point, color in zip(combined_points, combined_colors):
        color_int = (color * 255).astype(int)
        f.write(f"{point[0]} {point[1]} {point[2]} ")
        f.write(f"{color_int[0]} {color_int[1]} {color_int[2]}\n")

print(f"✅ Exported point cloud to {ply_path}")

print("\n" + "=" * 60)
print("✅ VGGT 3D Reconstruction Complete!")
print(f"📁 Results saved to: {OUTPUT_DIR}")
print("   - input_views.png")
print("   - depth_maps.png")
print("   - 3d_reconstruction.png")
print("   - point_cloud.ply")
print("=" * 60)
