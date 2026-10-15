# ruff: file-ignore[implicit-namespace-package]
"""Report how often the snapshots were recorded.

Usage: `uv run python tools/history_report.py [--data-dir site/data]`

Reads `history/*.jsonl` and prints, for each UTC day, the number of snapshots and the
median and maximum gap in minutes between consecutive ones. A gap counts for the day of
the snapshot that ends it. The last line covers every snapshot. The collector aims for a
snapshot every 15 minutes while the houses are open.
"""

import argparse
import json
import statistics
import sys

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "site" / "data"


def snapshot_times(data_dir: Path) -> list[datetime]:
    """When each snapshot was fetched, oldest first."""
    times = [
        datetime.strptime(json.loads(line)["t"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=UTC
        )
        for path in sorted((data_dir / "history").glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    return sorted(times)


def summary(count: int, gaps: list[float]) -> str:
    snapshots = f"{count:>4} {'snapshot ' if count == 1 else 'snapshots'}"
    if not gaps:
        return f"{snapshots}   median gap -   max gap -"
    return (
        f"{snapshots}   median gap {statistics.median(gaps):.0f} min"
        f"   max gap {max(gaps):.0f} min"
    )


def report(times: list[datetime]) -> list[str]:
    counts: defaultdict[str, int] = defaultdict(int)
    gaps: defaultdict[str, list[float]] = defaultdict(list)
    for index, moment in enumerate(times):
        day = moment.date().isoformat()
        counts[day] += 1
        if index > 0:
            gaps[day].append((moment - times[index - 1]).total_seconds() / 60)

    lines = [f"{day}  {summary(counts[day], gaps[day])}" for day in sorted(counts)]
    every_gap = [gap for day_gaps in gaps.values() for gap in day_gaps]
    lines.append(f"all         {summary(len(times), every_gap)}")
    return lines


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)

    times = snapshot_times(args.data_dir)
    if not times:
        sys.exit(f"no snapshots found in {args.data_dir / 'history'}")
    print("\n".join(report(times)))


if __name__ == "__main__":
    main()
