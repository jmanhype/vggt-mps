"""
Download model command for VGGT-MPS
"""

import sys
from pathlib import Path
import urllib.request
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MODEL_CONFIG, MODEL_DIR, get_model_path


def download_model(args):
    """Download VGGT model weights"""
    print("=" * 60)
    print("📥 VGGT Model Downloader")
    print("=" * 60)
    print(f"Model: {MODEL_CONFIG['name']}")
    print(f"Size: {MODEL_CONFIG['model_size']}")
    print(f"Parameters: {MODEL_CONFIG['parameters']}")
    print("-" * 60)

    # Check if model already exists
    model_path = get_model_path()
    if model_path.exists():
        print(f"✅ Model already exists at: {model_path}")
        response = input("Download again? (y/n): ")
        if response.lower() != 'y':
            return 0

    # Ensure model directory exists
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if args.source == "huggingface":
        print("\n📥 Downloading from HuggingFace...")
        try:
            # Try using huggingface_hub if available
            from huggingface_hub import hf_hub_download

            model_file = hf_hub_download(
                repo_id=MODEL_CONFIG["huggingface_id"],
                filename="model.pt",
                cache_dir=MODEL_DIR,
                local_dir=MODEL_DIR
            )
            print(f"✅ Downloaded to: {model_file}")

        except ImportError:
            print("⚠️ huggingface_hub not installed")
            print("Install with: pip install huggingface_hub")
            print("\nAlternatively, download manually from:")
            print(f"https://huggingface.co/{MODEL_CONFIG['huggingface_id']}/resolve/main/model.pt")
            print(f"\nSave to: {MODEL_CONFIG['local_path']}")
            return 1

        except Exception as e:
            print(f"❌ Download failed: {e}")
            return 1

    else:  # direct download
        print("\n📥 Direct download...")
        url = f"https://huggingface.co/{MODEL_CONFIG['huggingface_id']}/resolve/main/model.pt"
        target_path = MODEL_CONFIG["local_path"]

        print(f"URL: {url}")
        print(f"Target: {target_path}")

        try:
            # Download with progress
            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(downloaded * 100 / total_size, 100)
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total_size / 1024 / 1024
                print(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end="")

            print("\nDownloading...")
            urllib.request.urlretrieve(url, target_path, reporthook=download_progress)
            print("\n✅ Download complete!")

        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            print("\nManual download instructions:")
            print(f"1. Visit: https://huggingface.co/{MODEL_CONFIG['huggingface_id']}")
            print("2. Download: model.pt")
            print(f"3. Save to: {target_path}")
            return 1

    # Verify download
    if model_path.exists():
        file_size = model_path.stat().st_size / 1024 / 1024 / 1024  # GB
        print(f"\n✅ Model verified: {file_size:.1f} GB")
        print(f"📁 Location: {model_path}")
    else:
        print("\n❌ Model file not found after download")
        return 1

    print("\n" + "=" * 60)
    print("✅ Model ready for use!")
    print("Run: python main.py demo")
    print("=" * 60)

    return 0