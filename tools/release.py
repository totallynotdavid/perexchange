# ruff: file-ignore[implicit-namespace-package]
"""Release perexchange: bump the version, lock, check, commit, tag and push.

Usage: `mise run release VERSION [--dry-run]`

`--dry-run` runs the preconditions and prints the steps without changing anything. The
release workflow starts from the pushed tag and repeats the version check.
"""

import argparse
import re
import subprocess
import sys

from collections.abc import Callable
from pathlib import Path

from tomli import loads


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = Path("packages/core/pyproject.toml")
LOCKFILE = Path("uv.lock")
BRANCH = "master"
REMOTE = "origin"

_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_VERSION_LINE = re.compile(r'^version = "[^"]*"$', re.MULTILINE)


class ReleaseError(Exception):
    pass


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = f"git {' '.join(args)} failed: {result.stderr.strip()}"
        raise ReleaseError(msg)
    return result.stdout.strip()


def parse_version(text: str) -> tuple[int, int, int]:
    match = _VERSION.fullmatch(text)
    if match is None:
        msg = f"version must look like 2.1.0, got {text!r}"
        raise ReleaseError(msg)
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def project_version(pyproject_text: str) -> str:
    version: str = loads(pyproject_text)["project"]["version"]
    return version


def check_ready(root: Path, version: str) -> None:
    """Fail unless `master` is clean, matches the remote, and `version` is new."""
    current = project_version((root / PYPROJECT).read_text(encoding="utf-8"))
    if parse_version(version) <= parse_version(current):
        msg = f"version {version} must be greater than the current {current}"
        raise ReleaseError(msg)

    branch = git(root, "branch", "--show-current")
    if branch != BRANCH:
        msg = f"release from {BRANCH}, not {branch or 'a detached HEAD'}"
        raise ReleaseError(msg)
    if git(root, "status", "--porcelain"):
        msg = "the working tree has uncommitted changes"
        raise ReleaseError(msg)

    git(root, "fetch", REMOTE, BRANCH)
    if git(root, "rev-parse", "HEAD") != git(root, "rev-parse", f"{REMOTE}/{BRANCH}"):
        msg = f"{BRANCH} differs from {REMOTE}/{BRANCH}; pull or push first"
        raise ReleaseError(msg)

    tag = f"v{version}"
    if git(root, "tag", "--list", tag):
        msg = f"tag {tag} already exists"
        raise ReleaseError(msg)
    if git(root, "ls-remote", "--tags", REMOTE, f"refs/tags/{tag}"):
        msg = f"tag {tag} already exists on {REMOTE}"
        raise ReleaseError(msg)


def set_version(root: Path, version: str) -> None:
    path = root / PYPROJECT
    text, count = _VERSION_LINE.subn(f'version = "{version}"', path.read_text("utf-8"))
    if count != 1:
        msg = f"expected one version line in {PYPROJECT}, found {count}"
        raise ReleaseError(msg)
    path.write_text(text, encoding="utf-8")


def commit_and_tag(root: Path, version: str) -> None:
    git(root, "add", str(PYPROJECT), str(LOCKFILE))
    git(root, "commit", "-m", f"build: release perexchange {version}")
    git(root, "tag", "-a", f"v{version}", "-m", f"Release perexchange {version}")


def verify_files(root: Path, version: str) -> None:
    """Check the files the release commit will hold, as the release workflow does."""
    packaged = project_version((root / PYPROJECT).read_text(encoding="utf-8"))
    if packaged != version:
        msg = f"{PYPROJECT} holds version {packaged}"
        raise ReleaseError(msg)
    lock = (root / LOCKFILE).read_text(encoding="utf-8")
    if f'name = "perexchange"\nversion = "{version}"' not in lock:
        msg = f"{LOCKFILE} does not lock perexchange {version}"
        raise ReleaseError(msg)


def push(root: Path, version: str) -> None:
    git(root, "push", "--atomic", REMOTE, BRANCH, f"v{version}")


def release(
    root: Path,
    version: str,
    lock: Callable[[], None],
    check: Callable[[], None],
) -> None:
    check_ready(root, version)

    start = git(root, "rev-parse", "HEAD")
    try:
        set_version(root, version)
        lock()
        verify_files(root, version)
        check()
        commit_and_tag(root, version)
        push(root, version)
    except BaseException:
        restore(root, start, f"v{version}")
        raise


def restore(root: Path, start: str, tag: str) -> None:
    """Return to the clean `start` commit that `check_ready` verified."""
    if git(root, "tag", "--list", tag):
        git(root, "tag", "--delete", tag)
    git(root, "reset", "--hard", start)


def run(root: Path, *command: str) -> Callable[[], None]:
    def step() -> None:
        print(f"$ {' '.join(command)}", flush=True)
        try:
            subprocess.run(command, cwd=root, check=True)
        except subprocess.CalledProcessError as error:
            msg = f"{' '.join(command)} exited with {error.returncode}"
            raise ReleaseError(msg) from error

    return step


def main() -> int:
    parser = argparse.ArgumentParser(description="Release the perexchange package.")
    parser.add_argument("version", help="the new version, for example 2.1.0")
    parser.add_argument("--dry-run", action="store_true", help="check and stop")
    args = parser.parse_args()

    try:
        if args.dry_run:
            check_ready(ROOT, args.version)
            print(f"Ready to release perexchange {args.version} from {BRANCH}.")
            return 0
        release(
            ROOT,
            args.version,
            lock=run(ROOT, "uv", "lock"),
            check=run(ROOT, "mise", "run", "check"),
        )
    except ReleaseError as error:
        print(f"Release failed: {error}", file=sys.stderr)
        return 1

    print(f"Pushed v{args.version}. The release workflow publishes it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
