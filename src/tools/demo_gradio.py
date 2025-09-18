"""
VGGT Gradio Interface Tools for 3D Scene Reconstruction.

This MCP Server provides 3 tools:
1. vggt_extract_video_frames: Extract frames from video files for 3D reconstruction input
2. vggt_process_images: Process images through VGGT model for 3D reconstruction
3. vggt_create_3d_scene: Create 3D scene visualization from VGGT predictions

All tools extracted from `facebookresearch/vggt/demo_gradio.py`.
Note: Tools consolidate the main analytical workflows from the Gradio interface demo.
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
import shutil
import cv2
import glob
import torch
import gc
import time
import json

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("DEMO_GRADIO_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("DEMO_GRADIO_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
demo_gradio_mcp = FastMCP(name="demo_gradio")

@demo_gradio_mcp.tool
def vggt_extract_video_frames(
    # Primary data inputs
    video_path: Annotated[str | None, "Path to input video file with extension .mp4, .avi, .mov, etc."] = None,
    # Analysis parameters with tutorial defaults
    frame_interval_seconds: Annotated[float, "Time interval between extracted frames in seconds"] = 1.0,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Extract frames from video files at specified intervals for 3D reconstruction input.
    Input is video file and output is directory of extracted frame images and frame count summary.
    """
    # Input file validation
    if video_path is None:
        raise ValueError("Path to input video file must be provided")

    # File existence validation
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Input video file not found: {video_path}")

    # Setup output directory
    if out_prefix is None:
        out_prefix = f"video_frames_{timestamp}"

    output_dir = OUTPUT_DIR / out_prefix
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract frames using exact tutorial logic
    vs = cv2.VideoCapture(str(video_file))
    fps = vs.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_interval_seconds)  # frames to skip between extractions

    count = 0
    video_frame_num = 0
    image_paths = []

    while True:
        gotit, frame = vs.read()
        if not gotit:
            break
        count += 1
        if count % frame_interval == 0:
            image_path = output_dir / f"{video_frame_num:06}.png"
            cv2.imwrite(str(image_path), frame)
            image_paths.append(str(image_path))
            video_frame_num += 1

    vs.release()

    # Create summary CSV
    summary_data = {
        'frame_number': range(len(image_paths)),
        'frame_path': image_paths,
        'original_frame_index': [i * frame_interval for i in range(len(image_paths))]
    }

    summary_file = output_dir / f"{out_prefix}_frame_summary.csv"
    pd.DataFrame(summary_data).to_csv(summary_file, index=False)

    return {
        "message": f"Extracted {len(image_paths)} frames from video successfully",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_gradio.py",
        "artifacts": [
            {
                "description": "Frame extraction summary",
                "path": str(summary_file.resolve())
            },
            {
                "description": "Extracted frames directory",
                "path": str(output_dir.resolve())
            }
        ]
    }


