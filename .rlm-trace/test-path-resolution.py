#!/usr/bin/env python3
"""
Test script to verify PROJECT_ROOT path resolution
"""
from pathlib import Path
import sys

# Add src to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vggt_mps import config

print("=" * 60)
print("PATH RESOLUTION TEST")
print("=" * 60)

print(f"\n📍 config.py location: {Path(config.__file__).resolve()}")
print(f"   Expected: .../vggt-mps/src/vggt_mps/config.py")

print(f"\n📂 PROJECT_ROOT: {config.PROJECT_ROOT.resolve()}")
print(f"   Expected: .../vggt-mps/")

print(f"\n📂 SRC_DIR: {config.SRC_DIR.resolve()}")
print(f"   Expected: .../vggt-mps/src/")
print(f"   Exists: {config.SRC_DIR.exists()}")

print(f"\n📂 DATA_DIR: {config.DATA_DIR.resolve()}")
print(f"   Expected: .../vggt-mps/data/")
print(f"   Exists: {config.DATA_DIR.exists()}")

print(f"\n📂 MODEL_DIR: {config.MODEL_DIR.resolve()}")
print(f"   Expected: .../vggt-mps/models/")
print(f"   Exists: {config.MODEL_DIR.exists()}")

print(f"\n📂 OUTPUT_DIR: {config.OUTPUT_DIR.resolve()}")
print(f"   Expected: .../vggt-mps/outputs/")
print(f"   Exists: {config.OUTPUT_DIR.exists()}")

print(f"\n📂 REPO_DIR: {config.REPO_DIR.resolve()}")
print(f"   Expected: .../vggt-mps/repo/")
print(f"   Exists: {config.REPO_DIR.exists()}")

# Verify PROJECT_ROOT contains expected files
print("\n🔍 Verifying PROJECT_ROOT structure:")
expected_files = ['setup.py', 'pyproject.toml', 'README.md', 'src']
for expected in expected_files:
    path = config.PROJECT_ROOT / expected
    exists = path.exists()
    icon = "✅" if exists else "❌"
    print(f"   {icon} {expected}: {exists}")

print("\n" + "=" * 60)
if all((config.PROJECT_ROOT / f).exists() for f in expected_files):
    print("✅ PATH RESOLUTION TEST PASSED")
    sys.exit(0)
else:
    print("❌ PATH RESOLUTION TEST FAILED")
    sys.exit(1)
