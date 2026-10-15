# ruff: file-ignore[implicit-namespace-package]
"""Record a snapshot of every source on a fixed beat, and publish each one.

Usage: `uv run python tools/collect.py [--data-dir site/data] [--minutes 330]`

Runs for `--minutes`, waking every `--interval` minutes. At each wake it asks
`tools/hours.py` whether the houses are due, fetches with `tools/snapshot.py`, and pushes
the new snapshot to the data branch as one commit. A fetch that returns no rate is
logged and skipped. A failed push stops the run, so the next run starts from the new head.

The data directory must be a checkout of the data branch that no other process writes.
"""

import argparse
import asyncio
import subprocess
import sys
import time

from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from pathlib import Path

import hours
import snapshot


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "site" / "data"

Record = Callable[[Path], Coroutine[object, object, object]]


def git(data_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            *args,
        ],
        cwd=data_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def publish(data_dir: Path, remote: str, branch: str, moment: datetime) -> None:
    """Commit what the snapshot wrote and push it. Nothing changed means nothing to push."""
    git(data_dir, "add", "--all")
    if git(data_dir, "status", "--porcelain").stdout == "":
        return
    git(data_dir, "commit", "--message", f"data: snapshot {snapshot.utc_iso(moment)}")
    git(data_dir, "push", remote, f"HEAD:{branch}")


def collect(
    data_dir: Path,
    *,
    minutes: float,
    interval: float,
    remote: str = "origin",
    branch: str = "data",
    record: Record | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Run the beat and return how many snapshots it published."""
    record = record or snapshot.run
    step = timedelta(minutes=interval)
    deadline = now() + timedelta(minutes=minutes)
    slot = now()
    published = 0

    while True:
        moment = now()
        decision = hours.decide(data_dir, moment)
        print(
            f"{snapshot.utc_iso(moment)} {'fetching' if decision.fetch else 'skipping'}:"
            f" {decision.reason}",
            file=sys.stderr,
        )
        if decision.fetch:
            try:
                asyncio.run(record(data_dir))
            except snapshot.SnapshotError as error:
                print(f"snapshot failed: {error}", file=sys.stderr)
            else:
                publish(data_dir, remote, branch, moment)
                published += 1

        # A slow fetch can pass a slot. Skip it rather than fetch twice in a row.
        slot += step
        while slot <= now():
            slot += step
        if slot > deadline:
            return published
        sleep((slot - now()).total_seconds())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--minutes", type=float, default=330)
    parser.add_argument("--interval", type=float, default=15)
    args = parser.parse_args()

    published = collect(args.data_dir, minutes=args.minutes, interval=args.interval)
    print(f"published {published} snapshots")


if __name__ == "__main__":
    main()
