#!/usr/bin/env python3
"""
Update version, build, commit, tag, and push for release.
Usage: python tools/release.py --version 1.2.3
"""

import argparse
import re
import subprocess
import sys

from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="New version string")
    args = parser.parse_args()

    version = args.version.strip()
    pyproject = Path("pkg/core/pyproject.toml")
    if not pyproject.exists():
        print(f"Missing {pyproject}", file=sys.stderr)
        return 1

    # Update version
    text = pyproject.read_text(encoding="utf8")
    new_text, count = re.subn(
        r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', text
    )
    if count == 0:
        print("No version line updated", file=sys.stderr)
        return 2
    pyproject.write_text(new_text, encoding="utf8")
    print(f"Updated version to {version}")

    # Build
    print("Building package...")
    result = subprocess.run(
        [sys.executable, "-m", "build"], cwd="pkg/core", capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Build failed:", result.stderr, file=sys.stderr)
        return 3
    print("Build successful")

    # Commit
    print("Committing changes...")
    subprocess.run(["git", "add", str(pyproject)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore: bump version to {version}"], check=True
    )

    # Tag
    print("Tagging...")
    subprocess.run(["git", "tag", f"v{version}"], check=True)

    # Push
    print("Pushing...")
    subprocess.run(["git", "push", "origin", "main"], check=True)
    subprocess.run(["git", "push", "origin", f"v{version}"], check=True)

    print("Release complete. CI will publish to PyPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
