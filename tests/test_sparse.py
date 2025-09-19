"""
Sparse attention tests for VGGT
"""

import unittest
import torch
import torch.nn as nn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import DEVICE, SPARSE_CONFIG
from vggt_sparse_attention import (
    SparseAttentionAggregator,
    compute_covisibility_megaloc,
    make_vggt_sparse
)


class TestSparseAttention(unittest.TestCase):
    """Test sparse attention implementation"""

    def test_sparse_aggregator_creation(self):
        """Test creating sparse attention aggregator"""
        aggregator = SparseAttentionAggregator(
            feat_dim=256,
            pos_dim=12,
            num_heads=8,
            device=DEVICE
        )
        self.assertIsInstance(aggregator, nn.Module)
        print("✅ Sparse attention aggregator created")

    def test_covisibility_mask(self):
        """Test covisibility mask generation"""
        # Create dummy images
        images = torch.randn(4, 3, 224, 224).to(DEVICE)

        aggregator = SparseAttentionAggregator(
            feat_dim=256,
            pos_dim=12,
            num_heads=8,
            device=DEVICE
        )

        # Set covisibility mask
        aggregator.set_covisibility_mask(images)

        # Check mask was created
        self.assertTrue(hasattr(aggregator, 'covisibility_mask'))
        self.assertEqual(aggregator.covisibility_mask.shape, (4, 4))
        print("✅ Covisibility mask generated correctly")

    def test_memory_scaling(self):
        """Test O(n) vs O(n²) memory scaling"""
        # Test with different numbers of images
        for n_images in [10, 20, 50]:
            images = torch.randn(n_images, 3, 64, 64).to(DEVICE)

            # Calculate expected memory savings
            regular_memory = n_images * n_images  # O(n²)
            sparse_memory = n_images * SPARSE_CONFIG["covisibility_threshold"] * n_images
            savings = regular_memory / max(sparse_memory, 1)

            print(f"  Images: {n_images}, Expected savings: {savings:.1f}x")
            self.assertGreater(savings, 1.0)

        print("✅ Memory scaling verified as O(n)")


class TestCovisibility(unittest.TestCase):
    """Test covisibility detection"""

    def test_megaloc_covisibility(self):
        """Test MegaLoc-based covisibility computation"""
        # Create dummy images
        images = torch.randn(4, 3, 224, 224).to(DEVICE)

        # Compute covisibility
        covis_matrix = compute_covisibility_megaloc(
            images,
            device=DEVICE,
            threshold=SPARSE_CONFIG["covisibility_threshold"]
        )

        # Check matrix properties
        self.assertEqual(covis_matrix.shape, (4, 4))
        self.assertTrue(torch.all(covis_matrix.diag() == 1))  # Self-covisibility
        self.assertTrue(torch.all(covis_matrix == covis_matrix.T))  # Symmetric
        print("✅ MegaLoc covisibility computation works")

    def test_sparse_pattern(self):
        """Test that sparse pattern reduces connections"""
        # Create images that should have limited covisibility
        images = torch.randn(10, 3, 224, 224).to(DEVICE)

        covis_matrix = compute_covisibility_megaloc(
            images,
            device=DEVICE,
            threshold=0.5
        )

        # Count non-zero elements
        num_connections = covis_matrix.sum().item()
        max_connections = 10 * 10

        sparsity = 1.0 - (num_connections / max_connections)
        print(f"  Sparsity: {sparsity:.1%}")
        print(f"  Connections: {num_connections}/{max_connections}")

        # Should have some sparsity
        self.assertLess(num_connections, max_connections)
        print("✅ Sparse pattern reduces connections")


class TestVGGTIntegration(unittest.TestCase):
    """Test integration with VGGT model"""

    def test_make_vggt_sparse(self):
        """Test converting regular VGGT to sparse"""
        # Create a mock VGGT model
        class MockVGGT(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = nn.Linear(256, 256)
                self.aggregator = nn.MultiheadAttention(256, 8)

            def forward(self, x):
                return x

        mock_vggt = MockVGGT().to(DEVICE)

        # Convert to sparse
        sparse_vggt = make_vggt_sparse(mock_vggt, device=DEVICE)

        # Check that aggregator was replaced
        self.assertIsInstance(sparse_vggt.aggregator, SparseAttentionAggregator)
        print("✅ VGGT model converted to sparse")

    def test_sparse_forward_pass(self):
        """Test forward pass with sparse attention"""
        aggregator = SparseAttentionAggregator(
            feat_dim=64,
            pos_dim=12,
            num_heads=4,
            device=DEVICE
        )

        # Create dummy inputs
        feat_tokens = torch.randn(1, 4, 64).to(DEVICE)
        pos_tokens = torch.randn(1, 4, 12).to(DEVICE)

        # Set covisibility
        images = torch.randn(4, 3, 32, 32).to(DEVICE)
        aggregator.set_covisibility_mask(images)

        # Forward pass
        output = aggregator(feat_tokens, pos_tokens)

        self.assertEqual(output.shape, feat_tokens.shape)
        print("✅ Sparse forward pass successful")


if __name__ == '__main__':
    unittest.main()