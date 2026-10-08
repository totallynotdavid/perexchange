"""Run the snapshot tool against captured source responses and a throwaway directory."""

import importlib.util
import json

from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from perexchange import ExchangeRate, FetchReport, SourceFailure

from tests.captured import fixture_client


TOOL = Path(__file__).parents[4] / "tools" / "snapshot.py"
MORNING = datetime(2026, 10, 8, 9, 30, tzinfo=timezone(timedelta(hours=-5)))


def load_tool():
    spec = importlib.util.spec_from_file_location("snapshot_tool", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshot = load_tool()


def quote(source: str, name: str, buy: float, sell: float) -> ExchangeRate:
    return ExchangeRate(
        source=source,
        name=name,
        buy_price=buy,
        sell_price=sell,
        timestamp=MORNING,
    )


def history_lines(data_dir: Path, day: str) -> list[dict]:
    text = (data_dir / "history" / f"{day}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_latest_lists_every_rate_with_utc_times_and_the_failures(tmp_path):
    report = FetchReport(
        rates=(quote("tkambio", "tkambio_5000", 3.425, 3.452),),
        failures=(SourceFailure("okane", "HTTPStatusError", "403 Forbidden"),),
    )

    snapshot.write_snapshot(report, tmp_path, MORNING)

    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["generated_at"] == "2026-10-08T14:30:00Z"
    assert latest["rates"] == [
        {
            "id": "tkambio-5000",
            "source": "tkambio",
            "name": "tkambio_5000",
            "buy": 3.425,
            "sell": 3.452,
            "timestamp": "2026-10-08T14:30:00Z",
        }
    ]
    assert latest["failures"] == [
        {"source": "okane", "error_type": "HTTPStatusError", "message": "403 Forbidden"}
    ]


def test_each_fetch_appends_one_line_to_the_utc_day_it_happened_in(tmp_path):
    report = FetchReport(rates=(quote("a", "a", 3.3, 3.4),), failures=())
    late_evening = datetime(2026, 10, 8, 23, 50, tzinfo=timezone(timedelta(hours=-5)))

    snapshot.write_snapshot(report, tmp_path, MORNING)
    snapshot.write_snapshot(report, tmp_path, MORNING + timedelta(minutes=15))
    snapshot.write_snapshot(report, tmp_path, late_evening)

    assert [line["t"] for line in history_lines(tmp_path, "2026-10-08")] == [
        "2026-10-08T14:30:00Z",
        "2026-10-08T14:45:00Z",
    ]
    assert [line["t"] for line in history_lines(tmp_path, "2026-10-09")] == [
        "2026-10-09T04:50:00Z"
    ]


def test_history_keeps_buy_then_sell_for_each_quote(tmp_path):
    report = FetchReport(
        rates=(
            quote("a", "a", 3.3, 3.4),
            quote("cuanto", "Gordito digital", 3.35, 3.45),
        ),
        failures=(),
    )

    snapshot.write_snapshot(report, tmp_path, MORNING)

    [line] = history_lines(tmp_path, "2026-10-08")
    assert line["r"] == {"a": [3.3, 3.4, 0], "gordito-digital": [3.35, 3.45, 0]}


def test_history_records_how_old_each_quote_was_when_fetched(tmp_path):
    stale = ExchangeRate(
        source="chapacambio",
        name="chapacambio",
        buy_price=3.433,
        sell_price=3.464,
        timestamp=MORNING - timedelta(hours=12, minutes=14),
    )
    report = FetchReport(rates=(stale, quote("a", "a", 3.3, 3.4)), failures=())

    snapshot.write_snapshot(report, tmp_path, MORNING)

    [line] = history_lines(tmp_path, "2026-10-08")
    assert line["r"]["chapacambio"] == [3.433, 3.464, 734]
    assert line["r"]["a"][2] == 0


def test_a_house_listed_twice_keeps_its_first_price(tmp_path):
    report = FetchReport(
        rates=(
            quote("tucambista", "tucambista", 3.43, 3.46),
            quote("cuanto", "Tucambista", 3.40, 3.50),
        ),
        failures=(),
    )

    snapshot.write_snapshot(report, tmp_path, MORNING)

    [line] = history_lines(tmp_path, "2026-10-08")
    assert line["r"] == {"tucambista": [3.43, 3.46, 0]}
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert [rate["source"] for rate in latest["rates"]] == ["tucambista"]


def test_a_fetch_with_no_rates_leaves_earlier_data_untouched(tmp_path):
    good = FetchReport(rates=(quote("a", "a", 3.3, 3.4),), failures=())
    snapshot.write_snapshot(good, tmp_path, MORNING)
    before = (tmp_path / "latest.json").read_text(encoding="utf-8")
    empty = FetchReport(
        rates=(), failures=(SourceFailure("a", "TransportError", "timed out"),)
    )

    with pytest.raises(snapshot.SnapshotError, match="failed: a"):
        snapshot.write_snapshot(empty, tmp_path, MORNING + timedelta(minutes=15))

    assert (tmp_path / "latest.json").read_text(encoding="utf-8") == before
    assert len(history_lines(tmp_path, "2026-10-08")) == 1


async def test_a_live_style_run_records_what_the_library_returned(tmp_path):
    async with fixture_client() as client:
        report = await snapshot.run(tmp_path, client)

    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert report.rates
    assert [rate["id"] for rate in latest["rates"]] == [
        snapshot.quote_id(rate) for rate in report.rates
    ]
    assert [rate["buy"] for rate in latest["rates"]] == [
        rate.buy_price for rate in report.rates
    ]
    assert {failure["source"] for failure in latest["failures"]} == {
        failure.source for failure in report.failures
    }
    [line] = list((tmp_path / "history").glob("*.jsonl"))
    assert set(json.loads(line.read_text(encoding="utf-8"))["r"]) == {
        rate["id"] for rate in latest["rates"]
    }


async def test_a_run_where_every_source_fails_exits_without_writing(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(snapshot.SnapshotError, match="no source returned a rate"):
            await snapshot.run(tmp_path, client)

    assert list(tmp_path.iterdir()) == []
