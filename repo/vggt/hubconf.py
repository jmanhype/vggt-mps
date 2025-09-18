"""
Hub configuration for VGGT model loading
Enables torch.hub.load() functionality with MPS support
"""

import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional, Dict, Any

# Dependencies to export
dependencies = ['torch', 'torchvision', 'numpy', 'PIL']

def vggt(pretrained: bool = True, **kwargs) -> nn.Module:
    """
    Load VGGT model with MPS/CPU support

    Args:
        pretrained: Load pretrained weights
        **kwargs: Additional model configuration

    Returns:
        VGGT model instance
    """
    # Determine device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🔥 Using CUDA GPU")
    else:
        device = torch.device("cpu")
        print("💻 Using CPU")

    # Create model
    model = VGGTModel(**kwargs)

    if pretrained:
        # Load pretrained weights
        model_path = Path(__file__).parent / "vggt_model.pt"
        if model_path.exists():
            print(f"Loading weights from {model_path}")
            checkpoint = torch.load(model_path, map_location=device)

            # Handle different checkpoint formats
            if isinstance(checkpoint, dict):
                if 'model' in checkpoint:
                    model.load_state_dict(checkpoint['model'], strict=False)
                elif 'state_dict' in checkpoint:
                    model.load_state_dict(checkpoint['state_dict'], strict=False)
                else:
                    # Assume checkpoint is the state dict
                    model.load_state_dict(checkpoint, strict=False)
            else:
                model = checkpoint

            print("✅ Pretrained weights loaded")
        else:
            print(f"⚠️ Pretrained weights not found at {model_path}")
            print("Download from: https://huggingface.co/facebook/VGGT-1B")

    return model.to(device)


class VGGTModel(nn.Module):
    """
    Simplified VGGT model for demonstration
    Real model would have the full Vision Transformer architecture
    """

    def __init__(self,
                 image_size: int = 640,
                 patch_size: int = 16,
                 num_frames: int = 8,
                 embed_dim: int = 1024,
                 depth: int = 24,
                 num_heads: int = 16,
                 **kwargs):
        super().__init__()

        self.image_size = image_size
        self.patch_size = patch_size
        self.num_frames = num_frames

        # Simplified encoder (placeholder for full ViT)
        self.encoder = nn.Sequential(
            nn.Conv2d(3, embed_dim, kernel_size=patch_size, stride=patch_size),
            nn.GELU(),
            nn.LayerNorm([embed_dim, image_size//patch_size, image_size//patch_size])
        )

        # Decoder heads for different outputs
        self.camera_head = nn.Linear(embed_dim, 7)  # 6DOF + focal length
        self.depth_head = nn.Conv2d(embed_dim, 1, 1)
        self.track_head = nn.Conv2d(embed_dim, 2, 1)  # 2D tracks

    def forward(self, images: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass

        Args:
            images: (B, N, 3, H, W) batch of N images

        Returns:
            Dictionary with camera, depth, and track predictions
        """
        B, N, C, H, W = images.shape

        # Process each frame
        features = []
        for i in range(N):
            feat = self.encoder(images[:, i])
            features.append(feat)

        # Stack features
        features = torch.stack(features, dim=1)  # (B, N, C, H', W')

        # Global pooling for camera parameters
        global_feat = features.mean(dim=(1, 3, 4))  # (B, C)
        cameras = self.camera_head(global_feat)

        # Per-frame predictions
        depth_maps = []
        tracks = []

        for i in range(N):
            depth = self.depth_head(features[:, i])
            track = self.track_head(features[:, i])
            depth_maps.append(depth)
            tracks.append(track)

        return {
            'cameras': cameras,
            'depth': torch.stack(depth_maps, dim=1),
            'tracks': torch.stack(tracks, dim=1),
            'point_map': self._depth_to_points(torch.stack(depth_maps, dim=1))
        }

    def _depth_to_points(self, depth: torch.Tensor) -> torch.Tensor:
        """Convert depth maps to 3D point maps"""
        B, N, _, H, W = depth.shape

        # Create pixel grid
        y, x = torch.meshgrid(
            torch.arange(H, device=depth.device),
            torch.arange(W, device=depth.device),
            indexing='ij'
        )

        # Assume simple pinhole camera
        fx = fy = 500.0
        cx = W / 2
        cy = H / 2

        # Back-project to 3D
        X = (x - cx) * depth / fx
        Y = (y - cy) * depth / fy
        Z = depth

        # Stack into point map
        points = torch.stack([X, Y, Z], dim=2)  # (B, N, 3, H, W)

        return points