@demo_gradio_mcp.tool
def vggt_process_images(
    # Primary data inputs
    images_dir: Annotated[str | None, "Path to directory containing input images for 3D reconstruction"] = None,
    # Analysis parameters with tutorial defaults
    device: Annotated[Literal["cuda", "cpu", "mps", "auto"], "Computing device to use"] = "auto",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Process images through VGGT model to generate 3D reconstruction predictions including depth maps and camera poses.
    Input is directory of images and output is 3D reconstruction predictions with depth maps, confidence maps, and camera parameters.
    """
    # Input directory validation
    if images_dir is None:
        raise ValueError("Path to input images directory must be provided")

    # Directory existence validation
    images_directory = Path(images_dir)
    if not images_directory.exists():
        raise FileNotFoundError(f"Input images directory not found: {images_dir}")

    # Import VGGT modules after path validation
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        from vggt.utils.geometry import unproject_depth_map_to_point_map
    except ImportError as e:
        raise ImportError(f"VGGT modules not available: {e}")

    # Setup device with MPS support for Apple Silicon
    if device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
            print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
        elif torch.cuda.is_available():
            device = "cuda"
            print("🔥 Using CUDA GPU")
        else:
            device = "cpu"
            print("💻 Using CPU")

    # Validate device availability
    if device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA is not available. Check your environment.")
    if device == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS is not available. Check your environment.")

    # Setup output directory
    if out_prefix is None:
        out_prefix = f"vggt_processing_{timestamp}"

    output_dir = OUTPUT_DIR / out_prefix
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing images from {images_directory}")
    print(f"Using device: {device}")

    # Load VGGT model using exact tutorial logic
    print("Loading VGGT model...")
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

    # Load and preprocess images using exact tutorial logic
    image_names = glob.glob(os.path.join(str(images_directory), "*"))
    image_names = sorted(image_names)
    print(f"Found {len(image_names)} images")
    if len(image_names) == 0:
        raise ValueError("No images found. Check your upload.")

    images = load_and_preprocess_images(image_names).to(device)
    print(f"Preprocessed images shape: {images.shape}")

    # Run inference with MPS support
    print("Running inference...")
    if device == "cuda":
        dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    elif device == "mps":
        dtype = torch.float32  # MPS works best with float32
    else:
        dtype = torch.float32

    with torch.no_grad():
        # Only use autocast for CUDA, not for MPS
        if device == "cuda":
            with torch.cuda.amp.autocast(dtype=dtype, enabled=True):
                predictions = model(images)
        else:
            predictions = model(images)

    # Convert pose encoding to extrinsic and intrinsic matrices
    print("Converting pose encoding to extrinsic and intrinsic matrices...")
    extrinsic, intrinsic = pose_encoding_to_extri_intri(predictions["pose_enc"], images.shape[-2:])
    predictions["extrinsic"] = extrinsic
    predictions["intrinsic"] = intrinsic

    # Convert tensors to numpy using exact tutorial logic
    for key in predictions.keys():
        if isinstance(predictions[key], torch.Tensor):
            predictions[key] = predictions[key].cpu().numpy().squeeze(0)  # remove batch dimension
    predictions['pose_enc_list'] = None  # remove pose_enc_list

    # Generate world points from depth map using exact tutorial logic
    print("Computing world points from depth map...")
    depth_map = predictions["depth"]  # (S, H, W, 1)
    world_points = unproject_depth_map_to_point_map(depth_map, predictions["extrinsic"], predictions["intrinsic"])
    predictions["world_points_from_depth"] = world_points

    # Save predictions using exact tutorial logic
    prediction_save_path = output_dir / "predictions.npz"
    np.savez(str(prediction_save_path), **predictions)

    # Create processing summary
    summary_data = {
        'num_images': [len(image_names)],
        'image_resolution': [f"{images.shape[-2]}x{images.shape[-1]}"],
        'device_used': [device],
        'dtype_used': [str(dtype)],
        'processing_timestamp': [timestamp]
    }

    summary_file = output_dir / f"{out_prefix}_processing_summary.csv"
    pd.DataFrame(summary_data).to_csv(summary_file, index=False)

    # Clean up using exact tutorial logic
    torch.cuda.empty_cache()

    return {
        "message": f"Processed {len(image_names)} images successfully",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_gradio.py",
        "artifacts": [
            {
                "description": "VGGT predictions (NPZ format)",
                "path": str(prediction_save_path.resolve())
            },
            {
                "description": "Processing summary",
                "path": str(summary_file.resolve())
            }
        ]
    }


@demo_gradio_mcp.tool
def vggt_create_3d_scene(
    # Primary data inputs
    predictions_path: Annotated[str | None, "Path to NPZ file containing VGGT predictions from vggt_process_images"] = None,
    # Analysis parameters with tutorial defaults
    conf_thres: Annotated[float, "Confidence threshold percentage for filtering points"] = 50.0,
    frame_filter: Annotated[str, "Frame filter specification"] = "All",
    mask_black_bg: Annotated[bool, "Mask out black background pixels"] = False,
    mask_white_bg: Annotated[bool, "Mask out white background pixels"] = False,
    show_cam: Annotated[bool, "Include camera visualization"] = True,
    mask_sky: Annotated[bool, "Apply sky segmentation mask"] = False,
    prediction_mode: Annotated[Literal["Depthmap and Camera Branch", "Pointmap Branch"], "Prediction mode selector"] = "Depthmap and Camera Branch",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Create 3D scene visualization from VGGT predictions and export as GLB file for 3D viewing.
    Input is NPZ predictions file and visualization parameters and output is GLB 3D scene file and visualization summary.
    """
    # Input file validation
    if predictions_path is None:
        raise ValueError("Path to NPZ predictions file must be provided")

    # File existence validation
    predictions_file = Path(predictions_path)
    if not predictions_file.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    # Import visual utilities after path validation
    try:
        # Add VGGT repo path to sys.path for visual_util import
        import sys
        vggt_repo_path = PROJECT_ROOT / "repo" / "vggt"
        if str(vggt_repo_path) not in sys.path:
            sys.path.insert(0, str(vggt_repo_path))

        from visual_util import predictions_to_glb
    except ImportError as e:
        raise ImportError(f"Visual utilities not available: {e}")

    # Setup output directory
    if out_prefix is None:
        out_prefix = f"vggt_3d_scene_{timestamp}"

    output_dir = OUTPUT_DIR / out_prefix
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load predictions using exact tutorial logic
    key_list = [
        "pose_enc",
        "depth",
        "depth_conf",
        "world_points",
        "world_points_conf",
        "images",
        "extrinsic",
        "intrinsic",
        "world_points_from_depth",
    ]

    loaded = np.load(str(predictions_file))
    predictions = {key: np.array(loaded[key]) for key in key_list}

    # Build GLB file name using exact tutorial logic
    glbfile = output_dir / (
        f"glbscene_{conf_thres}_{frame_filter.replace('.', '_').replace(':', '').replace(' ', '_')}_"
        f"maskb{mask_black_bg}_maskw{mask_white_bg}_cam{show_cam}_sky{mask_sky}_"
        f"pred{prediction_mode.replace(' ', '_')}.glb"
    )

    # Convert predictions to GLB using exact tutorial logic
    glbscene = predictions_to_glb(
        predictions,
        conf_thres=conf_thres,
        filter_by_frames=frame_filter,
        mask_black_bg=mask_black_bg,
        mask_white_bg=mask_white_bg,
        show_cam=show_cam,
        mask_sky=mask_sky,
        target_dir=str(output_dir),
        prediction_mode=prediction_mode,
    )
    glbscene.export(file_obj=str(glbfile))

    # Create visualization summary
    summary_data = {
        'confidence_threshold': [conf_thres],
        'frame_filter': [frame_filter],
        'mask_black_bg': [mask_black_bg],
        'mask_white_bg': [mask_white_bg],
        'show_cam': [show_cam],
        'mask_sky': [mask_sky],
        'prediction_mode': [prediction_mode],
        'glb_file': [str(glbfile)],
        'creation_timestamp': [timestamp]
    }

    summary_file = output_dir / f"{out_prefix}_scene_summary.csv"
    pd.DataFrame(summary_data).to_csv(summary_file, index=False)

    # Clean up
    del predictions
    gc.collect()

    return {
        "message": "3D scene created successfully",
        "reference": "https://github.com/facebookresearch/vggt/blob/main/demo_gradio.py",
        "artifacts": [
            {
                "description": "3D scene GLB file",
                "path": str(glbfile.resolve())
            },
            {
                "description": "Scene creation summary",
                "path": str(summary_file.resolve())
            }
        ]
    }
