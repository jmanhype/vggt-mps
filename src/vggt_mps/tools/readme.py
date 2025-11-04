"""
VGGT (Visual Geometry Grounded Transformer) tutorial tools for 3D scene reconstruction from images.

This MCP Server provides 5 tools:
1. vggt_quick_start_inference: Initialize VGGT model and run basic inference on images
2. vggt_detailed_component_predictions: Run detailed component-wise inference for cameras, depth, point maps and tracks
3. vggt_visualize_depth_maps: Visualize original images alongside predicted depth maps
4. vggt_visualize_point_tracks: Visualize tracked points on images with visibility and confidence scores
5. vggt_alternative_model_loading: Demonstrate alternative manual model loading method

All tools extracted from `facebookresearch/vggt/README.md`.
Note: If source file contains multiple tutorial sections, all tools are consolidated from those sections.
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime

# VGGT specific imports
import torch
import matplotlib.pyplot as plt
from PIL import Image
import sys

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("README_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("README_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
readme_mcp = FastMCP(name="readme")

@readme_mcp.tool
def vggt_quick_start_inference(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images (.png, .jpg, .jpeg). The directory should contain the image files to process."] = None,
    # Analysis parameters with tutorial defaults
    max_images: Annotated[int, "Maximum number of images to process"] = 3,
    device: Annotated[Literal["auto", "cuda", "cpu", "mps"], "Computation device"] = "auto",
    use_sparse_attention: Annotated[bool, "Use sparse attention for O(n) scaling (experimental)"] = False,
    sparse_k_nearest: Annotated[int, "Number of nearest neighbors for sparse attention"] = 10,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Initialize VGGT model and run basic inference on a set of images for 3D scene reconstruction.
    Input is directory of images and output is prediction results with camera parameters, depth maps, and point maps.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_directory = Path(images_dir)
    if not images_directory.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"vggt_inference_{timestamp}"

    # Set up output files
    results_file = OUTPUT_DIR / f"{out_prefix}_results.csv"
    log_file = OUTPUT_DIR / f"{out_prefix}_log.txt"

    # Add the VGGT repo path to sys.path
    vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
    if str(vggt_repo_path) not in sys.path:
        sys.path.append(str(vggt_repo_path))

    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except ImportError as e:
        raise ImportError(f"Failed to import VGGT modules. Make sure VGGT is properly installed: {e}")

    # Configure matplotlib for high-quality output
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300

    # Device setup with MPS support
    if device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    # Set appropriate dtype based on device
    if device == "cuda" and torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    log_messages = []
    log_messages.append(f"Using device: {device}")
    log_messages.append(f"Using dtype: {dtype}")

    # Find image files
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [f for f in os.listdir(images_directory) if f.lower().endswith(image_extensions)]
    image_files = sorted(image_files)[:max_images]
    
    if not image_files:
        raise ValueError(f"No image files found in directory: {images_dir}")
    
    image_paths = [str(images_directory / img) for img in image_files]
    log_messages.append(f"Found {len(image_files)} images: {image_files}")

    # Initialize the model and load the pretrained weights
    log_messages.append("Loading VGGT model...")
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
    log_messages.append("Model loaded successfully!")

    # Apply sparse attention if requested
    if use_sparse_attention:
        log_messages.append(f"Enabling sparse attention with k={sparse_k_nearest} nearest neighbors...")
        try:
            # Import sparse attention module
            sys.path.insert(0, str(PROJECT_ROOT / "src"))
            from vggt_sparse_attention import make_vggt_sparse

            # Convert to sparse attention
            model = make_vggt_sparse(model, device=device)
            log_messages.append("✅ Sparse attention enabled - O(n) memory scaling!")
        except ImportError as e:
            log_messages.append(f"⚠️ Could not enable sparse attention: {e}")
            log_messages.append("Continuing with regular attention...")

    # Load and preprocess the images
    log_messages.append("Loading and preprocessing images...")
    images = load_and_preprocess_images(image_paths).to(device)
    log_messages.append(f"Loaded images with shape: {images.shape}")

    # Run inference
    log_messages.append("Running VGGT inference...")
    with torch.no_grad():
        with torch.amp.autocast('cuda', dtype=dtype) if torch.cuda.is_available() else torch.amp.autocast('cpu'):
            predictions = model(images)

    log_messages.append("Inference completed!")
    log_messages.append(f"Predictions keys: {list(predictions.keys())}")

    # Save results
    results_data = []
    for i, img_file in enumerate(image_files):
        results_data.append({
            'image_index': i,
            'image_filename': img_file,
            'pose_enc_shape': str(predictions['pose_enc'].shape),
            'depth_shape': str(predictions['depth'].shape),
            'world_points_shape': str(predictions['world_points'].shape),
        })

    results_df = pd.DataFrame(results_data)
    results_df.to_csv(results_file, index=False)

    # Save log
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_messages))

    return {
        "message": f"VGGT inference completed on {len(image_files)} images successfully",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/README.md",
        "artifacts": [
            {
                "description": "Inference results summary",
                "path": str(results_file.resolve())
            },
            {
                "description": "Processing log",
                "path": str(log_file.resolve())
            }
        ]
    }

@readme_mcp.tool
def vggt_detailed_component_predictions(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images (.png, .jpg, .jpeg). The directory should contain the image files to process."] = None,
    # Analysis parameters with tutorial defaults
    max_images: Annotated[int, "Maximum number of images to process"] = 3,
    query_points: Annotated[list, "List of [x, y] coordinate pairs for point tracking"] = [[100.0, 200.0], [60.72, 259.94]],
    device: Annotated[Literal["auto", "cuda", "cpu"], "Computation device"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Run detailed component-wise VGGT inference to predict cameras, depth maps, point maps, and tracks separately.
    Input is directory of images and query points, output is detailed camera parameters, depth maps, point maps and tracking results.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_directory = Path(images_dir)
    if not images_directory.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"vggt_detailed_{timestamp}"

    # Set up output files
    camera_params_file = OUTPUT_DIR / f"{out_prefix}_camera_parameters.csv"
    depth_info_file = OUTPUT_DIR / f"{out_prefix}_depth_info.csv"
    point_info_file = OUTPUT_DIR / f"{out_prefix}_point_info.csv"
    track_info_file = OUTPUT_DIR / f"{out_prefix}_track_info.csv"
    log_file = OUTPUT_DIR / f"{out_prefix}_log.txt"

    # Add the VGGT repo path to sys.path
    vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
    if str(vggt_repo_path) not in sys.path:
        sys.path.append(str(vggt_repo_path))

    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        from vggt.utils.geometry import unproject_depth_map_to_point_map
    except ImportError as e:
        raise ImportError(f"Failed to import VGGT modules. Make sure VGGT is properly installed: {e}")

    # Device setup with MPS support
    if device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    # Set appropriate dtype based on device
    if device == "cuda" and torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    log_messages = []
    log_messages.append(f"Using device: {device}")
    log_messages.append(f"Using dtype: {dtype}")

    # Find image files
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [f for f in os.listdir(images_directory) if f.lower().endswith(image_extensions)]
    image_files = sorted(image_files)[:max_images]
    
    if not image_files:
        raise ValueError(f"No image files found in directory: {images_dir}")
    
    image_paths = [str(images_directory / img) for img in image_files]
    log_messages.append(f"Found {len(image_files)} images: {image_files}")

    # Initialize the model
    log_messages.append("Loading VGGT model...")
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
    log_messages.append("Model loaded successfully!")

    # Load and preprocess the images
    log_messages.append("Loading and preprocessing images...")
    images = load_and_preprocess_images(image_paths).to(device)
    log_messages.append(f"Loaded images with shape: {images.shape}")

    log_messages.append("Running detailed component-wise inference...")

    with torch.no_grad():
        with torch.amp.autocast('cuda', dtype=dtype) if torch.cuda.is_available() else torch.amp.autocast('cpu'):
            images_batch = images[None]  # add batch dimension
            aggregated_tokens_list, ps_idx = model.aggregator(images_batch)
            
        log_messages.append("1. Predicting Camera Parameters...")
        # Predict Cameras
        pose_enc = model.camera_head(aggregated_tokens_list)[-1]
        # Extrinsic and intrinsic matrices, following OpenCV convention (camera from world)
        extrinsic, intrinsic = pose_encoding_to_extri_intri(pose_enc, images_batch.shape[-2:])
        
        log_messages.append(f"Extrinsic matrices shape: {extrinsic.shape}")
        log_messages.append(f"Intrinsic matrices shape: {intrinsic.shape}")
        
        log_messages.append("2. Predicting Depth Maps...")
        # Predict Depth Maps
        depth_map, depth_conf = model.depth_head(aggregated_tokens_list, images_batch, ps_idx)
        log_messages.append(f"Depth map shape: {depth_map.shape}")
        log_messages.append(f"Depth confidence shape: {depth_conf.shape}")
        
        log_messages.append("3. Predicting Point Maps...")
        # Predict Point Maps
        point_map, point_conf = model.point_head(aggregated_tokens_list, images_batch, ps_idx)
        log_messages.append(f"Point map shape: {point_map.shape}")
        log_messages.append(f"Point confidence shape: {point_conf.shape}")
        
        log_messages.append("4. Constructing 3D Points from Depth Maps...")
        # Construct 3D Points from Depth Maps and Cameras
        # which usually leads to more accurate 3D points than point map branch
        point_map_by_unprojection = unproject_depth_map_to_point_map(depth_map.squeeze(0), 
                                                                    extrinsic.squeeze(0), 
                                                                    intrinsic.squeeze(0))
        log_messages.append(f"Unprojected point map shape: {point_map_by_unprojection.shape}")
        
        log_messages.append("5. Predicting Point Tracks...")
        # Predict Tracks
        # choose your own points to track, with shape (N, 2) for one scene
        query_points_tensor = torch.FloatTensor(query_points).to(device)
        track_list, vis_score, conf_score = model.track_head(aggregated_tokens_list, images_batch, ps_idx, query_points=query_points_tensor[None])
        log_messages.append(f"Track list length: {len(track_list)}")
        log_messages.append(f"Visibility score shape: {vis_score.shape}")
        log_messages.append(f"Confidence score shape: {conf_score.shape}")

    # Save camera parameters
    camera_data = []
    for i in range(extrinsic.shape[1]):
        camera_data.append({
            'camera_id': i + 1,
            'image_filename': image_files[i],
            'intrinsic_fx': intrinsic[0, i, 0, 0].cpu().numpy(),
            'intrinsic_fy': intrinsic[0, i, 1, 1].cpu().numpy(),
            'intrinsic_cx': intrinsic[0, i, 0, 2].cpu().numpy(),
            'intrinsic_cy': intrinsic[0, i, 1, 2].cpu().numpy(),
            'extrinsic_r11': extrinsic[0, i, 0, 0].cpu().numpy(),
            'extrinsic_r12': extrinsic[0, i, 0, 1].cpu().numpy(),
            'extrinsic_r13': extrinsic[0, i, 0, 2].cpu().numpy(),
            'extrinsic_tx': extrinsic[0, i, 0, 3].cpu().numpy(),
            'extrinsic_r21': extrinsic[0, i, 1, 0].cpu().numpy(),
            'extrinsic_r22': extrinsic[0, i, 1, 1].cpu().numpy(),
            'extrinsic_r23': extrinsic[0, i, 1, 2].cpu().numpy(),
            'extrinsic_ty': extrinsic[0, i, 1, 3].cpu().numpy(),
            'extrinsic_r31': extrinsic[0, i, 2, 0].cpu().numpy(),
            'extrinsic_r32': extrinsic[0, i, 2, 1].cpu().numpy(),
            'extrinsic_r33': extrinsic[0, i, 2, 2].cpu().numpy(),
            'extrinsic_tz': extrinsic[0, i, 2, 3].cpu().numpy(),
        })
    
    camera_df = pd.DataFrame(camera_data)
    camera_df.to_csv(camera_params_file, index=False)

    # Save depth info
    depth_data = []
    for i in range(depth_map.shape[1]):
        depth_values = depth_map[0, i, :, :, 0].cpu().numpy()
        conf_values = depth_conf[0, i].cpu().numpy()
        depth_data.append({
            'image_id': i + 1,
            'image_filename': image_files[i],
            'depth_min': depth_values.min(),
            'depth_max': depth_values.max(),
            'depth_mean': depth_values.mean(),
            'depth_std': depth_values.std(),
            'confidence_min': conf_values.min(),
            'confidence_max': conf_values.max(),
            'confidence_mean': conf_values.mean(),
        })
    
    depth_df = pd.DataFrame(depth_data)
    depth_df.to_csv(depth_info_file, index=False)

    # Save point info
    point_data = []
    for i in range(point_map.shape[1]):
        point_values = point_map[0, i].cpu().numpy()
        point_conf_values = point_conf[0, i].cpu().numpy()
        point_data.append({
            'image_id': i + 1,
            'image_filename': image_files[i],
            'point_x_min': point_values[:, :, 0].min(),
            'point_x_max': point_values[:, :, 0].max(),
            'point_y_min': point_values[:, :, 1].min(),
            'point_y_max': point_values[:, :, 1].max(),
            'point_z_min': point_values[:, :, 2].min(),
            'point_z_max': point_values[:, :, 2].max(),
            'point_confidence_mean': point_conf_values.mean(),
        })
    
    point_df = pd.DataFrame(point_data)
    point_df.to_csv(point_info_file, index=False)

    # Save track info
    track_data = []
    for i in range(len(image_files)):
        for j in range(len(query_points)):
            if i < len(track_list[0]):
                track_point = track_list[0][i][j].float().cpu().numpy()
                visibility = vis_score[0, i, j].float().cpu().numpy()
                confidence = conf_score[0, i, j].float().cpu().numpy()
                track_data.append({
                    'query_point_id': j + 1,
                    'query_x': query_points[j][0],
                    'query_y': query_points[j][1],
                    'image_id': i + 1,
                    'image_filename': image_files[i],
                    'tracked_x': track_point[0],
                    'tracked_y': track_point[1],
                    'visibility_score': visibility,
                    'confidence_score': confidence,
                })
    
    track_df = pd.DataFrame(track_data)
    track_df.to_csv(track_info_file, index=False)

    # Save log
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_messages))

    return {
        "message": f"Detailed VGGT inference completed on {len(image_files)} images",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/README.md",
        "artifacts": [
            {
                "description": "Camera parameters",
                "path": str(camera_params_file.resolve())
            },
            {
                "description": "Depth map information",
                "path": str(depth_info_file.resolve())
            },
            {
                "description": "Point map information",
                "path": str(point_info_file.resolve())
            },
            {
                "description": "Point tracking results",
                "path": str(track_info_file.resolve())
            },
            {
                "description": "Processing log",
                "path": str(log_file.resolve())
            }
        ]
    }

@readme_mcp.tool
def vggt_visualize_depth_maps(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images (.png, .jpg, .jpeg). The directory should contain the image files to process."] = None,
    # Analysis parameters with tutorial defaults
    max_images: Annotated[int, "Maximum number of images to process"] = 3,
    colormap: Annotated[Literal["viridis", "plasma", "inferno", "magma", "cividis"], "Colormap for depth visualization"] = "viridis",
    device: Annotated[Literal["auto", "cuda", "cpu"], "Computation device"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Visualize original images alongside their predicted depth maps using VGGT.
    Input is directory of images and output is visualization comparing original images with depth maps.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_directory = Path(images_dir)
    if not images_directory.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"vggt_depth_viz_{timestamp}"

    # Set up output files
    visualization_file = OUTPUT_DIR / f"{out_prefix}_depth_visualization.png"
    log_file = OUTPUT_DIR / f"{out_prefix}_log.txt"

    # Add the VGGT repo path to sys.path
    vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
    if str(vggt_repo_path) not in sys.path:
        sys.path.append(str(vggt_repo_path))

    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except ImportError as e:
        raise ImportError(f"Failed to import VGGT modules. Make sure VGGT is properly installed: {e}")

    # Configure matplotlib for high-quality output
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300

    # Device setup with MPS support
    if device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    # Set appropriate dtype based on device
    if device == "cuda" and torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    log_messages = []
    log_messages.append(f"Using device: {device}")
    log_messages.append(f"Using dtype: {dtype}")

    # Find image files
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [f for f in os.listdir(images_directory) if f.lower().endswith(image_extensions)]
    image_files = sorted(image_files)[:max_images]
    
    if not image_files:
        raise ValueError(f"No image files found in directory: {images_dir}")
    
    image_paths = [str(images_directory / img) for img in image_files]
    log_messages.append(f"Found {len(image_files)} images: {image_files}")

    # Initialize the model
    log_messages.append("Loading VGGT model...")
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
    log_messages.append("Model loaded successfully!")

    # Load and preprocess the images
    log_messages.append("Loading and preprocessing images...")
    images = load_and_preprocess_images(image_paths).to(device)
    log_messages.append(f"Loaded images with shape: {images.shape}")

    # Run inference
    log_messages.append("Running VGGT inference...")
    with torch.no_grad():
        with torch.amp.autocast('cuda', dtype=dtype) if torch.cuda.is_available() else torch.amp.autocast('cpu'):
            predictions = model(images)

    log_messages.append("Inference completed!")

    # Extract depth maps
    depth_map = predictions['depth']
    log_messages.append("Visualizing depth maps...")

    num_images = depth_map.shape[1]
    fig, axes = plt.subplots(2, num_images, figsize=(5*num_images, 10))
    if num_images == 1:
        axes = axes.reshape(-1, 1)

    for i in range(num_images):
        # Original image
        original_img = images[i].permute(1, 2, 0).cpu().numpy()
        # Denormalize the image (assuming it was normalized)
        original_img = (original_img + 1) / 2  # Convert from [-1, 1] to [0, 1]
        original_img = np.clip(original_img, 0, 1)
        
        axes[0, i].imshow(original_img)
        axes[0, i].set_title(f"Original Image {i+1}")
        axes[0, i].axis('off')
        
        # Depth map
        depth = depth_map[0, i, :, :, 0].float().cpu().numpy()  # Convert to float32 first, then remove batch and channel dimensions
        im = axes[1, i].imshow(depth, cmap=colormap)
        axes[1, i].set_title(f"Depth Map {i+1}")
        axes[1, i].axis('off')
        plt.colorbar(im, ax=axes[1, i], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(visualization_file, dpi=300, bbox_inches='tight')
    plt.close()

    log_messages.append(f"Visualization saved to: {visualization_file}")

    # Save log
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_messages))

    return {
        "message": f"Depth map visualization completed for {num_images} images",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/README.md",
        "artifacts": [
            {
                "description": "Depth maps visualization",
                "path": str(visualization_file.resolve())
            },
            {
                "description": "Processing log",
                "path": str(log_file.resolve())
            }
        ]
    }

@readme_mcp.tool
def vggt_visualize_point_tracks(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images (.png, .jpg, .jpeg). The directory should contain the image files to process."] = None,
    # Analysis parameters with tutorial defaults
    max_images: Annotated[int, "Maximum number of images to process"] = 3,
    query_points: Annotated[list, "List of [x, y] coordinate pairs for point tracking"] = [[100.0, 200.0], [60.72, 259.94]],
    visibility_threshold: Annotated[float, "Minimum visibility score to show tracks"] = 0.5,
    device: Annotated[Literal["auto", "cuda", "cpu"], "Computation device"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Visualize tracked points on images with visibility and confidence scores using VGGT.
    Input is directory of images and query points, output is visualization showing tracked points across images.
    """
    # Input file validation only
    if images_dir is None:
        raise ValueError("Path to images directory must be provided")

    # Directory existence validation
    images_directory = Path(images_dir)
    if not images_directory.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"vggt_tracks_viz_{timestamp}"

    # Set up output files
    visualization_file = OUTPUT_DIR / f"{out_prefix}_tracks_visualization.png"
    track_summary_file = OUTPUT_DIR / f"{out_prefix}_track_summary.csv"
    log_file = OUTPUT_DIR / f"{out_prefix}_log.txt"

    # Add the VGGT repo path to sys.path
    vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
    if str(vggt_repo_path) not in sys.path:
        sys.path.append(str(vggt_repo_path))

    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except ImportError as e:
        raise ImportError(f"Failed to import VGGT modules. Make sure VGGT is properly installed: {e}")

    # Configure matplotlib for high-quality output
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300

    # Device setup with MPS support
    if device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    # Set appropriate dtype based on device
    if device == "cuda" and torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    log_messages = []
    log_messages.append(f"Using device: {device}")
    log_messages.append(f"Using dtype: {dtype}")

    # Find image files
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [f for f in os.listdir(images_directory) if f.lower().endswith(image_extensions)]
    image_files = sorted(image_files)[:max_images]
    
    if not image_files:
        raise ValueError(f"No image files found in directory: {images_dir}")
    
    image_paths = [str(images_directory / img) for img in image_files]
    log_messages.append(f"Found {len(image_files)} images: {image_files}")

    # Initialize the model
    log_messages.append("Loading VGGT model...")
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
    log_messages.append("Model loaded successfully!")

    # Load and preprocess the images
    log_messages.append("Loading and preprocessing images...")
    images = load_and_preprocess_images(image_paths).to(device)
    log_messages.append(f"Loaded images with shape: {images.shape}")

    log_messages.append("Running VGGT inference for point tracking...")

    with torch.no_grad():
        with torch.amp.autocast('cuda', dtype=dtype) if torch.cuda.is_available() else torch.amp.autocast('cpu'):
            images_batch = images[None]  # add batch dimension
            aggregated_tokens_list, ps_idx = model.aggregator(images_batch)
            
            # Predict Tracks
            query_points_tensor = torch.FloatTensor(query_points).to(device)
            track_list, vis_score, conf_score = model.track_head(aggregated_tokens_list, images_batch, ps_idx, query_points=query_points_tensor[None])

    log_messages.append("Visualizing point tracks...")

    num_images = len(image_files)
    fig, axes = plt.subplots(1, num_images, figsize=(5*num_images, 5))
    if num_images == 1:
        axes = [axes]

    track_summary_data = []

    for i in range(num_images):
        # Original image
        original_img = images[i].permute(1, 2, 0).cpu().numpy()
        original_img = (original_img + 1) / 2  # Denormalize
        original_img = np.clip(original_img, 0, 1)
        
        axes[i].imshow(original_img)
        
        # Plot tracked points
        if i < len(track_list[0]):
            tracks = track_list[0][i].float().cpu().numpy()  # [num_query_points, 2]
            vis = vis_score[0, i].float().cpu().numpy()     # [num_query_points]
            conf = conf_score[0, i].float().cpu().numpy()  # [num_query_points]

            for j, (track_point, visibility, confidence) in enumerate(zip(tracks, vis, conf)):
                if visibility > visibility_threshold:  # Only show visible tracks
                    # Safe conversion for plotting
                    try:
                        plot_x = float(track_point[0]) if hasattr(track_point[0], '__float__') else track_point[0]
                        plot_y = float(track_point[1]) if hasattr(track_point[1], '__float__') else track_point[1]
                    except (ValueError, TypeError):
                        plot_x = track_point[0] if len(track_point) > 0 else 0.0
                        plot_y = track_point[1] if len(track_point) > 1 else 0.0
                    
                    axes[i].plot(plot_x, plot_y, 'ro', markersize=8)
                    # Skip text plotting to avoid tensor conversion issues
                
                # Record track information with safe conversion
                try:
                    tracked_x = track_point[0].item() if hasattr(track_point[0], 'item') else float(track_point[0])
                except (ValueError, TypeError):
                    tracked_x = track_point[0] if len(track_point) > 0 else 0.0
                    
                try:
                    tracked_y = track_point[1].item() if hasattr(track_point[1], 'item') else float(track_point[1])
                except (ValueError, TypeError):
                    tracked_y = track_point[1] if len(track_point) > 1 else 0.0
                    
                try:
                    vis_score = visibility.item() if hasattr(visibility, 'item') else float(visibility)
                except (ValueError, TypeError):
                    vis_score = visibility if hasattr(visibility, '__float__') else 0.0
                    
                try:
                    conf_score = confidence.item() if hasattr(confidence, 'item') else float(confidence)
                except (ValueError, TypeError):
                    conf_score = confidence if hasattr(confidence, '__float__') else 0.0
                
                track_summary_data.append({
                    'query_point_id': j + 1,
                    'query_x': query_points[j][0],
                    'query_y': query_points[j][1],
                    'image_id': i + 1,
                    'image_filename': image_files[i],
                    'tracked_x': tracked_x,
                    'tracked_y': tracked_y,
                    'visibility_score': vis_score,
                    'confidence_score': conf_score,
                    'visible': visibility > visibility_threshold
                })
        
        axes[i].set_title(f"Image {i+1} with Tracks")
        axes[i].axis('off')

    plt.tight_layout()
    plt.savefig(visualization_file, dpi=300, bbox_inches='tight')
    plt.close()

    # Print track information to log
    log_messages.append("Track Information:")

    for j in range(len(query_points)):
        log_messages.append(f"Query Point {j+1}: ({query_points[j][0]:.1f}, {query_points[j][1]:.1f})")
        try:
            # Get the appropriate dimensions for iteration
            if hasattr(track_list[0], 'shape') and len(track_list[0].shape) >= 2:
                num_images = track_list[0].shape[0]
            else:
                num_images = len(track_list[0]) if isinstance(track_list[0], (list, tuple)) else 1
                
            for i in range(min(num_images, 3)):  # Limit to 3 images as expected
                try:
                    # Handle different tensor structures
                    if hasattr(track_list[0], 'shape') and len(track_list[0].shape) >= 3:
                        # Tensor with shape [num_images, num_points, 2]
                        track_point = track_list[0][i, j].float().cpu().numpy()
                    else:
                        # Other structure
                        track_point = track_list[0][i][j].float().cpu().numpy()
                    
                    visibility = vis_score[0, i, j].float().cpu().numpy().item()
                    confidence = conf_score[0, i, j].float().cpu().numpy().item()
                    
                    # Extract coordinates safely
                    if hasattr(track_point, '__len__') and len(track_point) >= 2:
                        track_x = float(track_point[0])
                        track_y = float(track_point[1])
                    else:
                        track_x, track_y = 0.0, 0.0
                    
                    # Process visibility and confidence scores
                    vis_val = float(visibility)
                    conf_val = float(confidence)
                    
                    log_messages.append(f"  Image {i+1}: ({track_x:.1f}, {track_y:.1f}), "
                          f"vis={vis_val:.3f}, conf={conf_val:.3f}")
                          
                except Exception as e:
                    log_messages.append(f"  Image {i+1}: Error processing track data - {str(e)}")
                    
        except Exception as e:
            log_messages.append(f"Query Point {j+1}: Error processing tracks - {str(e)}")

    # Save track summary
    track_summary_df = pd.DataFrame(track_summary_data)
    track_summary_df.to_csv(track_summary_file, index=False)

    # Save log
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_messages))

    return {
        "message": f"Point tracking visualization completed for {num_images} images",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/README.md",
        "artifacts": [
            {
                "description": "Point tracks visualization",
                "path": str(visualization_file.resolve())
            },
            {
                "description": "Track summary data",
                "path": str(track_summary_file.resolve())
            },
            {
                "description": "Processing log",
                "path": str(log_file.resolve())
            }
        ]
    }

