"""
VGGT 3D Scene Reconstruction and Visualization Demo.

This MCP Server provides 2 tools:
1. vggt_reconstruct_3d_scene: Reconstruct 3D scene from multi-view images using VGGT model
2. vggt_visualize_reconstruction: Generate comprehensive visualizations of 3D reconstruction results

All tools extracted from `facebookresearch/vggt/demo_viser.py`.
Note: Implements complete 3D reconstruction pipeline with depth estimation, confidence filtering, and point cloud generation.
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
import glob
import torch
import torch.nn.functional as F
from PIL import Image
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("DEMO_VISER_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("DEMO_VISER_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configure matplotlib for high-resolution outputs
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
demo_viser_mcp = FastMCP(name="demo_viser")

@demo_viser_mcp.tool
def vggt_reconstruct_3d_scene(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images. The directory should contain image files with extensions .jpg, .jpeg, or .png"] = None,
    # Analysis parameters with tutorial defaults
    resolution: Annotated[int, "Image resolution for processing"] = 518,
    confidence_threshold: Annotated[float, "Confidence threshold for point filtering (0.0 to 1.0)"] = 0.5,
    device_type: Annotated[Literal["auto", "cuda", "cpu", "mps"], "Device to use for computation"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Reconstruct 3D scene from multi-view images using VGGT model for depth estimation and point cloud generation.
    Input is directory of images and output is 3D point cloud data, depth maps, confidence maps, and camera poses.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_path = Path(images_dir)
    if not images_path.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Import VGGT modules
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images_square
        from vggt.utils.geometry import unproject_depth_map_to_point_map
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    except ImportError as e:
        raise ImportError(f"VGGT modules not available: {e}")

    # Find image files
    image_paths = list(images_path.glob("*"))
    image_paths = [p for p in image_paths if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]

    if len(image_paths) == 0:
        raise ValueError(f"No valid images found in {images_dir}")

    print(f"Found {len(image_paths)} images in {images_path.name}")

    # Set device with MPS support for Apple Silicon
    if device_type == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
            print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
        elif torch.cuda.is_available():
            device = "cuda"
            print("🔥 Using CUDA GPU")
        else:
            device = "cpu"
            print("💻 Using CPU")
    else:
        device = device_type

    if device == "cuda":
        try:
            dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
        except (RuntimeError, AttributeError) as e:
            # Fallback to float16 if unable to query device capability
            print(f"⚠️ Could not determine CUDA device capability ({type(e).__name__}), using float16")
            dtype = torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    print(f"Using device: {device}")
    print(f"Using dtype: {dtype}")

    # Load VGGT model with timeout handling
    print("Loading VGGT model...")
    try:
        # Use the alternative loading method from tutorial
        try:
            model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
        except Exception as e:
            print(f"from_pretrained failed: {e}")
            print("Trying alternative loading method...")
            model = VGGT()
            _URL = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt"
            model.load_state_dict(torch.hub.load_state_dict_from_url(_URL))
            model = model.to(device)
        
        model.eval()
        print("Model loaded successfully!")
    except Exception as e:
        raise RuntimeError(f"Model loading failed: {e}")

    # Load and preprocess images
    image_path_strs = [str(p) for p in image_paths]
    print(f"Loading {len(image_path_strs)} images...")
    images, original_coords = load_and_preprocess_images_square(image_path_strs, resolution)
    images = images.to(device)
    print(f"Loaded images with shape: {images.shape}")

    # Run VGGT inference with MPS support
    print("Running VGGT inference...")
    with torch.no_grad():
        # Only use autocast for CUDA, not for MPS
        if device == "cuda":
            with torch.cuda.amp.autocast(dtype=dtype, enabled=True):
                predictions = model(images)
        else:
            predictions = model(images)

    print("Inference completed!")
    print(f"Prediction keys: {list(predictions.keys())}")

    # Extract predictions safely
    print("Extracting predictions...")
    depth_maps = predictions['depth'].cpu().numpy()
    confidence_maps = predictions['depth_conf'].cpu().numpy()
    world_points = predictions['world_points'].cpu().numpy()
    world_points_conf = predictions['world_points_conf'].cpu().numpy()

    # Generate camera matrices from pose encoding
    extrinsics, intrinsics = pose_encoding_to_extri_intri(predictions["pose_enc"], images.shape[-2:])
    extrinsics = extrinsics.cpu().numpy()
    intrinsics = intrinsics.cpu().numpy()

    print(f"Depth maps shape: {depth_maps.shape}")
    print(f"Confidence maps shape: {confidence_maps.shape}")
    print(f"World points shape: {world_points.shape}")
    print(f"World points conf shape: {world_points_conf.shape}")

    # Generate 3D point clouds from VGGT world points
    print("Using 3D world points from VGGT predictions...")
    point_clouds = world_points.squeeze(0)  # Remove batch dimension
    print(f"Point clouds shape: {point_clouds.shape}")

    # Apply confidence filtering
    print(f"Applying confidence filtering with threshold: {confidence_threshold}")

    # Collect valid 3D points from all views
    all_points = []
    all_colors = []

    # Handle the actual tensor shapes
    num_views = point_clouds.shape[0]
    for i in range(num_views):
        # Get confidence mask for this view
        conf_mask = world_points_conf.squeeze(0)[i] > confidence_threshold
        
        # Get valid 3D points for this view
        valid_points = point_clouds[i][conf_mask]
        
        # Get corresponding colors from original image
        img_rgb = images[i].cpu().permute(1, 2, 0).numpy()
        img_rgb = (img_rgb * 255).astype(np.uint8)
        valid_colors = img_rgb[conf_mask]
        
        all_points.append(valid_points)
        all_colors.append(valid_colors)
        
        print(f"View {i+1}: {len(valid_points)} valid points")

    # Combine all points
    if all_points:
        combined_points = np.concatenate(all_points, axis=0)
        combined_colors = np.concatenate(all_colors, axis=0)
        print(f"Total combined points: {len(combined_points)}")
    else:
        print("No valid points found with current confidence threshold")
        combined_points = np.array([])
        combined_colors = np.array([])

    # Generate output file paths
    if out_prefix is None:
        out_prefix = f"vggt_reconstruction_{timestamp}"

    # Save point cloud data
    if len(combined_points) > 0:
        point_cloud_df = pd.DataFrame({
            'x': combined_points[:, 0],
            'y': combined_points[:, 1],
            'z': combined_points[:, 2],
            'r': combined_colors[:, 0],
            'g': combined_colors[:, 1],
            'b': combined_colors[:, 2]
        })
        point_cloud_file = OUTPUT_DIR / f"{out_prefix}_point_cloud.csv"
        point_cloud_df.to_csv(point_cloud_file, index=False)
    else:
        point_cloud_file = None

    # Save camera poses
    extrinsics_viz = extrinsics.squeeze(0)
    intrinsics_viz = intrinsics.squeeze(0)
    
    camera_data = []
    for i in range(len(extrinsics_viz)):
        camera_data.append({
            'camera_id': i + 1,
            'rotation_00': extrinsics_viz[i][0, 0],
            'rotation_01': extrinsics_viz[i][0, 1],
            'rotation_02': extrinsics_viz[i][0, 2],
            'rotation_10': extrinsics_viz[i][1, 0],
            'rotation_11': extrinsics_viz[i][1, 1],
            'rotation_12': extrinsics_viz[i][1, 2],
            'rotation_20': extrinsics_viz[i][2, 0],
            'rotation_21': extrinsics_viz[i][2, 1],
            'rotation_22': extrinsics_viz[i][2, 2],
            'translation_x': extrinsics_viz[i][0, 3],
            'translation_y': extrinsics_viz[i][1, 3],
            'translation_z': extrinsics_viz[i][2, 3]
        })
    
    camera_poses_df = pd.DataFrame(camera_data)
    camera_poses_file = OUTPUT_DIR / f"{out_prefix}_camera_poses.csv"
    camera_poses_df.to_csv(camera_poses_file, index=False)

    # Save reconstruction summary
    summary_data = {
        'scene_name': images_path.name,
        'num_input_images': len(images),
        'image_resolution': f"{images.shape[-2]}x{images.shape[-1]}",
        'total_3d_points': len(combined_points) if len(combined_points) > 0 else 0,
        'confidence_threshold': confidence_threshold,
        'device_used': device,
        'data_type': str(dtype)
    }

    if len(combined_points) > 0:
        summary_data.update({
            'x_range_min': float(combined_points[:, 0].min()),
            'x_range_max': float(combined_points[:, 0].max()),
            'y_range_min': float(combined_points[:, 1].min()),
            'y_range_max': float(combined_points[:, 1].max()),
            'z_range_min': float(combined_points[:, 2].min()),
            'z_range_max': float(combined_points[:, 2].max())
        })

    summary_df = pd.DataFrame([summary_data])
    summary_file = OUTPUT_DIR / f"{out_prefix}_summary.csv"
    summary_df.to_csv(summary_file, index=False)

    # Prepare artifacts list
    artifacts = [
        {
            "description": "Camera poses and extrinsic parameters",
            "path": str(camera_poses_file.resolve())
        },
        {
            "description": "Reconstruction summary statistics",
            "path": str(summary_file.resolve())
        }
    ]

    if point_cloud_file is not None:
        artifacts.insert(0, {
            "description": "3D point cloud with RGB colors",
            "path": str(point_cloud_file.resolve())
        })

    return {
        "message": f"3D reconstruction completed: {len(combined_points) if len(combined_points) > 0 else 0} points from {len(images)} images",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_viser.py",
        "artifacts": artifacts
    }


@demo_viser_mcp.tool
def vggt_visualize_reconstruction(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images. The directory should contain image files with extensions .jpg, .jpeg, or .png"] = None,
    # Analysis parameters with tutorial defaults
    resolution: Annotated[int, "Image resolution for processing"] = 518,
    confidence_threshold: Annotated[float, "Confidence threshold for point filtering (0.0 to 1.0)"] = 0.5,
    max_display_points: Annotated[int, "Maximum number of points to display in 3D visualization"] = 10000,
    device_type: Annotated[Literal["auto", "cuda", "cpu", "mps"], "Device to use for computation"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Generate comprehensive visualizations of VGGT 3D reconstruction including depth maps, confidence maps, and 3D point clouds.
    Input is directory of images and output is visualization plots showing reconstruction quality and 3D structure.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_path = Path(images_dir)
    if not images_path.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Import VGGT modules
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images_square
        from vggt.utils.geometry import unproject_depth_map_to_point_map
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    except ImportError as e:
        raise ImportError(f"VGGT modules not available: {e}")

    # Find image files
    image_paths = list(images_path.glob("*"))
    image_paths = [p for p in image_paths if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]

    if len(image_paths) == 0:
        raise ValueError(f"No valid images found in {images_dir}")

    print(f"Found {len(image_paths)} images in {images_path.name}")

    # Set device with MPS support for Apple Silicon
    if device_type == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
            print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
        elif torch.cuda.is_available():
            device = "cuda"
            print("🔥 Using CUDA GPU")
        else:
            device = "cpu"
            print("💻 Using CPU")
    else:
        device = device_type

    if device == "cuda":
        try:
            dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
        except (RuntimeError, AttributeError) as e:
            # Fallback to float16 if unable to query device capability
            print(f"⚠️ Could not determine CUDA device capability ({type(e).__name__}), using float16")
            dtype = torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    # Load VGGT model
    print("Loading VGGT model...")
    try:
        try:
            model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
        except Exception as e:
            model = VGGT()
            _URL = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt"
            model.load_state_dict(torch.hub.load_state_dict_from_url(_URL))
            model = model.to(device)
        
        model.eval()
    except Exception as e:
        raise RuntimeError(f"Model loading failed: {e}")

    # Load and preprocess images
    image_path_strs = [str(p) for p in image_paths]
    images, original_coords = load_and_preprocess_images_square(image_path_strs, resolution)
    images = images.to(device)

    # Run VGGT inference with MPS support
    print("Running VGGT inference...")
    with torch.no_grad():
        # Only use autocast for CUDA, not for MPS
        if device == "cuda":
            with torch.cuda.amp.autocast(dtype=dtype, enabled=True):
                predictions = model(images)
        else:
            predictions = model(images)

    # Extract predictions
    depth_maps = predictions['depth'].cpu().numpy()
    confidence_maps = predictions['depth_conf'].cpu().numpy()
    world_points = predictions['world_points'].cpu().numpy()
    world_points_conf = predictions['world_points_conf'].cpu().numpy()

    # Generate output file paths
    if out_prefix is None:
        out_prefix = f"vggt_visualization_{timestamp}"

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

    plt.suptitle(f"Input Images from {images_path.name}")
    plt.tight_layout()
    input_images_file = OUTPUT_DIR / f"{out_prefix}_input_images.png"
    plt.savefig(input_images_file, dpi=300, bbox_inches='tight')
    plt.close()

    # Visualize depth maps and confidence maps
    depth_maps_viz = depth_maps.squeeze()
    confidence_maps_viz = confidence_maps.squeeze()

    if len(depth_maps_viz.shape) == 3:
        num_views = depth_maps_viz.shape[0]
    else:
        num_views = 1
        depth_maps_viz = depth_maps_viz[np.newaxis, ...]
        confidence_maps_viz = confidence_maps_viz[np.newaxis, ...]

    num_views_display = min(4, num_views)
    fig, axes = plt.subplots(2, num_views_display, figsize=(16, 8))
    if num_views_display == 1:
        axes = axes.reshape(2, 1)

    for i in range(num_views_display):
        # Depth map
        im1 = axes[0, i].imshow(depth_maps_viz[i], cmap='viridis')
        axes[0, i].set_title(f"Depth Map {i+1}")
        axes[0, i].axis('off')
        plt.colorbar(im1, ax=axes[0, i], fraction=0.046, pad=0.04)
        
        # Confidence map
        im2 = axes[1, i].imshow(confidence_maps_viz[i], cmap='plasma')
        axes[1, i].set_title(f"Confidence {i+1}")
        axes[1, i].axis('off')
        plt.colorbar(im2, ax=axes[1, i], fraction=0.046, pad=0.04)

    plt.suptitle("Depth Maps and Confidence Maps")
    plt.tight_layout()
    depth_confidence_file = OUTPUT_DIR / f"{out_prefix}_depth_confidence.png"
    plt.savefig(depth_confidence_file, dpi=300, bbox_inches='tight')
    plt.close()

    # Apply confidence filtering and generate point cloud
    print(f"Applying confidence filtering with threshold: {confidence_threshold}")
    point_clouds = world_points.squeeze(0)
    all_points = []
    all_colors = []

    num_views = point_clouds.shape[0]
    for i in range(num_views):
        conf_mask = world_points_conf.squeeze(0)[i] > confidence_threshold
        valid_points = point_clouds[i][conf_mask]
        img_rgb = images[i].cpu().permute(1, 2, 0).numpy()
        img_rgb = (img_rgb * 255).astype(np.uint8)
        valid_colors = img_rgb[conf_mask]
        all_points.append(valid_points)
        all_colors.append(valid_colors)

    # Combine all points
    if all_points:
        combined_points = np.concatenate(all_points, axis=0)
        combined_colors = np.concatenate(all_colors, axis=0)
    else:
        combined_points = np.array([])
        combined_colors = np.array([])

    # Visualize 3D point cloud
    if len(combined_points) > 0:
        # Subsample for visualization if too many points
        if len(combined_points) > max_display_points:
            indices = np.random.choice(len(combined_points), max_display_points, replace=False)
            vis_points = combined_points[indices]
            vis_colors = combined_colors[indices]
        else:
            vis_points = combined_points
            vis_colors = combined_colors
        
        # Create 3D scatter plot
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot points with colors
        scatter = ax.scatter(vis_points[:, 0], vis_points[:, 1], vis_points[:, 2], 
                            c=vis_colors/255.0, s=1, alpha=0.6)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'3D Point Cloud Reconstruction\n({len(vis_points)} points)')
        
        # Set equal aspect ratio
        max_range = np.array([vis_points[:, 0].max() - vis_points[:, 0].min(),
                             vis_points[:, 1].max() - vis_points[:, 1].min(),
                             vis_points[:, 2].max() - vis_points[:, 2].min()]).max() / 2.0
        
        mid_x = (vis_points[:, 0].max() + vis_points[:, 0].min()) * 0.5
        mid_y = (vis_points[:, 1].max() + vis_points[:, 1].min()) * 0.5
        mid_z = (vis_points[:, 2].max() + vis_points[:, 2].min()) * 0.5
        
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
        
        plt.tight_layout()
        point_cloud_file = OUTPUT_DIR / f"{out_prefix}_point_cloud_3d.png"
        plt.savefig(point_cloud_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualized {len(vis_points)} points from the 3D reconstruction")
    else:
        print("No points to visualize")
        point_cloud_file = None

    # Prepare artifacts list
    artifacts = [
        {
            "description": "Input images visualization",
            "path": str(input_images_file.resolve())
        },
        {
            "description": "Depth and confidence maps",
            "path": str(depth_confidence_file.resolve())
        }
    ]

    if point_cloud_file is not None:
        artifacts.append({
            "description": "3D point cloud visualization",
            "path": str(point_cloud_file.resolve())
        })

    return {
        "message": f"Visualization completed: {len(combined_points) if len(combined_points) > 0 else 0} points from {len(images)} images",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_viser.py",
        "artifacts": artifacts
    }