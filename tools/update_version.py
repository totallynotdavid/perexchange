#!/usr/bin/env python3
"""
Update version in pyproject.toml.
Usage: python tools/update_version.py --version 1.2.3
"""

import argparse
import re
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

    text = pyproject.read_text(encoding="utf8")
    new_text, count = re.subn(
        r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', text
    )
    if count == 0:
        print("No version line updated", file=sys.stderr)
        return 2

    pyproject.write_text(new_text, encoding="utf8")
    print(f"Updated version to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
