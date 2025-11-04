"""
VGGT-MPS Configuration
Centralized configuration management
"""

import os
from pathlib import Path
from typing import Optional
import torch

# Project paths
# File is in src/vggt_mps/config.py, so need 3 levels up to reach project root
# Path calculation: __file__ -> config.py in src/vggt_mps/
#   .parent -> src/vggt_mps/
#   .parent.parent -> src/
#   .parent.parent.parent -> project root
# This works for: pip install, editable install (pip install -e .), and direct execution
PROJECT_ROOT = Path(__file__).parent.parent.parent

SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"
REPO_DIR = PROJECT_ROOT / "repo"

# Validate path calculation - check for expected project markers
# This validation ensures PROJECT_ROOT works correctly across:
# 1. pip install (site-packages/vggt_mps/)
# 2. editable install (pip install -e .)
# 3. direct execution (python -m vggt_mps.*)
if not (PROJECT_ROOT / "src").exists() and not (PROJECT_ROOT / "pyproject.toml").exists():
    # Fallback for edge cases (e.g., installed package in site-packages)
    import warnings
    warnings.warn(
        f"PROJECT_ROOT calculation may be incorrect. "
        f"Expected 'src/' or 'pyproject.toml' at: {PROJECT_ROOT}. "
        f"Current __file__: {__file__}",
        RuntimeWarning
    )

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
    """
    Get the best available device.

    Returns:
        torch.device: MPS if available on Apple Silicon, CUDA if available,
                     otherwise CPU.
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
    """
    Load configuration from environment variables.

    Supported environment variables:
        USE_SPARSE_ATTENTION: Enable/disable sparse attention (true/false)
        COVISIBILITY_THRESHOLD: Threshold for covisibility detection (float)
        WEB_PORT: Port for web interface (int)
        WEB_SHARE: Enable public sharing for Gradio (true/false)
    """
    global SPARSE_CONFIG, WEB_CONFIG

    if os.getenv("USE_SPARSE_ATTENTION"):
        SPARSE_CONFIG["enabled"] = os.getenv("USE_SPARSE_ATTENTION").lower() == "true"

    if os.getenv("COVISIBILITY_THRESHOLD"):
        try:
            SPARSE_CONFIG["covisibility_threshold"] = float(os.getenv("COVISIBILITY_THRESHOLD"))
        except ValueError as e:
            print(f"⚠️ Invalid COVISIBILITY_THRESHOLD: {e}")

    if os.getenv("WEB_PORT"):
        try:
            WEB_CONFIG["default_port"] = int(os.getenv("WEB_PORT"))
        except ValueError as e:
            print(f"⚠️ Invalid WEB_PORT: {e}")

    if os.getenv("WEB_SHARE"):
        WEB_CONFIG["share"] = os.getenv("WEB_SHARE").lower() == "true"

# Load environment variables on import
load_from_env()

# Utility functions
def get_model_path() -> Path:
    """Get model path, checking multiple locations"""
    # Check local path first
    if MODEL_CONFIG["local_path"].exists():
        return MODEL_CONFIG["local_path"]

    # Check repo directory
    repo_model = REPO_DIR / "vggt" / "vggt_model.pt"
    if repo_model.exists():
        return repo_model

    return MODEL_CONFIG["local_path"]  # Return expected path even if not exists

def is_model_available() -> bool:
    """Check if model is available locally"""
    return get_model_path().exists()