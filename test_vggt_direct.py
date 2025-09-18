#!/usr/bin/env python3
"""
Test VGGT inference directly with MPS support
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
import glob

print("=" * 60)
print("Testing VGGT Direct Inference with MPS")
print("=" * 60)

# Check device
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("🍎 Using MPS (Metal Performance Shaders) on Apple Silicon")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("🔥 Using CUDA GPU")
else:
    device = torch.device("cpu")
    print("💻 Using CPU")

# Import VGGT modules
try:
    import sys
    vggt_path = Path(__file__).parent / "repo" / "vggt"
    sys.path.insert(0, str(vggt_path))

    from vggt.models.vggt import VGGT
    from vggt.utils.load_fn import load_and_preprocess_images
    print("✅ VGGT modules imported")
except ImportError as e:
    print(f"❌ Failed to import VGGT: {e}")
    print("Trying simplified model...")
    from hubconf import vggt
    model = vggt(pretrained=True)
    print("✅ Using simplified hub model")
else:
    # Load full VGGT model
    print("\nLoading VGGT model...")
    try:
        model = VGGT.from_pretrained("facebook/VGGT-1B").to(device)
        print("✅ Loaded from pretrained")
    except:
        model = VGGT()
        model_path = Path(__file__).parent / "repo" / "vggt" / "vggt_model.pt"
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=device)
            if isinstance(checkpoint, dict) and 'model' in checkpoint:
                model.load_state_dict(checkpoint['model'], strict=False)
            elif isinstance(checkpoint, dict):
                model.load_state_dict(checkpoint, strict=False)
            print(f"✅ Loaded from {model_path}")
        model = model.to(device)

model.eval()

# Load test images
input_dir = Path("/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs")
image_paths = sorted(input_dir.glob("test_scene_*.jpg"))[:4]

print(f"\nFound {len(image_paths)} test images")

# Process with simplified model if using hubconf
if hasattr(model, 'forward') and 'VGGTModel' in str(type(model)):
    print("\nUsing simplified model inference...")

    # Create batch of images
    images = []
    for path in image_paths:
        img = Image.open(path).convert('RGB')
        img = img.resize((640, 480))
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)

        # Normalize
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        img_tensor = (img_tensor - mean) / std
        images.append(img_tensor)

    # Stack into batch (B, N, C, H, W)
    image_batch = torch.stack(images).unsqueeze(0).to(device)

    print(f"Image batch shape: {image_batch.shape}")

    with torch.no_grad():
        output = model(image_batch)

    print("\n✅ Inference successful!")
    print(f"Output keys: {list(output.keys())}")

    # Show output shapes
    for key, val in output.items():
        if isinstance(val, torch.Tensor):
            print(f"  {key}: {val.shape}")

else:
    print("\nUsing full VGGT model inference...")

    # Load and preprocess images
    image_path_strs = [str(p) for p in image_paths]
    images = load_and_preprocess_images(image_path_strs).to(device)

    print(f"Preprocessed images shape: {images.shape}")

    # Run inference
    dtype = torch.float32  # Use float32 for MPS

    with torch.no_grad():
        if device.type == "cuda":
            with torch.cuda.amp.autocast(dtype=dtype):
                predictions = model(images)
        else:
            predictions = model(images)

    print("\n✅ Inference successful!")
    print(f"Prediction keys: {list(predictions.keys())}")

    # Show prediction shapes
    for key, val in predictions.items():
        if isinstance(val, torch.Tensor):
            print(f"  {key}: {val.shape}")

print("\n" + "=" * 60)
print("✅ VGGT inference with MPS completed successfully!")
print("=" * 60)