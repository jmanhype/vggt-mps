"""
VGGT-COLMAP 3D reconstruction demo following the simplified tutorial workflow.

This MCP Server provides 1 tool:
1. vggt_reconstruct_3d_scene_simplified: Perform simplified 3D scene reconstruction from images using VGGT model with feedforward approach

All tools extracted from `facebookresearch/vggt/demo_colmap.py`.
Note: This implementation follows the simplified tutorial approach with step-by-step visualizations.
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
import random
import glob
import torch
import torch.nn.functional as F
import trimesh
import matplotlib.pyplot as plt

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("DEMO_COLMAP_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("DEMO_COLMAP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
demo_colmap_mcp = FastMCP(name="demo_colmap")

@demo_colmap_mcp.tool
def vggt_reconstruct_3d_scene_simplified(
    # Primary data inputs
    scene_dir_path: Annotated[str | None, "Path to scene directory containing 'images' subdirectory with input images"] = None,
    # Analysis parameters with tutorial defaults
    seed: Annotated[int, "Random seed for reproducibility"] = 42,
    img_load_resolution: Annotated[int, "Image loading resolution"] = 1024,
    vggt_fixed_resolution: Annotated[int, "VGGT processing resolution"] = 518,
    conf_thres_value: Annotated[float, "Confidence threshold value for depth filtering"] = 5.0,
    max_points_for_colmap: Annotated[int, "Maximum number of points for COLMAP reconstruction"] = 100000,
    max_vis_points: Annotated[int, "Maximum number of points for visualization"] = 5000,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Perform simplified 3D scene reconstruction from images using VGGT model following tutorial approach.
    Input is scene directory with images subdirectory and output is visualizations, point cloud, and optional COLMAP reconstruction.
    """
    # Configure matplotlib for high-resolution outputs
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300

    # Input validation
    if scene_dir_path is None:
        raise ValueError("Path to scene directory must be provided")

    scene_dir = Path(scene_dir_path)
    if not scene_dir.exists():
        raise FileNotFoundError(f"Scene directory not found: {scene_dir_path}")

    images_dir = scene_dir / "images"
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Import VGGT modules
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images_square
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        from vggt.utils.geometry import unproject_depth_map_to_point_map
        from vggt.utils.helper import create_pixel_coordinate_grid, randomly_limit_trues
    except ImportError as e:
        raise ImportError(f"VGGT modules not available: {e}")

    # Try to import COLMAP modules (optional for this simplified demo)
    try:
        import pycolmap
        from vggt.dependency.np_to_pycolmap import batch_np_matrix_to_pycolmap_wo_track
        COLMAP_AVAILABLE = True
    except ImportError:
        COLMAP_AVAILABLE = False

    # Set seed for reproducibility
    np.random.seed(seed)
    torch.manual_seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # Set device with MPS support for Apple Silicon
    if torch.backends.mps.is_available():
        device = "mps"
        print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
    elif torch.cuda.is_available():
        device = "cuda"
        print("🔥 Using CUDA GPU")
    else:
        device = "cpu"
        print("💻 Using CPU")

    if device == "cuda":
        try:
            dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
        except:
            dtype = torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    # Define the VGGT inference function
    def run_VGGT(model, images, dtype, resolution=518):
        """Run VGGT inference on input images"""
        assert len(images.shape) == 4
        assert images.shape[1] == 3

        # Resize to VGGT resolution
        images_resized = F.interpolate(images, size=(resolution, resolution), mode="bilinear", align_corners=False)

        with torch.no_grad():
            # Only use autocast for CUDA, not for MPS
            if device == "cuda":
                with torch.cuda.amp.autocast(dtype=dtype, enabled=True):
                    images_batched = images_resized[None]  # add batch dimension
                    aggregated_tokens_list, ps_idx = model.aggregator(images_batched)
            else:
                images_batched = images_resized[None]  # add batch dimension
                aggregated_tokens_list, ps_idx = model.aggregator(images_batched)

            # Predict Cameras
            pose_enc = model.camera_head(aggregated_tokens_list)[-1]
            # Extrinsic and intrinsic matrices, following OpenCV convention (camera from world)
            extrinsic, intrinsic = pose_encoding_to_extri_intri(pose_enc, images_resized.shape[-2:])
            # Predict Depth Maps
            depth_map, depth_conf = model.depth_head(aggregated_tokens_list, images_batched, ps_idx)

        extrinsic = extrinsic.squeeze(0).cpu().numpy()
        intrinsic = intrinsic.squeeze(0).cpu().numpy()
        depth_map = depth_map.squeeze(0).cpu().numpy()
        depth_conf = depth_conf.squeeze(0).cpu().numpy()

        return extrinsic, intrinsic, depth_map, depth_conf

    # Load VGGT model
    model = VGGT()
    _URL = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt"
    model.load_state_dict(torch.hub.load_state_dict_from_url(_URL))
    model.eval()
    model = model.to(device)

    # Find and load example images
    image_paths = list(images_dir.glob("*"))
    image_paths = [p for p in image_paths if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]

    if len(image_paths) == 0:
        raise ValueError(f"No valid images found in {images_dir}")

    # Set up output directory
    if out_prefix is None:
        out_prefix = f"{scene_dir.name}_reconstruction_{timestamp}"

    output_dir = OUTPUT_DIR / out_prefix
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and preprocess images
    image_path_strs = [str(p) for p in image_paths]
    images, original_coords = load_and_preprocess_images_square(image_path_strs, img_load_resolution)
    images = images.to(device)
    original_coords = original_coords.to(device)

    artifacts = []

    # Display input images
    num_images = min(4, len(images))
    fig, axes = plt.subplots(1, num_images, figsize=(16, 4))
    if num_images == 1:
        axes = [axes]

    for i in range(num_images):
        img_np = images[i].cpu().permute(1, 2, 0).numpy()
        img_np = np.clip(img_np, 0, 1)
        axes[i].imshow(img_np)
        axes[i].set_title(f"Image {i+1}")
        axes[i].axis('off')

    plt.suptitle(f"Input Images from {scene_dir.name}")
    plt.tight_layout()
    input_images_path = output_dir / "input_images.png"
    plt.savefig(input_images_path, dpi=300, bbox_inches='tight')
    plt.close()

    artifacts.append({
        "description": "Input images visualization",
        "path": str(input_images_path.resolve())
    })

    # Run VGGT inference
    extrinsic, intrinsic, depth_map, depth_conf = run_VGGT(model, images, dtype, vggt_fixed_resolution)

    # Generate 3D point clouds
    points_3d = unproject_depth_map_to_point_map(depth_map, extrinsic, intrinsic)

    # Visualize depth maps and confidence maps
    num_views = min(4, len(depth_map))
    fig, axes = plt.subplots(2, num_views, figsize=(16, 8))
    if num_views == 1:
        axes = axes.reshape(2, 1)

    for i in range(num_views):
        # Depth map
        im1 = axes[0, i].imshow(depth_map[i], cmap='viridis')
        axes[0, i].set_title(f"Depth Map {i+1}")
        axes[0, i].axis('off')
        plt.colorbar(im1, ax=axes[0, i], fraction=0.046, pad=0.04)

        # Confidence map
        im2 = axes[1, i].imshow(depth_conf[i], cmap='plasma')
        axes[1, i].set_title(f"Confidence {i+1}")
        axes[1, i].axis('off')
        plt.colorbar(im2, ax=axes[1, i], fraction=0.046, pad=0.04)

    plt.suptitle("VGGT Depth and Confidence Predictions")
    plt.tight_layout()
    depth_confidence_path = output_dir / "depth_and_confidence_maps.png"
    plt.savefig(depth_confidence_path, dpi=300, bbox_inches='tight')
    plt.close()

    artifacts.append({
        "description": "Depth and confidence maps",
        "path": str(depth_confidence_path.resolve())
    })

    # Process for COLMAP format (simplified approach without Bundle Adjustment)
    shared_camera = False  # feedforward manner doesn't support shared camera
    camera_type = "PINHOLE"  # feedforward manner only supports PINHOLE camera

    image_size = np.array([vggt_fixed_resolution, vggt_fixed_resolution])
    num_frames, height, width, _ = points_3d.shape

    # Generate RGB colors for points
    points_rgb = F.interpolate(
        images, size=(vggt_fixed_resolution, vggt_fixed_resolution), mode="bilinear", align_corners=False
    )
    points_rgb = (points_rgb.cpu().numpy() * 255).astype(np.uint8)
    points_rgb = points_rgb.transpose(0, 2, 3, 1)

    # Create pixel coordinates and apply confidence filtering
    points_xyf = create_pixel_coordinate_grid(num_frames, height, width)

    # Apply confidence mask
    conf_mask = depth_conf >= conf_thres_value
    # Randomly limit to max points for COLMAP
    conf_mask = randomly_limit_trues(conf_mask, max_points_for_colmap)

    # Filter points based on confidence
    filtered_points_3d = points_3d[conf_mask]
    filtered_points_xyf = points_xyf[conf_mask]
    filtered_points_rgb = points_rgb[conf_mask]

    # Visualize filtered 3D points
    if len(filtered_points_3d) > 0:
        # Subsample for visualization
        if len(filtered_points_3d) > max_vis_points:
            indices = np.random.choice(len(filtered_points_3d), max_vis_points, replace=False)
            vis_points = filtered_points_3d[indices]
            vis_colors = filtered_points_rgb[indices]
        else:
            vis_points = filtered_points_3d
            vis_colors = filtered_points_rgb

        # Create 3D scatter plot
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')

        # Plot points with colors
        scatter = ax.scatter(vis_points[:, 0], vis_points[:, 1], vis_points[:, 2],
                            c=vis_colors/255.0, s=1, alpha=0.8)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'Filtered 3D Point Cloud\n({len(vis_points)} points, confidence > {conf_thres_value})')

        plt.tight_layout()
        pointcloud_vis_path = output_dir / "3d_point_cloud_visualization.png"
        plt.savefig(pointcloud_vis_path, dpi=300, bbox_inches='tight')
        plt.close()

        artifacts.append({
            "description": "3D point cloud visualization",
            "path": str(pointcloud_vis_path.resolve())
        })

    # Convert to COLMAP format if available
    reconstruction = None
    if COLMAP_AVAILABLE and len(filtered_points_3d) > 0:
        try:
            reconstruction = batch_np_matrix_to_pycolmap_wo_track(
                filtered_points_3d,
                filtered_points_xyf,
                filtered_points_rgb,
                extrinsic,
                intrinsic,
                image_size,
                shared_camera=shared_camera,
                camera_type=camera_type,
            )
        except Exception as e:
            reconstruction = None

    # Save sparse reconstruction if COLMAP is available
    if reconstruction is not None:
        sparse_dir = output_dir / "sparse"
        sparse_dir.mkdir(parents=True, exist_ok=True)

        try:
            reconstruction.write(str(sparse_dir))
            artifacts.append({
                "description": "COLMAP sparse reconstruction",
                "path": str(sparse_dir.resolve())
            })
        except Exception:
            pass

    # Save point cloud as PLY file for visualization
    if len(filtered_points_3d) > 0:
        ply_path = output_dir / "points.ply"
        try:
            point_cloud = trimesh.PointCloud(filtered_points_3d, colors=filtered_points_rgb)
            point_cloud.export(str(ply_path))
            artifacts.append({
                "description": "3D point cloud PLY file",
                "path": str(ply_path.resolve())
            })
        except Exception:
            pass

    # Create summary report with camera parameters and statistics
    summary_data = []

    # Basic statistics
    summary_data.append(["scene_name", scene_dir.name])
    summary_data.append(["num_input_images", len(images)])
    summary_data.append(["processing_resolution", f"{vggt_fixed_resolution}x{vggt_fixed_resolution}"])
    summary_data.append(["original_resolution", f"{img_load_resolution}x{img_load_resolution}"])
    summary_data.append(["device_used", device])
    summary_data.append(["data_type", str(dtype)])
    summary_data.append(["total_3d_points_generated", np.prod(points_3d.shape[:3])])
    summary_data.append(["points_after_confidence_filtering", len(filtered_points_3d)])
    summary_data.append(["confidence_threshold", conf_thres_value])

    # Camera parameters
    for i in range(len(extrinsic)):
        fx, fy = intrinsic[i][0, 0], intrinsic[i][1, 1]
        cx, cy = intrinsic[i][0, 2], intrinsic[i][1, 2]
        summary_data.append([f"camera_{i+1}_fx", fx])
        summary_data.append([f"camera_{i+1}_fy", fy])
        summary_data.append([f"camera_{i+1}_cx", cx])
        summary_data.append([f"camera_{i+1}_cy", cy])
        summary_data.append([f"camera_{i+1}_translation_x", extrinsic[i][0, 3]])
        summary_data.append([f"camera_{i+1}_translation_y", extrinsic[i][1, 3]])
        summary_data.append([f"camera_{i+1}_translation_z", extrinsic[i][2, 3]])

    # Point cloud spatial extents
    if len(filtered_points_3d) > 0:
        summary_data.append(["pointcloud_x_min", filtered_points_3d[:, 0].min()])
        summary_data.append(["pointcloud_x_max", filtered_points_3d[:, 0].max()])
        summary_data.append(["pointcloud_y_min", filtered_points_3d[:, 1].min()])
        summary_data.append(["pointcloud_y_max", filtered_points_3d[:, 1].max()])
        summary_data.append(["pointcloud_z_min", filtered_points_3d[:, 2].min()])
        summary_data.append(["pointcloud_z_max", filtered_points_3d[:, 2].max()])

    # Reconstruction info
    if reconstruction is not None:
        summary_data.append(["colmap_num_cameras", len(reconstruction.cameras)])
        summary_data.append(["colmap_num_images", len(reconstruction.images)])
        summary_data.append(["colmap_num_3d_points", len(reconstruction.points3D)])

    summary_df = pd.DataFrame(summary_data, columns=["parameter", "value"])
    summary_path = output_dir / "reconstruction_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    artifacts.append({
        "description": "Reconstruction summary and parameters",
        "path": str(summary_path.resolve())
    })

    message = f"3D reconstruction completed for {scene_dir.name} with {len(images)} images, {len(filtered_points_3d)} filtered points"

    return {
        "message": message,
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_colmap.py",
        "artifacts": artifacts
    }