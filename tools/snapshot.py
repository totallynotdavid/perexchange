# ruff: file-ignore[implicit-namespace-package]
"""Fetch every source once and record the result for the site.

Usage: `uv run python tools/snapshot.py [--data-dir site/data]`

Writes two things under the data directory. `latest.json` is the newest fetch.
`history/YYYY-MM-DD.jsonl` gets one more line per fetch, keyed by the UTC day of the
fetch, so history is append-only and a day's file is the only one a run touches.

The tool exits with an error and writes nothing when no source returned a rate, so a
scheduled run never replaces good data with an empty snapshot.
"""

import argparse
import asyncio
import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path

import httpx
import perexchange

from perexchange import ExchangeRate, FetchReport, SourceFailure


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "site" / "data"

# These statuses indicate that the runner's address was refused or rate-limited.
BLOCKING_STATUSES = frozenset({401, 403, 429})

CROSSED = "CrossedQuote"

_NOT_ALNUM = re.compile(r"[^a-z0-9]+")


class SnapshotError(Exception):
    pass


def quote_id(rate: ExchangeRate) -> str:
    """A URL-safe key for a quote, equal across sources that list the same house."""
    return _NOT_ALNUM.sub("-", rate.name.lower()).strip("-")


def failure_reason(failure: SourceFailure) -> str:
    """Why a source returned nothing, in the words the site can show.

    `blocked` is a source that refuses this address, `changed` one whose response no
    longer parses, `timeout` one that answered too slowly, `error` one that answered with
    another error status, `invalid` one whose quote pays more than it charges, and
    `unreachable` one that did not answer at all.
    """
    if failure.error_type == CROSSED:
        return "invalid"
    if failure.status_code in BLOCKING_STATUSES:
        return "blocked"
    if failure.status_code is not None:
        return "error"
    if failure.error_type == "SourceParseError":
        return "changed"
    if failure.error_type.endswith("Timeout") or failure.error_type == "TimeoutError":
        return "timeout"
    return "unreachable"


def utc_iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def unique_rates(rates: tuple[ExchangeRate, ...]) -> list[ExchangeRate]:
    """Keep the first rate for each quote ID so a history line has one price per key."""
    seen: set[str] = set()
    kept: list[ExchangeRate] = []
    for rate in rates:
        key = quote_id(rate)
        if key not in seen:
            seen.add(key)
            kept.append(rate)
    return kept


def latest_document(report: FetchReport, fetched_at: datetime) -> dict[str, object]:
    return {
        "generated_at": utc_iso(fetched_at),
        "library_version": perexchange.__version__,
        "rates": [
            {
                "id": quote_id(rate),
                "source": rate.source,
                "name": rate.name,
                "buy": rate.buy_price,
                "sell": rate.sell_price,
                "timestamp": utc_iso(rate.timestamp),
            }
            for rate in unique_rates(report.rates)
        ],
        "failures": [
            {
                "source": failure.source,
                "reason": failure_reason(failure),
                "error_type": failure.error_type,
                "message": failure.message.splitlines()[0] if failure.message else "",
            }
            for failure in report.failures
        ],
    }


def age_minutes(rate: ExchangeRate, fetched_at: datetime) -> int:
    return max(0, round((fetched_at - rate.timestamp).total_seconds() / 60))


def history_line(report: FetchReport, fetched_at: datetime) -> str:
    """One fetch as `{"t": time, "r": {id: [buy, sell, minutes]}, "f": [source, ...]}`.

    The minutes are the quote age. `f` lists sources that returned nothing.
    """
    prices = {
        quote_id(rate): [rate.buy_price, rate.sell_price, age_minutes(rate, fetched_at)]
        for rate in unique_rates(report.rates)
    }
    line = {
        "t": utc_iso(fetched_at),
        "r": prices,
        "f": [failure.source for failure in report.failures],
    }
    return json.dumps(line, separators=(",", ":"))


def drop_crossed(report: FetchReport) -> FetchReport:
    """Move a quote whose house pays more than it charges from the rates to the failures.

    A round trip through such a quote would earn money, so one side is wrong and the
    quote must not take part in a ranking.
    """
    kept = tuple(rate for rate in report.rates if rate.buy_price <= rate.sell_price)
    crossed = tuple(
        SourceFailure(
            rate.name,
            CROSSED,
            f"pays {rate.buy_price:g} for a dollar and charges {rate.sell_price:g}",
        )
        for rate in report.rates
        if rate.buy_price > rate.sell_price
    )
    return FetchReport(rates=kept, failures=report.failures + crossed)


def write_snapshot(
    report: FetchReport, data_dir: Path, fetched_at: datetime
) -> FetchReport:
    report = drop_crossed(report)
    if not report.rates:
        failed = ", ".join(failure.source for failure in report.failures) or "none"
        msg = f"no source returned a rate (failed: {failed})"
        raise SnapshotError(msg)

    fetched_at = fetched_at.astimezone(timezone.utc)
    history_dir = data_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    day_file = history_dir / f"{fetched_at:%Y-%m-%d}.jsonl"
    with day_file.open("a", encoding="utf-8") as file:
        file.write(history_line(report, fetched_at) + "\n")

    # Replace the file in one step so a reader never sees half a document.
    latest = data_dir / "latest.json"
    pending = latest.with_suffix(".json.tmp")
    document = latest_document(report, fetched_at)
    pending.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    pending.replace(latest)
    return report


async def run(data_dir: Path, client: httpx.AsyncClient | None = None) -> FetchReport:
    report = await perexchange.fetch_rates_report(client=client)
    return write_snapshot(report, data_dir, datetime.now(timezone.utc))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    try:
        report = asyncio.run(run(args.data_dir))
    except SnapshotError as error:
        print(f"snapshot failed: {error}", file=sys.stderr)
        sys.exit(1)

    for failure in report.failures:
        print(f"skipped {failure.source}: {failure.message}", file=sys.stderr)
    print(f"recorded {len(report.rates)} rates in {args.data_dir}")


if __name__ == "__main__":
    main()
