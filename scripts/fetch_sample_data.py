#!/usr/bin/env python3
"""Download additional VGGT sample scenes from facebookresearch/vggt."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
from typing import Iterable, List

import subprocess

REPO = "facebookresearch/vggt"
DEFAULT_OUTPUT = Path("examples/sample_data/datasets")
DEFAULT_SCENES = [
    "kitchen/images",
    "single_cartoon/images",
    "single_oil_painting/images",
    "llff_fern",
    "llff_flower",
    "room",
]

def gh_api(path: str) -> dict:
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def download_file(remote_path: str, dest: Path) -> None:
    data = gh_api(remote_path)
    content = base64.b64decode(data["content"], validate=False)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)


def download_scene(scene: str, output_root: Path) -> None:
    print(f"\n📥 Downloading {scene} ...")
    entries = gh_api(f"examples/{scene}")
    for entry in entries:
        if entry["type"] == "file":
            dest = output_root / scene / entry["name"]
            download_file(f"examples/{scene}/{entry['name']}", dest)
            print(f"  • {dest.relative_to(output_root)}")
        elif entry["type"] == "dir":
            download_scene(f"{scene}/{entry['name']}", output_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch VGGT sample datasets")
    parser.add_argument("--scenes", nargs="*", default=DEFAULT_SCENES, help="Scenes to download (relative to examples/)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination directory")
    return parser.parse_args()


def main() -> None:
    if os.getenv("GITHUB_TOKEN") is None:
        print("⚠️ GITHUB_TOKEN is not set; 'gh api' may hit rate limits")
    args = parse_args()
    for scene in args.scenes:
        download_scene(scene, args.output)
    print('\n✅ Done')


if __name__ == "__main__":
    main()
