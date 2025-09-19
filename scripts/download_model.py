#!/usr/bin/env python3
"""Download VGGT model weights from Hugging Face."""

import os
import shutil
from pathlib import Path

import requests

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # type: ignore

MODEL_DIR = Path("models")
LEGACY_MODEL_PATH = Path("repo/vggt/vggt_model.pt")
MODEL_PATH = MODEL_DIR / "vggt_model.pt"


def download_file(url: str, dest_path: Path) -> None:
    """Download file with progress bar."""
    if tqdm is None:
        raise RuntimeError("tqdm is required; install it or run this script as __main__")

    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, "wb") as file:
        with tqdm(total=total_size, unit="B", unit_scale=True, desc=dest_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                pbar.update(len(chunk))


def migrate_legacy_model() -> Path:
    """Move legacy model file into the models/ directory if needed."""
    if MODEL_PATH.exists():
        return MODEL_PATH

    if LEGACY_MODEL_PATH.exists():
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            LEGACY_MODEL_PATH.replace(MODEL_PATH)
        except OSError:
            shutil.copy2(LEGACY_MODEL_PATH, MODEL_PATH)
            LEGACY_MODEL_PATH.unlink(missing_ok=True)
        print(f"🔁 Migrated model weights to {MODEL_PATH}")
        return MODEL_PATH

    return MODEL_PATH


def main() -> None:
    print("=" * 60)
    print("VGGT Model Downloader")
    print("=" * 60)

    model_url = "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt"
    model_path = migrate_legacy_model()

    if model_path.exists():
        print(f"✅ Model already exists at {model_path}")
        print(f"   Size: {model_path.stat().st_size / 1e9:.2f} GB")
        response = input("\nRedownload? (y/N): ")
        if response.lower() != "y":
            print("Skipping download.")
            return

    print("\n📥 Downloading VGGT model (5GB)...")
    print(f"From: {model_url}")
    print(f"To: {model_path}")

    try:
        download_file(model_url, model_path)
        print("\n✅ Successfully downloaded model!")
        print(f"   Size: {model_path.stat().st_size / 1e9:.2f} GB")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n❌ Download failed: {exc}")
        print("\nYou can manually download from:")
        print(model_url)
        print(f"and place it at: {model_path}")


if __name__ == "__main__":
    if tqdm is None:
        print("Installing tqdm for progress bar...")
        os.system("pip install tqdm")
        from tqdm import tqdm  # type: ignore  # noqa: E402

    main()
