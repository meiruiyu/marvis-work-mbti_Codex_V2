#!/usr/bin/env python3
"""Validate the repository against Marvis/Tencent Agent Skill package limits."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MAX_FILES = 300
MAX_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".yaml", ".yml"
}
TEXT_NAMES = {".gitignore", "LICENSE", "SKILL.md"}


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
    )
    return [root / line for line in result.stdout.splitlines() if line]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors: list[str] = []
    files = tracked_files(root)

    for required in (root / "SKILL.md", root / "LICENSE"):
        if required not in files or not required.is_file():
            errors.append(f"missing required root file: {required.name}")

    if len(files) > MAX_FILES:
        errors.append(f"too many files: {len(files)} > {MAX_FILES}")

    total_bytes = sum(path.stat().st_size for path in files if path.is_file())
    if total_bytes > MAX_BYTES:
        errors.append(f"package too large: {total_bytes} > {MAX_BYTES} bytes")

    for path in files:
        relative = path.relative_to(root)
        if path.name not in TEXT_NAMES and path.suffix.lower() not in TEXT_SUFFIXES:
            errors.append(f"unsupported non-text file type: {relative}")
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"file is not UTF-8 text: {relative}")

    if errors:
        print("Marvis package validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Marvis package validation passed: {len(files)} files, "
        f"{total_bytes / 1024 / 1024:.2f} MB, UTF-8 text only."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
