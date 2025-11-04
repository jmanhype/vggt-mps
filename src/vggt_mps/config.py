"""
VGGT-MPS Configuration
Centralized configuration management
"""

import os
import shutil
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


def _migrate_legacy_model() -> None:
    """Move legacy model file into the canonical models/ directory."""
    target_path = MODEL_CONFIG["local_path"]
    if target_path.exists() or not LEGACY_MODEL_PATH.exists():
        return

    try:
        LEGACY_MODEL_PATH.replace(target_path)
    except OSError:
        shutil.copy2(LEGACY_MODEL_PATH, target_path)
        LEGACY_MODEL_PATH.unlink(missing_ok=True)


_migrate_legacy_model()

# Model configuration
MODEL_CONFIG = {
    "name": "VGGT-1B",
    "huggingface_id": "facebook/VGGT-1B",
    "local_path": MODEL_DIR / "vggt_model.pt",
    "model_size": "5GB",
    "parameters": "1B",
}
LEGACY_MODEL_PATH = REPO_DIR / "vggt" / "vggt_model.pt"

# Device configuration
def get_device() -> torch.device:
    """Get the best available device.

    Returns:
        torch.device: The best available device (mps > cuda > cpu)
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
    """Load configuration from environment variables.

    Overrides global configuration dictionaries based on environment variables:
    - USE_SPARSE_ATTENTION: Enable/disable sparse attention
    - COVISIBILITY_THRESHOLD: Set covisibility threshold
    - WEB_PORT: Set web interface port
    - WEB_SHARE: Enable/disable public sharing
    """
    global SPARSE_CONFIG, WEB_CONFIG

    if os.getenv("USE_SPARSE_ATTENTION"):
        SPARSE_CONFIG["enabled"] = os.getenv("USE_SPARSE_ATTENTION", "").lower() == "true"

    if os.getenv("COVISIBILITY_THRESHOLD"):
        SPARSE_CONFIG["covisibility_threshold"] = float(os.getenv("COVISIBILITY_THRESHOLD", "0.7"))

    if os.getenv("WEB_PORT"):
        WEB_CONFIG["default_port"] = int(os.getenv("WEB_PORT", "7860"))

    if os.getenv("WEB_SHARE"):
        WEB_CONFIG["share"] = os.getenv("WEB_SHARE", "").lower() == "true"

# Load environment variables on import
load_from_env()

# Utility functions
def get_model_path() -> Path:
    """Get model path, checking multiple locations.

    Returns:
        Path: Path to model file (may not exist if model not downloaded)
    """
    target_path = MODEL_CONFIG["local_path"]
    if target_path.exists():
        return target_path

    if LEGACY_MODEL_PATH.exists():
        _migrate_legacy_model()
        if target_path.exists():
            return target_path
        return LEGACY_MODEL_PATH

    return target_path  # Return expected path even if not exists

def is_model_available() -> bool:
    """Check if model is available locally.

    Returns:
        bool: True if model file exists, False otherwise
    """
    return get_model_path().exists()
