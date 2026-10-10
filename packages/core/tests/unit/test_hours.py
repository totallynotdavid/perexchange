"""Ask the hours tool whether a scheduled run should fetch, for moments in Lima time."""

import importlib.util
import json

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


TOOL = Path(__file__).parents[4] / "tools" / "hours.py"
LIMA = timezone(timedelta(hours=-5))


def load_tool():
    spec = importlib.util.spec_from_file_location("hours_tool", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hours = load_tool()


def lima(day: int, hour: int, minute: int = 0) -> datetime:
    """A moment in October 2026. The 8th is a Thursday and a public holiday."""
    return datetime(2026, 10, day, hour, minute, tzinfo=LIMA)


def record_fetch(data_dir: Path, at: datetime) -> None:
    stamp = at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (data_dir / "latest.json").write_text(
        json.dumps({"generated_at": stamp}), encoding="utf-8"
    )


@pytest.mark.parametrize(
    ("moment", "closed"),
    [
        (lima(10, 12, 59), False),
        (lima(10, 13, 1), True),
        (lima(10, 13, 0), True),
        (lima(11, 0, 0), True),
        (lima(11, 23, 59), True),
        (lima(12, 0, 0), False),
        (lima(9, 15), False),
        (lima(8, 10), True),
        (lima(7, 23, 59), False),
        (lima(9, 3), False),
    ],
)
def test_the_houses_are_closed_from_saturday_afternoon_and_on_sundays_and_holidays(
    moment, closed
):
    assert (hours.closed_reason(moment) is not None) is closed


def test_saturday_closes_at_one_in_lima_whatever_zone_the_runner_reports():
    before = lima(10, 12, 59).astimezone(timezone.utc)
    after = lima(10, 13, 1).astimezone(timezone.utc)

    assert hours.closed_reason(before) is None
    assert hours.closed_reason(after) == "Saturday after 13:00"


def test_a_holiday_and_a_sunday_name_their_reason():
    assert hours.closed_reason(lima(8, 10)) == "a public holiday"
    assert hours.closed_reason(lima(11, 10)) == "Sunday"


def test_an_open_day_fetches_on_every_run(tmp_path):
    record_fetch(tmp_path, lima(9, 14, 59))

    decision = hours.decide(tmp_path, lima(9, 15, 0))

    assert decision.fetch is True


def test_just_before_saturday_closing_fetches_and_just_after_waits(tmp_path):
    record_fetch(tmp_path, lima(10, 12, 50))

    assert hours.decide(tmp_path, lima(10, 12, 59)).fetch is True
    assert hours.decide(tmp_path, lima(10, 13, 1)).fetch is False


@pytest.mark.parametrize("moment", [lima(11, 15), lima(8, 15)])
def test_a_closed_day_fetches_once_the_last_fetch_is_nearly_an_hour_old(
    tmp_path, moment
):
    record_fetch(tmp_path, moment - timedelta(minutes=49))
    assert hours.decide(tmp_path, moment).fetch is False

    record_fetch(tmp_path, moment - timedelta(minutes=50))
    assert hours.decide(tmp_path, moment).fetch is True


def test_a_closed_day_fetches_when_nothing_is_recorded(tmp_path):
    assert hours.decide(tmp_path, lima(11, 15)).fetch is True


def test_a_closed_day_fetches_when_the_recorded_snapshot_cannot_be_read(tmp_path):
    (tmp_path / "latest.json").write_text("{", encoding="utf-8")

    assert hours.decide(tmp_path, lima(11, 15)).fetch is True


def test_the_command_prints_the_answer_for_the_workflow_output(tmp_path, capsys):
    record_fetch(tmp_path, lima(11, 14, 30))

    hours.main(["--data-dir", str(tmp_path)], now=lima(11, 15))
    skipped = capsys.readouterr()
    hours.main(["--data-dir", str(tmp_path)], now=lima(11, 16))
    fetched = capsys.readouterr()

    assert skipped.out == "fetch=false\n"
    assert "Sunday" in skipped.err
    assert fetched.out == "fetch=true\n"
