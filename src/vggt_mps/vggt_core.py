"""
Core VGGT processing module
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import sys

# Add VGGT repo to path
REPO_PATH = Path(__file__).parent.parent / "repo" / "vggt"
if REPO_PATH.exists():
    sys.path.insert(0, str(REPO_PATH))


class VGGTProcessor:
    """VGGT model processor for 3D reconstruction"""

    def __init__(self, device: Union[str, torch.device] = "mps"):
        """
        Initialize VGGT processor

        Args:
            device: Device to run model on (mps, cuda, cpu)
        """
        self.device = torch.device(device) if isinstance(device, str) else device
        self.model = None
        self.dtype = torch.float32 if self.device.type == "mps" else torch.float16

    def load_model(self, model_path: Optional[Path] = None) -> None:
        """
        Load VGGT model with robust error handling.

        Args:
            model_path: Optional path to model weights. If not provided,
                       will search default locations and fall back to HuggingFace.

        Raises:
            ImportError: If VGGT module cannot be imported (handled gracefully)
            RuntimeError: If model loading fails completely
        """
        if self.model is not None:
            return  # Already loaded

        try:
            from vggt.models.vggt import VGGT
        except ImportError as e:
            print(f"⚠️ VGGT module not found: {e}")
            print("   Using simulated mode for testing.")
            return

        if model_path is None:
            # Default paths to check
            possible_paths = [
                Path(__file__).parent.parent / "models" / "vggt_model.pt",
                Path(__file__).parent.parent / "repo" / "vggt" / "vggt_model.pt",
            ]
            for path in possible_paths:
                if path.exists():
                    model_path = path
                    break

        # Try loading from local path if provided
        try_huggingface = False  # Flag to control HuggingFace fallback

        if model_path is not None and model_path.exists():
            # Local model file exists - try loading it
            print(f"📂 Loading model from: {model_path}")
            try:
                self.model = VGGT()
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)

                # Validate checkpoint format
                if not isinstance(checkpoint, dict):
                    raise ValueError(f"Invalid checkpoint format: expected dict, got {type(checkpoint)}")

                self.model.load_state_dict(checkpoint)
                self.model = self.model.to(self.device)
                print("✅ Model loaded successfully from local path!")
                return  # Success - exit early
            except Exception as e:
                print(f"⚠️ Error loading model from disk: {e}")
                print("   Attempting to load from HuggingFace...")
                self.model = None  # Clear corrupted model state
                try_huggingface = True  # Trigger HuggingFace fallback
        else:
            # No local model available
            if model_path is not None:
                print(f"⚠️ Local model not found at: {model_path}")
            try_huggingface = True

        # Try HuggingFace fallback if:
        # 1. No local path was provided (model_path is None)
        # 2. Local path doesn't exist
        # 3. Local loading failed with exception
        if self.model is None and try_huggingface:
            print("📥 Loading model from HuggingFace...")
            try:
                self.model = VGGT.from_pretrained("facebook/VGGT-1B").to(self.device)
                print("✅ Model loaded successfully from HuggingFace!")
            except Exception as e:
                print(f"⚠️ Could not load model from HuggingFace: {e}")
                print("   Run 'vggt download' to download the model manually.")
                self.model = None

        if self.model:
            self.model.eval()

    def process_images(self, images: List[np.ndarray]) -> Union[List[np.ndarray], Dict[str, Any]]:
        """
        Process images through VGGT

        Args:
            images: List of images as numpy arrays (H, W, 3)

        Returns:
            Dict containing depth maps, camera poses, and point cloud, or list of depth maps as fallback

        Raises:
            ValueError: If images list is empty or contains invalid data
        """
        # Input validation
        if not images:
            raise ValueError("Empty image list provided")

        if not isinstance(images, list):
            raise ValueError(f"Expected list of images, got {type(images)}")

        for i, img in enumerate(images):
            if not isinstance(img, np.ndarray):
                raise ValueError(f"Image {i} is not a numpy array: {type(img)}")
            if img.ndim != 3 or img.shape[2] != 3:
                raise ValueError(f"Image {i} has invalid shape {img.shape}, expected (H, W, 3)")

        # Ensure model is loaded
        if self.model is None:
            self.load_model()

        # Verify model loaded successfully after load attempt
        # Check both that model exists AND that it has required methods
        # Note: This is intentional graceful degradation, not an error condition
        # The system can still function with simulated depth for testing/development
        if self.model is None or not hasattr(self.model, 'eval'):
            if self.model is not None:
                print("⚠️ Model loaded but appears to be invalid (missing required methods)")
            else:
                print("⚠️ Model could not be loaded from any source (local or HuggingFace)")
            print("   Falling back to simulated depth for testing purposes")
            print("   To use real model: run 'vggt download' or check network connection")
            return self._simulate_depth(images)

        # Process with real model
        temp_dir = None
        try:
            from vggt.utils.load_fn import load_and_preprocess_images

            # Save images temporarily for VGGT loader
            import tempfile
            import shutil
            temp_dir = Path(tempfile.mkdtemp())
            temp_paths = []

            for i, img in enumerate(images):
                temp_path = temp_dir / f"input_{i:03d}.jpg"
                if isinstance(img, np.ndarray):
                    Image.fromarray(img).save(temp_path)
                else:
                    img.save(temp_path)
                temp_paths.append(str(temp_path))

            # Load and preprocess
            input_tensor = load_and_preprocess_images(temp_paths).to(self.device)

            # Run inference
            with torch.no_grad():
                if self.device.type == "mps":
                    predictions = self.model(input_tensor)
                else:
                    with torch.cuda.amp.autocast(dtype=self.dtype):
                        predictions = self.model(input_tensor)

            # Extract depth maps
            depth_tensor = predictions['depth'].cpu().numpy()
            depth_maps = [depth_tensor[0, i, :, :, 0] for i in range(depth_tensor.shape[1])]

            # Return full predictions dict if available
            result = {
                'depth_maps': depth_maps,
                'camera_poses': predictions.get('poses', None),
                'point_cloud': self._generate_point_cloud(images, depth_maps)
            }

            return result

        except Exception as e:
            print(f"⚠️ Error processing with real model: {e}")
            print(f"   Falling back to simulated depth maps.")
            return self._simulate_depth(images)

        finally:
            # Clean up temp files
            if temp_dir is not None and temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Could not clean up temp directory: {cleanup_error}")

    def _simulate_depth(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """
        Generate simulated depth maps for testing

        Args:
            images: List of input images

        Returns:
            List of simulated depth maps
        """
        depth_maps = []
        for img in images:
            if isinstance(img, np.ndarray):
                h, w = img.shape[:2]
            else:
                w, h = img.size

            # Create radial depth pattern
            center_x, center_y = w // 2, h // 2
            y_coords, x_coords = np.ogrid[:h, :w]
            distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)

            # Normalize to depth range
            max_dist = np.sqrt(center_x**2 + center_y**2)
            depth = 5.0 + 3.0 * (1.0 - distances / max_dist)

            # Add some noise
            depth += np.random.randn(h, w) * 0.2

            depth_maps.append(depth)

        return depth_maps

    def _generate_point_cloud(
        self,
        images: List[np.ndarray],
        depth_maps: List[np.ndarray],
        step: int = 10
    ) -> np.ndarray:
        """
        Generate 3D point cloud from depth maps

        Args:
            images: Input images
            depth_maps: Depth maps
            step: Downsampling step for visualization

        Returns:
            Nx3 array of 3D points
        """
        all_points = []

        for i, (img, depth) in enumerate(zip(images, depth_maps)):
            h, w = depth.shape

            # Camera parameters (simplified)
            fx = fy = 500
            cx, cy = w/2, h/2

            # Create pixel grid
            xx, yy = np.meshgrid(np.arange(0, w, step), np.arange(0, h, step))

            # Sample depth
            z = depth[::step, ::step]

            # Back-project to 3D
            x = (xx - cx) * z / fx + i * 2  # Offset each view
            y = (yy - cy) * z / fy

            # Stack points
            points = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=-1)
            all_points.append(points)

        return np.vstack(all_points)