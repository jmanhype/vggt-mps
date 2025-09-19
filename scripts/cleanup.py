#!/usr/bin/env python3
"""Utility to clean runtime, build, and model artifacts.

Usage examples:

    # Preview what would be removed
    python scripts/cleanup.py --dry-run

    # Remove runtime directories (logs, outputs, tmp, data)
    python scripts/cleanup.py --yes

    # Deep clean including models and build artifacts
    python scripts/cleanup.py --all --yes
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CleanupTarget:
    path: Path
    is_dir: bool

    @property
    def exists(self) -> bool:
        return self.path.exists()

    def size(self) -> int:
        if not self.exists:
            return 0
        if self.path.is_file():
            return self.path.stat().st_size
        total = 0
        for child in self.path.rglob("*"):
            try:
                total += child.stat().st_size
            except FileNotFoundError:
                continue
        return total


RUNTIME_DIRS: List[CleanupTarget] = [
    CleanupTarget(PROJECT_ROOT / name, True)
    for name in ("logs", "outputs", "tmp", "data")
]

BUILD_ARTIFACTS: List[CleanupTarget] = [
    CleanupTarget(PROJECT_ROOT / name, True)
    for name in ("build", "dist", ".pytest_cache", ".benchmarks")
]

MODEL_ARTIFACTS: List[CleanupTarget] = [
    CleanupTarget(PROJECT_ROOT / "models", True),
    CleanupTarget(PROJECT_ROOT / "repo" / "vggt" / "vggt_model.pt", False),
]


def format_bytes(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024 or unit == "TB":
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def collect_targets(args: argparse.Namespace) -> List[CleanupTarget]:
    targets: List[CleanupTarget] = []

    if args.all or args.runtime:
        targets.extend(RUNTIME_DIRS)

    if args.all or args.build:
        targets.extend(BUILD_ARTIFACTS)

    if args.all or args.models:
        targets.extend(MODEL_ARTIFACTS)

    # Deduplicate while preserving order
    seen = set()
    unique: List[CleanupTarget] = []
    for target in targets:
        key = target.path.resolve()
        if key not in seen:
            unique.append(target)
            seen.add(key)
    return unique


def remove_target(target: CleanupTarget, dry_run: bool) -> None:
    if not target.exists:
        return

    if dry_run:
        return

    if target.is_dir:
        shutil.rmtree(target.path, ignore_errors=True)
    else:
        try:
            target.path.unlink()
        except FileNotFoundError:
            pass


def confirm(prompt: str) -> bool:
    try:
        response = input(prompt).strip().lower()
    except EOFError:
        return False
    return response in {"y", "yes", ""}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean VGGT-MPS workspace artifacts")
    parser.add_argument("--runtime", action="store_true", help="Remove runtime directories (default)")
    parser.add_argument("--build", action="store_true", help="Remove build artifacts")
    parser.add_argument("--models", action="store_true", help="Remove downloaded models")
    parser.add_argument("--all", action="store_true", help="Remove runtime, build, and model artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    # Default to runtime cleanup if nothing specified
    if not any((args.runtime, args.build, args.models, args.all)):
        args.runtime = True

    return args


def main() -> int:
    args = parse_args()
    targets = collect_targets(args)

    existing = [t for t in targets if t.exists]
    if not existing:
        print("Nothing to clean – workspace already tidy ✨")
        return 0

    total_size = sum(target.size() for target in existing)

    print("The following targets will be removed:" if not args.dry_run else "Would remove:")
    for target in existing:
        size = format_bytes(target.size())
        rel = target.path.relative_to(PROJECT_ROOT)
        kind = "dir" if target.is_dir else "file"
        print(f"  - {rel} ({kind}, {size})")

    print(f"Total size: {format_bytes(total_size)}")

    if args.dry_run:
        print("Dry run complete. Use --yes to execute.")
        return 0

    if not args.yes and not confirm("Proceed with deletion? [Y/n] "):
        print("Aborted – no changes made.")
        return 1

    for target in existing:
        remove_target(target, dry_run=False)

    print("Cleanup complete ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
