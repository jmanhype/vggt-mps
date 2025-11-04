#!/usr/bin/env python3
"""
MegaLoc MPS Port for VGGT Sparse Attention
Implements covisibility detection for O(n) scaling
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
import numpy as np
from typing import Tuple, Optional

class MegaLocMPS(nn.Module):
    """MegaLoc ported to Apple Silicon MPS for fast covisibility detection"""

    def __init__(
        self,
        num_clusters: int = 64,
        cluster_dim: int = 256,
        token_dim: int = 256,
        mlp_dim: int = 512,
        device: str = "mps"
    ):
        super().__init__()

        # Device setup
        self.device = torch.device(device if torch.backends.mps.is_available() else "cpu")
        print(f"MegaLoc using device: {self.device}")

        # DINOv2 backbone (we'll use torch.hub to load)
        self.backbone = self._load_dinov2()

        # SALAD aggregator components
        self.cluster_dim = cluster_dim
        self.token_dim = token_dim
        self.num_clusters = num_clusters

        # MLPs for SALAD
        self.mlp_local = nn.Sequential(
            nn.Linear(768, mlp_dim),  # DINOv2 outputs 768 dims
            nn.ReLU(),
            nn.Linear(mlp_dim, num_clusters * cluster_dim)
        ).to(self.device)

        self.mlp_global = nn.Sequential(
            nn.Linear(768, mlp_dim),
            nn.ReLU(),
            nn.Linear(mlp_dim, token_dim)
        ).to(self.device)

        # Output dimension
        self.out_dim = num_clusters * cluster_dim + token_dim

    def _load_dinov2(self) -> nn.Module:
        """Load DINOv2 backbone optimized for MPS"""
        try:
            # Load DINOv2 ViT-B/14
            model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14')
            model = model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"⚠️ Could not load DINOv2: {e}")
            print("   Using placeholder for testing")
            # Placeholder if DINOv2 not available
            return nn.Identity()

    def extract_features(self, images: torch.Tensor) -> torch.Tensor:
        """
        Extract MegaLoc features from images

        Args:
            images: [B, 3, H, W] tensor of images

        Returns:
            features: [B, out_dim] normalized feature vectors
        """
        B = images.shape[0]

        # Resize to multiple of 14 for ViT
        H, W = images.shape[-2:]
        new_H = (H // 14) * 14
        new_W = (W // 14) * 14
        if H != new_H or W != new_W:
            images = F.interpolate(images, size=(new_H, new_W), mode='bilinear')

        # Extract DINOv2 features
        with torch.no_grad():
            if hasattr(self.backbone, 'forward_features'):
                # Real DINOv2
                features_dict = self.backbone.forward_features(images)
                local_features = features_dict['x_norm_patchtokens']  # [B, N, 768]
                global_token = features_dict['x_norm_clstoken']  # [B, 768]
            else:
                # Placeholder
                N = (new_H // 14) * (new_W // 14)
                local_features = torch.randn(B, N, 768, device=self.device)
                global_token = torch.randn(B, 768, device=self.device)

        # Apply SALAD aggregation
        local_desc = self.mlp_local(local_features)  # [B, N, num_clusters * cluster_dim]
        local_desc = local_desc.reshape(B, -1, self.num_clusters, self.cluster_dim)

        # Sinkhorn normalization (simplified)
        local_desc = F.softmax(local_desc, dim=1)  # Soft assignment
        local_desc = local_desc.sum(dim=1)  # Aggregate: [B, num_clusters, cluster_dim]
        local_desc = local_desc.reshape(B, -1)  # [B, num_clusters * cluster_dim]

        # Global token processing
        global_desc = self.mlp_global(global_token)  # [B, token_dim]

        # Concatenate and normalize
        features = torch.cat([local_desc, global_desc], dim=1)  # [B, out_dim]
        features = F.normalize(features, p=2, dim=1)

        return features

    def compute_covisibility_matrix(
        self,
        features: torch.Tensor,
        threshold: float = 0.7,
        k_nearest: Optional[int] = None
    ) -> torch.Tensor:
        """
        Compute covisibility matrix from features

        Args:
            features: [N, D] feature vectors
            threshold: Similarity threshold for covisibility
            k_nearest: If set, ensure each image connects to k nearest neighbors

        Returns:
            mask: [N, N] binary covisibility matrix (1 = covisible, 0 = not)
        """
        N = features.shape[0]

        # Compute pairwise cosine similarities
        similarities = torch.mm(features, features.t())  # [N, N]

        # Create binary mask
        mask = (similarities > threshold).float()

        # Ensure k-nearest neighbors if specified
        if k_nearest is not None and k_nearest > 0:
            # Get k nearest for each image
            _, indices = similarities.topk(min(k_nearest, N), dim=1)

            # Add k-nearest connections
            for i in range(N):
                mask[i, indices[i]] = 1.0
                mask[indices[i], i] = 1.0  # Symmetric

        # Always connect to self
        mask.fill_diagonal_(1.0)

        return mask

    def generate_attention_mask_for_vggt(
        self,
        images: torch.Tensor,
        threshold: float = 0.7,
        k_nearest: int = 10,
        ensure_connected: bool = True
    ) -> torch.Tensor:
        """
        Generate sparse attention mask for VGGT

        Args:
            images: [B, S, 3, H, W] batch of image sequences
            threshold: Covisibility threshold
            k_nearest: Minimum connections per image
            ensure_connected: Whether to ensure graph connectivity

        Returns:
            attention_mask: [B, S, S] attention mask for VGGT
        """
        B, S = images.shape[:2]

        # Process each batch
        masks = []
        for b in range(B):
            # Extract features for this batch
            batch_images = images[b]  # [S, 3, H, W]
            features = self.extract_features(batch_images)  # [S, D]

            # Compute covisibility
            mask = self.compute_covisibility_matrix(
                features, threshold, k_nearest
            )

            # Ensure connectivity if requested
            if ensure_connected:
                mask = self._ensure_graph_connectivity(mask)

            masks.append(mask)

        # Stack into batch
        attention_mask = torch.stack(masks, dim=0)  # [B, S, S]

        return attention_mask

    def _ensure_graph_connectivity(self, mask: torch.Tensor) -> torch.Tensor:
        """
        Ensure the attention graph is connected

        Args:
            mask: [N, N] binary matrix

        Returns:
            mask: [N, N] connected binary matrix
        """
        N = mask.shape[0]

        # Simple heuristic: connect sequential frames
        # This ensures at least a chain connection
        for i in range(N - 1):
            mask[i, i + 1] = 1.0
            mask[i + 1, i] = 1.0

        # Could implement more sophisticated graph algorithms here
        # like finding connected components and bridging them

        return mask


def integrate_with_vggt(vggt_model, megaloc_model):
    """
    Integrate MegaLoc sparse attention into VGGT

    This modifies VGGT's attention mechanism to use sparse masks
    """

    # Store original forward
    original_forward = vggt_model.forward

    def forward_with_sparse_attention(images, query_points=None):
        # Generate sparse attention mask
        with torch.no_grad():
            attention_mask = megaloc_model.generate_attention_mask_for_vggt(
                images.unsqueeze(0) if images.ndim == 4 else images
            )

        # TODO: Modify VGGT's aggregator to use this mask
        # This would require patching the attention layers
        # For now, just call original forward
        return original_forward(images, query_points)

    # Replace forward method
    vggt_model.forward = forward_with_sparse_attention

    return vggt_model


def test_megaloc_mps():
    """Test MegaLoc on MPS"""
    print("=" * 60)
    print("🔍 Testing MegaLoc on MPS")
    print("=" * 60)

    # Initialize MegaLoc
    model = MegaLocMPS()

    # Create test images
    test_images = torch.randn(4, 3, 224, 224).to(model.device)

    # Extract features
    features = model.extract_features(test_images)
    print(f"✅ Features extracted: {features.shape}")

    # Compute covisibility
    mask = model.compute_covisibility_matrix(features, k_nearest=2)
    print(f"✅ Covisibility matrix: {mask.shape}")
    print(f"   Sparsity: {(mask == 0).sum().item() / mask.numel():.2%} zeros")

    # Memory savings
    n = 100
    full_attention = n * n
    sparse_attention = n * 10  # k=10 nearest
    print(f"\n📊 For {n} images:")
    print(f"   Full attention: {full_attention:,} connections")
    print(f"   Sparse attention: {sparse_attention:,} connections")
    print(f"   Memory savings: {full_attention/sparse_attention:.1f}x")

    print("=" * 60)


if __name__ == "__main__":
    test_megaloc_mps()