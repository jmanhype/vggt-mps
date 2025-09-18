#!/usr/bin/env python3
"""Quick test of VGGT on MPS"""

import torch
import sys
from pathlib import Path

print("=" * 60)
print("🍎 Quick VGGT MPS Test")
print("=" * 60)

# Check MPS
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ MPS available!")
else:
    device = torch.device("cpu")
    print("⚠️ MPS not available, using CPU")

# Add VGGT to path
sys.path.insert(0, str(Path(__file__).parent / "repo" / "vggt"))

try:
    from vggt.models.vggt import VGGT
    print("✅ VGGT import successful")

    # Try to initialize model structure (without weights)
    model = VGGT()
    print(f"✅ VGGT model created with {sum(p.numel() for p in model.parameters())} parameters")

    # Try to move to MPS
    model = model.to(device)
    print(f"✅ Model moved to {device}")

    # Create dummy input
    dummy_input = torch.randn(1, 3, 518, 518).to(device)
    print(f"✅ Test input created: {dummy_input.shape} on {dummy_input.device}")

    # Test forward pass with random weights
    model.eval()
    with torch.no_grad():
        output = model(dummy_input.unsqueeze(0))  # Add batch dimension

    print("✅ Forward pass successful!")
    print(f"   - Depth shape: {output['depth'].shape}")
    print(f"   - Camera poses: {output['pose_enc'].shape}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)