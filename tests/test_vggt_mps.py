#!/usr/bin/env python3
"""
Test VGGT with PyTorch MPS (Metal Performance Shaders) on Apple Silicon
"""

import torch
import numpy as np
from pathlib import Path
import sys

print("=" * 50)
print("VGGT on Apple Silicon (MPS) Test")
print("=" * 50)

# Check MPS availability
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"✅ MPS (Metal Performance Shaders) available!")
    print(f"   Running on Apple Silicon GPU")
else:
    device = torch.device("cpu")
    print(f"⚠️  MPS not available, using CPU")

print(f"Device: {device}")
print("-" * 50)

# Try to load the model
try:
    print("Loading VGGT model weights...")
    model_path = Path("repo/vggt/vggt_model.pt")

    if model_path.exists():
        print(f"✅ Model file found: {model_path}")
        print(f"   Size: {model_path.stat().st_size / 1e9:.2f} GB")

        # Load model weights
        checkpoint = torch.load(model_path, map_location=device)
        print(f"✅ Model weights loaded to {device}")

        # Check what's in the checkpoint
        if isinstance(checkpoint, dict):
            print(f"   Checkpoint keys: {list(checkpoint.keys())[:5]}...")
            if 'model' in checkpoint:
                print(f"   Model state dict keys: {len(checkpoint['model'])} parameters")
        else:
            print(f"   Checkpoint type: {type(checkpoint)}")

    else:
        print(f"❌ Model file not found at {model_path}")
        print("   Download from: https://huggingface.co/facebook/VGGT-1B")

except Exception as e:
    print(f"❌ Error loading model: {e}")
    import traceback
    traceback.print_exc()

print("-" * 50)

# Test tensor operations on MPS
print("Testing MPS tensor operations...")
try:
    # Create a test tensor on MPS
    test_tensor = torch.randn(1, 3, 224, 224).to(device)
    print(f"✅ Created tensor on {device}: {test_tensor.shape}")

    # Simple convolution test
    conv = torch.nn.Conv2d(3, 64, 3).to(device)
    output = conv(test_tensor)
    print(f"✅ Convolution on {device}: {output.shape}")

    # Memory info (if available)
    if device.type == 'mps':
        print(f"✅ MPS operations working correctly!")

except Exception as e:
    print(f"❌ MPS operation failed: {e}")

print("=" * 50)