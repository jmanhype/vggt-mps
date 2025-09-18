#!/usr/bin/env python3
"""
Download VGGT model weights from Hugging Face
"""

import os
import requests
from pathlib import Path
from tqdm import tqdm

def download_file(url, dest_path):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, 'wb') as file:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=dest_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                pbar.update(len(chunk))

def main():
    print("=" * 60)
    print("VGGT Model Downloader")
    print("=" * 60)

    model_url = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt"
    model_path = Path("repo/vggt/vggt_model.pt")

    if model_path.exists():
        print(f"✅ Model already exists at {model_path}")
        print(f"   Size: {model_path.stat().st_size / 1e9:.2f} GB")
        response = input("\nRedownload? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download.")
            return

    print(f"\n📥 Downloading VGGT model (5GB)...")
    print(f"From: {model_url}")
    print(f"To: {model_path}")

    try:
        download_file(model_url, model_path)
        print(f"\n✅ Successfully downloaded model!")
        print(f"   Size: {model_path.stat().st_size / 1e9:.2f} GB")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nYou can manually download from:")
        print(model_url)
        print(f"And place it at: {model_path}")

if __name__ == "__main__":
    # Install tqdm if not available
    try:
        import tqdm
    except ImportError:
        print("Installing tqdm for progress bar...")
        os.system("pip install tqdm")
        from tqdm import tqdm

    main()