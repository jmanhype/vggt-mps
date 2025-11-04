"""
VGGT-MPS: 3D Vision Agent for Apple Silicon

A powerful 3D reconstruction package optimized for Apple Silicon,
featuring sparse attention for city-scale reconstruction.
"""

__version__ = "2.0.0"
__author__ = "VGGT MPS Contributors"
__license__ = "MIT"

# Core exports
from .vggt_core import VGGTProcessor
from .config import (
    DEVICE,
    MODEL_CONFIG,
    SPARSE_CONFIG,
    get_device,
    get_model_path,
    is_model_available,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core classes
    "VGGTProcessor",
    # Configuration
    "DEVICE",
    "MODEL_CONFIG",
    "SPARSE_CONFIG",
    "get_device",
    "get_model_path",
    "is_model_available",
]