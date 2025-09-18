#!/usr/bin/env python3
"""
Test torch.hub.load() for VGGT model
"""

import torch
import sys
from pathlib import Path

# Add repo to path
repo_path = Path(__file__).parent / "repo" / "vggt"
sys.path.insert(0, str(repo_path))

print("=" * 50)
print("Testing torch.hub functionality")
print("=" * 50)

# Import the hub configuration
from hubconf import vggt

# Test loading the model
print("\nLoading VGGT model with MPS support...")
model = vggt(pretrained=True)

print("\n✅ Model loaded successfully!")
print(f"Model type: {type(model)}")
print(f"Model device: {next(model.parameters()).device}")

# Test a simple forward pass
print("\nTesting forward pass...")
test_input = torch.randn(1, 1, 3, 640, 640).to(next(model.parameters()).device)
try:
    with torch.no_grad():
        output = model(test_input)
    print(f"✅ Forward pass successful!")
    print(f"Output keys: {list(output.keys())}")
except Exception as e:
    print(f"⚠️ Forward pass failed (expected for simplified model): {e}")

print("=" * 50)