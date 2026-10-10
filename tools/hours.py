# ruff: file-ignore[implicit-namespace-package]
"""Decide whether a scheduled run should fetch the exchange houses now.

Usage: `uv run python tools/hours.py [--data-dir site/data]`

Prints `fetch=true` or `fetch=false` on stdout, for `$GITHUB_OUTPUT`, and the reason on
stderr. The rule is in docs/architecture.md, under "Opening hours".
"""

import argparse
import json
import sys

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta, timezone
from pathlib import Path

import holidays


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "site" / "data"

# Lima has no daylight saving time.
LIMA = timezone(timedelta(hours=-5))

SATURDAY_CLOSING = time(13)

# Keep it below OLD_AFTER_MINUTES in site/src/lib/market.ts.
CLOSED_INTERVAL = timedelta(minutes=50)

SATURDAY = 5
SUNDAY = 6


@dataclass(frozen=True)
class Decision:
    fetch: bool
    reason: str


def closed_reason(moment: datetime) -> str | None:
    """Why the houses are closed at this moment, or None when they are open."""
    local = moment.astimezone(LIMA)
    if local.date() in holidays.country_holidays("PE", years=local.year):
        return "a public holiday"
    if local.weekday() == SUNDAY:
        return "Sunday"
    if local.weekday() == SATURDAY and local.time() >= SATURDAY_CLOSING:
        return f"Saturday after {SATURDAY_CLOSING:%H:%M}"
    return None


def last_fetch(data_dir: Path) -> datetime | None:
    """When the newest snapshot was fetched, or None when there is no readable one."""
    try:
        text = (data_dir / "latest.json").read_text(encoding="utf-8")
        stamp = json.loads(text)["generated_at"]
        return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        return None


def decide(data_dir: Path, now: datetime) -> Decision:
    reason = closed_reason(now)
    if reason is None:
        return Decision(fetch=True, reason="the houses are open")

    fetched = last_fetch(data_dir)
    if fetched is None:
        return Decision(
            fetch=True,
            reason=f"the houses are closed ({reason}) and nothing is recorded",
        )

    elapsed = now - fetched
    minutes = round(elapsed.total_seconds() / 60)
    if elapsed >= CLOSED_INTERVAL:
        return Decision(
            fetch=True, reason=f"closed ({reason}), last fetch {minutes} min ago"
        )
    return Decision(
        fetch=False, reason=f"closed ({reason}), last fetch only {minutes} min ago"
    )


def main(argv: Sequence[str] | None = None, now: datetime | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)

    decision = decide(args.data_dir, now or datetime.now(UTC))
    print(
        f"{'fetching' if decision.fetch else 'skipping'}: {decision.reason}",
        file=sys.stderr,
    )
    print(f"fetch={str(decision.fetch).lower()}")


if __name__ == "__main__":
    main()
