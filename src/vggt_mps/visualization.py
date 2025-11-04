"""
Visualization utilities for VGGT-MPS
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import torch
from typing import List, Optional, Dict, Any


def create_visualizations(
    images: List[np.ndarray],
    depth_maps: List[np.ndarray],
    output_dir: Path,
    camera_poses: Optional[np.ndarray] = None,
    point_cloud: Optional[np.ndarray] = None
) -> List[Path]:
    """
    Create visualization outputs for VGGT results

    Args:
        images: List of input images
        depth_maps: List of predicted depth maps
        output_dir: Directory to save visualizations
        camera_poses: Optional camera pose estimates
        point_cloud: Optional 3D point cloud

    Returns:
        List of created file paths
    """
    output_files = []
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create input views visualization
    fig, axes = plt.subplots(1, len(images), figsize=(4*len(images), 4))
    if len(images) == 1:
        axes = [axes]

    for i, img in enumerate(images):
        axes[i].imshow(img)
        axes[i].set_title(f"View {i+1}")
        axes[i].axis('off')

    plt.suptitle("Input Views")
    plt.tight_layout()
    input_path = output_dir / "input_views.png"
    plt.savefig(input_path, dpi=100, bbox_inches='tight')
    plt.close()
    output_files.append(input_path)

    # Create depth maps visualization
    fig, axes = plt.subplots(1, len(depth_maps), figsize=(4*len(depth_maps), 4))
    if len(depth_maps) == 1:
        axes = [axes]

    for i, depth in enumerate(depth_maps):
        im = axes[i].imshow(depth, cmap='viridis')
        axes[i].set_title(f"Depth {i+1}")
        axes[i].axis('off')
        plt.colorbar(im, ax=axes[i], fraction=0.046)

    plt.suptitle("Predicted Depth Maps")
    plt.tight_layout()
    depth_path = output_dir / "depth_maps.png"
    plt.savefig(depth_path, dpi=100, bbox_inches='tight')
    plt.close()
    output_files.append(depth_path)

    # Create 3D visualization if point cloud provided
    if point_cloud is not None:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Sample points for visualization
        max_points = 5000
        if len(point_cloud) > max_points:
            indices = np.random.choice(len(point_cloud), max_points, replace=False)
            points = point_cloud[indices]
        else:
            points = point_cloud

        ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                  c=points[:, 2], cmap='viridis', s=1, alpha=0.6)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Point Cloud Reconstruction')

        viz_path = output_dir / "3d_reconstruction.png"
        plt.savefig(viz_path, dpi=100, bbox_inches='tight')
        plt.close()
        output_files.append(viz_path)

        # Export point cloud to PLY
        ply_path = output_dir / "point_cloud.ply"
        export_ply(point_cloud, ply_path)
        output_files.append(ply_path)

    return output_files


def export_ply(points: np.ndarray, output_path: Path, colors: Optional[np.ndarray] = None) -> None:
    """
    Export point cloud to PLY format.

    Args:
        points: Nx3 array of 3D points
        output_path: Path to save PLY file
        colors: Optional Nx3 array of RGB colors (0-255)
    """

    # Prepare header
    num_points = len(points)
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {num_points}",
        "property float x",
        "property float y",
        "property float z",
    ]

    if colors is not None:
        header.extend([
            "property uchar red",
            "property uchar green",
            "property uchar blue"
        ])

    header.append("end_header")

    # Write PLY file
    with open(output_path, 'w') as f:
        for line in header:
            f.write(line + '\n')

        for i in range(num_points):
            x, y, z = points[i]
            if colors is not None:
                r, g, b = colors[i]
                f.write(f"{x:.6f} {y:.6f} {z:.6f} {int(r)} {int(g)} {int(b)}\n")
            else:
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")


def create_depth_from_images(images: List[np.ndarray]) -> List[np.ndarray]:
    """Create simulated depth maps from images (for testing without model)"""
    depth_maps = []
    for img in images:
        # Simple depth simulation based on image gradients
        gray = np.mean(img, axis=2)
        h, w = gray.shape

        # Create radial depth pattern
        center_x, center_y = w // 2, h // 2
        y_coords, x_coords = np.ogrid[:h, :w]
        distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)

        # Normalize to depth range
        max_dist = np.sqrt(center_x**2 + center_y**2)
        depth = 5.0 + 3.0 * (1.0 - distances / max_dist)

        # Add some noise based on image content
        depth += 0.5 * (gray / 255.0 - 0.5)

        depth_maps.append(depth)

    return depth_maps