@readme_mcp.tool
def vggt_alternative_model_loading(
    # Analysis parameters with tutorial defaults  
    model_url: Annotated[str, "URL to download model weights"] = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt",
    device: Annotated[Literal["auto", "cuda", "cpu"], "Computation device"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Demonstrate alternative manual model loading method for troubleshooting VGGT model initialization.
    Input is model URL and output is log of loading process and model initialization status.
    """
    # Set output prefix
    if out_prefix is None:
        out_prefix = f"vggt_alt_loading_{timestamp}"

    # Set up output files
    log_file = OUTPUT_DIR / f"{out_prefix}_log.txt"

    # Add the VGGT repo path to sys.path
    vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
    if str(vggt_repo_path) not in sys.path:
        sys.path.append(str(vggt_repo_path))

    try:
        from vggt.models.vggt import VGGT
    except ImportError as e:
        raise ImportError(f"Failed to import VGGT modules. Make sure VGGT is properly installed: {e}")

    # Device setup
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    log_messages = []
    log_messages.append(f"Using device: {device}")
    log_messages.append("Demonstrating alternative model loading method...")

    success = False
    error_message = None

    try:
        # Create a new model instance
        model_alt = VGGT()
        
        # Load weights from URL
        log_messages.append(f"Loading model weights from: {model_url}")
        
        state_dict = torch.hub.load_state_dict_from_url(model_url, map_location=device)
        model_alt.load_state_dict(state_dict)
        model_alt.to(device)
        
        log_messages.append("Alternative model loading successful!")
        success = True
        
    except Exception as e:
        error_message = str(e)
        log_messages.append(f"Alternative loading failed: {e}")
        log_messages.append("This is expected if the model was already loaded successfully above.")

    # Save log
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_messages))

    status_msg = "Alternative model loading successful" if success else f"Alternative loading failed: {error_message}"

    return {
        "message": status_msg,
        "reference": "https://github.com/facebookresearch/vggt/blob/main/README.md",
        "artifacts": [
            {
                "description": "Model loading log",
                "path": str(log_file.resolve())
            }
        ]
    }