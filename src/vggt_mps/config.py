"""
VGGT-MPS Configuration
Centralized configuration management for the VGGT-MPS package.

This module provides:
- Device detection and configuration (MPS, CUDA, CPU)
- Model paths and metadata
- Sparse attention settings
- Camera and processing parameters
- Web interface configuration
- Environment variable integration

Example:
    >>> from vggt_mps.config import DEVICE, get_model_path
    >>> print(f"Using device: {DEVICE}")
    >>> model_path = get_model_path()
    >>> if is_model_available():
    ...     print("Model is ready")
"""

import os
from pathlib import Path
from typing import Optional
import torch

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"
REPO_DIR = PROJECT_ROOT / "repo"

# Create directories if they don't exist
for dir_path in [DATA_DIR, OUTPUT_DIR, MODEL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Model configuration
MODEL_CONFIG = {
    "name": "VGGT-1B",
    "huggingface_id": "facebook/VGGT-1B",
    "local_path": MODEL_DIR / "vggt_model.pt",
    "model_size": "5GB",
    "parameters": "1B",
}

# Device configuration
def get_device() -> torch.device:
    """Get the best available device for computation.

    Checks device availability in order of preference:
    1. MPS (Metal Performance Shaders) for Apple Silicon
    2. CUDA for NVIDIA GPUs
    3. CPU as fallback

    Returns:
        torch.device: The optimal available device

    Example:
        >>> device = get_device()
        >>> print(f"Using {device}")
        Using mps
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

DEVICE = get_device()

# Sparse attention configuration
SPARSE_CONFIG = {
    "enabled": True,
    "covisibility_threshold": 0.7,
    "memory_savings": 100,  # 100x for 1000 images
}

# Camera parameters (simplified)
CAMERA_CONFIG = {
    "fx": 500,
    "fy": 500,
    "image_width": 640,
    "image_height": 480,
}

# Processing configuration
PROCESSING_CONFIG = {
    "batch_size": 4,
    "max_images": 100,
    "point_cloud_step": 10,  # Downsampling for visualization
    "max_viz_points": 5000,  # Max points for 3D visualization
}

# Web interface configuration
WEB_CONFIG = {
    "default_port": 7860,
    "share": False,
    "theme": "dark",
}

# Test data configuration
TEST_DATA = {
    "kitchen_path": REPO_DIR / "vggt" / "examples" / "kitchen" / "images",
    "test_images": DATA_DIR / "test_images",
}

# Export formats
EXPORT_FORMATS = {
    "ply": {"extension": ".ply", "binary": False},
    "obj": {"extension": ".obj", "binary": False},
    "glb": {"extension": ".glb", "binary": True},
}

# Logging configuration
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Environment variables override
def load_from_env() -> None:
    """Load configuration overrides from environment variables.

    Supported environment variables:
    - USE_SPARSE_ATTENTION: Enable/disable sparse attention (true/false)
    - COVISIBILITY_THRESHOLD: Threshold for covisibility detection (0.0-1.0)
    - WEB_PORT: Port for web interface (integer)
    - WEB_SHARE: Enable public sharing (true/false)

    Note:
        This function modifies global configuration dictionaries.
        It is called automatically on module import.

    Example:
        >>> import os
        >>> os.environ['WEB_PORT'] = '8080'
        >>> load_from_env()
    """
    global SPARSE_CONFIG, WEB_CONFIG

    if os.getenv("USE_SPARSE_ATTENTION"):
        SPARSE_CONFIG["enabled"] = os.getenv("USE_SPARSE_ATTENTION").lower() == "true"

    if os.getenv("COVISIBILITY_THRESHOLD"):
        SPARSE_CONFIG["covisibility_threshold"] = float(os.getenv("COVISIBILITY_THRESHOLD"))

    if os.getenv("WEB_PORT"):
        WEB_CONFIG["default_port"] = int(os.getenv("WEB_PORT"))

    if os.getenv("WEB_SHARE"):
        WEB_CONFIG["share"] = os.getenv("WEB_SHARE").lower() == "true"

# Load environment variables on import
load_from_env()

# Utility functions
def get_model_path() -> Path:
    """Get the path to the VGGT model weights.

    Checks multiple locations in order:
    1. Local models directory (models/vggt_model.pt)
    2. Repository directory (repo/vggt/vggt_model.pt)
    3. Returns expected path even if file doesn't exist

    Returns:
        Path: Path to the model file (may not exist yet)

    Example:
        >>> model_path = get_model_path()
        >>> if model_path.exists():
        ...     print(f"Model found at {model_path}")
    """
    # Check local path first
    if MODEL_CONFIG["local_path"].exists():
        return MODEL_CONFIG["local_path"]

    # Check repo directory
    repo_model = REPO_DIR / "vggt" / "vggt_model.pt"
    if repo_model.exists():
        return repo_model

    return MODEL_CONFIG["local_path"]  # Return expected path even if not exists

def is_model_available() -> bool:
    """Check if the VGGT model weights are available locally.

    Returns:
        bool: True if model file exists, False otherwise

    Example:
        >>> if is_model_available():
        ...     print("Model ready to use")
        ... else:
        ...     print("Run 'vggt download' to get the model")
    """
    return get_model_path().exists()