#!/usr/bin/env python3
"""
VGGT inference on Apple Silicon with MPS
"""

import torch
import torch.nn as nn
from pathlib import Path
import numpy as np
from PIL import Image
from typing import List, Dict, Any

class VGGTModelMPS:
    """VGGT wrapper for Apple Silicon MPS inference"""

    def __init__(self, model_path: str = "repo/vggt/vggt_model.pt"):
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Import real VGGT
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "repo" / "vggt"))
        from vggt.models.vggt import VGGT

        # Load the real VGGT model
        model_path = Path(__file__).parent.parent / model_path
        if model_path.exists():
            print(f"📂 Loading VGGT from: {model_path}")
            self.model = VGGT()
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint)
            self.model = self.model.to(self.device)
        else:
            print("📥 Downloading VGGT from HuggingFace...")
            self.model = VGGT.from_pretrained("facebook/VGGT-1B").to(self.device)

        self.model.eval()
        print("✅ Real VGGT model loaded successfully!")

    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """Preprocess image for VGGT"""
        img = Image.open(image_path).convert('RGB')
        img = img.resize((640, 480))

        # Convert to tensor and normalize
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)

        # Normalize with ImageNet stats
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        img_tensor = (img_tensor - mean) / std

        return img_tensor.unsqueeze(0).to(self.device)

    def infer(self, image_paths: List[str]) -> Dict[str, Any]:
        """Run VGGT inference on images"""
        # Import VGGT's loader
        from vggt.utils.load_fn import load_and_preprocess_images

        # Load and preprocess all images at once
        print("🖼️ Loading and preprocessing images...")
        input_images = load_and_preprocess_images(image_paths).to(self.device)

        # Run real VGGT inference
        print("🧠 Running VGGT inference...")
        with torch.no_grad():
            if self.device.type == "mps":
                # MPS doesn't support autocast
                predictions = self.model(input_images)
            else:
                dtype = torch.float16
                with torch.cuda.amp.autocast(dtype=dtype):
                    predictions = self.model(input_images)

        # Extract results from predictions
        results = {
            'camera_poses': predictions['pose_enc'].cpu().numpy(),
            'depth_maps': predictions['depth'].cpu().numpy()[0, :, :, :, 0],  # [S, H, W]
            'world_points': predictions['world_points'].cpu().numpy(),
            'confidence': predictions['depth_conf'].cpu().numpy()
        }

        # Generate point clouds from world points
        point_clouds = []
        for i in range(results['world_points'].shape[1]):
            points = results['world_points'][0, i].reshape(-1, 3)
            conf = results['confidence'][0, i].reshape(-1)
            # Filter by confidence
            mask = conf > 0.5
            points = points[mask]
            # Subsample if too many
            if len(points) > 10000:
                idx = np.random.choice(len(points), 10000, replace=False)
                points = points[idx]
            point_clouds.append(points)

        results['point_clouds'] = point_clouds

        print(f"✅ Processed {len(image_paths)} images")
        print(f"   - Camera poses: {results['camera_poses'].shape}")
        print(f"   - Depth maps: {results['depth_maps'].shape}")
        print(f"   - Point clouds: {len(point_clouds)} clouds")

        return results



def test_vggt_mps():
    """Test VGGT on MPS with sample images"""
    print("=" * 50)
    print("VGGT MPS Inference Test")
    print("=" * 50)

    # Initialize model
    model = VGGTModelMPS()

    # Use test images
    test_images = [
        "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs/test_image_001.jpg",
        "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs/test_image_002.jpg"
    ]

    # Check if images exist
    existing_images = [p for p in test_images if Path(p).exists()]
    if not existing_images:
        print("No test images found. Creating one...")
        # Create a simple test image
        test_img = Image.new('RGB', (640, 480), color=(73, 109, 137))
        test_img.save(test_images[0])
        existing_images = [test_images[0]]

    # Run inference
    print(f"\nRunning inference on {len(existing_images)} images...")
    results = model.infer(existing_images)

    # Show results
    print("\n" + "=" * 50)
    print("Results:")
    print(f"- Camera poses extracted: {len(results['camera_poses'])}")
    print(f"- Depth maps generated: {len(results['depth_maps'])}")
    print(f"- Point clouds created: {len(results['point_clouds'])}")

    for i, points in enumerate(results['point_clouds']):
        print(f"  Image {i+1}: {points.shape[0]} 3D points")

    print("=" * 50)
    print("✅ VGGT inference on MPS successful!")

    return results


if __name__ == "__main__":
    test_vggt_mps()