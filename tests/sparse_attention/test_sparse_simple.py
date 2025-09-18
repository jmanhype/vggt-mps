#!/usr/bin/env python3
"""
Simple test of sparse attention - just check if it runs without errors
"""

import torch
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_sparse_components():
    """Test individual components"""
    print("="*60)
    print("Testing Sparse Attention Components")
    print("="*60)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    # 1. Test MegaLoc
    print("\n1️⃣ Testing MegaLoc...")
    from megaloc_mps import MegaLocMPS

    megaloc = MegaLocMPS(device=str(device))
    test_img = torch.randn(1, 3, 224, 224).to(device)

    try:
        features = megaloc.extract_features(test_img)
        print(f"✅ MegaLoc features: {features.shape}")
    except Exception as e:
        print(f"❌ MegaLoc failed: {e}")
        return

    # 2. Test covisibility matrix
    print("\n2️⃣ Testing covisibility matrix...")
    try:
        # Multiple images
        multi_features = torch.randn(10, features.shape[1]).to(device)
        mask = megaloc.compute_covisibility_matrix(multi_features, k_nearest=3)
        print(f"✅ Covisibility mask: {mask.shape}")
        sparsity = (mask == 0).sum().item() / mask.numel()
        print(f"   Sparsity: {sparsity:.1%} zeros")
    except Exception as e:
        print(f"❌ Covisibility failed: {e}")
        return

    # 3. Test attention mask generation
    print("\n3️⃣ Testing attention mask for VGGT...")
    try:
        # Batch of image sequences [B, S, C, H, W]
        batch_images = torch.randn(1, 4, 3, 224, 224).to(device)
        attention_mask = megaloc.generate_attention_mask_for_vggt(
            batch_images,
            threshold=0.5,
            k_nearest=2
        )
        print(f"✅ Attention mask: {attention_mask.shape}")
        print(f"   Sample connections per image: {attention_mask[0, 0].sum().item()}")
    except Exception as e:
        print(f"❌ Attention mask failed: {e}")
        return

    # 4. Test sparse attention integration (mock)
    print("\n4️⃣ Testing sparse attention mechanism...")
    try:
        from vggt_sparse_attention import SparseAttentionAggregator

        # Create mock aggregator
        class MockAggregator(torch.nn.Module):
            def forward(self, x):
                return x

        mock_agg = MockAggregator()
        sparse_agg = SparseAttentionAggregator(mock_agg, megaloc)

        # Test with images
        sparse_agg.set_covisibility_mask(batch_images)
        print(f"✅ Sparse aggregator mask set: {sparse_agg.attention_mask.shape}")
    except Exception as e:
        print(f"❌ Sparse aggregator failed: {e}")
        return

    print("\n" + "="*60)
    print("✅ All components working!")
    print("="*60)

    # Memory comparison
    print("\n📊 Memory Estimation:")
    for n in [10, 50, 100, 500, 1000]:
        regular = n * n
        sparse = n * 10  # k=10
        savings = regular / sparse
        print(f"   {n:4d} images: {savings:5.1f}x savings")

if __name__ == "__main__":
    test_sparse_components()