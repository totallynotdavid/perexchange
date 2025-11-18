#!/usr/bin/env python3

import shutil
import subprocess
import sys

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "pkg" / "core"


def rmtree_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def main() -> int:
    print("Cleaning build artifacts")
    rmtree_if_exists(PKG_DIR / "dist")
    rmtree_if_exists(PKG_DIR / "build")
    rmtree_if_exists(ROOT / "perexchange.egg-info")

    print("Building package")
    try:
        subprocess.check_call([sys.executable, "-m", "build"], cwd=str(PKG_DIR))
        print("Build successful")
        return 0
    except subprocess.CalledProcessError as e:
        print("Build failed:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
