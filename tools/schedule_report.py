# ruff: file-ignore[implicit-namespace-package]
"""Report how often GitHub ran the scheduled snapshot workflow.

Usage: `uv run python tools/schedule_report.py [--workflow site] [--limit 500]`

Reads the scheduled runs of a workflow with `gh run list` and prints, for each UTC day,
the number of runs and the median and maximum gap in minutes between consecutive runs.
A gap counts for the day of the run that ends it. The last line covers all runs.
`--input FILE` reads the JSON of `gh run list --json createdAt,event` instead, and `-`
reads it from stdin.
"""

import argparse
import json
import statistics
import subprocess
import sys

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path


def fetch_runs(workflow: str, limit: int) -> str:
    command = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow,
        "--event",
        "schedule",
        "--limit",
        str(limit),
        "--json",
        "createdAt,event",
    ]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def run_times(text: str) -> list[datetime]:
    """When each scheduled run was created, oldest first."""
    times = [
        datetime.strptime(run["createdAt"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        for run in json.loads(text)
        if run.get("event", "schedule") == "schedule"
    ]
    return sorted(times)


def summary(count: int, gaps: list[float]) -> str:
    runs = f"{count:>4} {'run ' if count == 1 else 'runs'}"
    if not gaps:
        return f"{runs}   median gap -   max gap -"
    return (
        f"{runs}   median gap {statistics.median(gaps):.0f} min"
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
    parser.add_argument("--workflow", default="site")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--input", help="a file of `gh run list` JSON, or - for stdin")
    args = parser.parse_args(argv)

    if args.input == "-":
        text = sys.stdin.read()
    elif args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = fetch_runs(args.workflow, args.limit)

    times = run_times(text)
    if not times:
        sys.exit("no scheduled runs found")
    if not args.input and len(times) >= args.limit:
        print(
            f"only the newest {args.limit} runs are counted; raise --limit for more",
            file=sys.stderr,
        )
    print("\n".join(report(times)))


if __name__ == "__main__":
    main()
