"""Run the collector on a fake clock, against captured responses and a real git remote."""

import json
import subprocess
import sys

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path

import perexchange
import pytest

from tests.captured import fixture_client


TOOLS = Path(__file__).parents[4] / "tools"
LIMA = timezone(timedelta(hours=-5))

# The tools import each other by name, as they do when run as scripts.
sys.path.insert(0, str(TOOLS))
collect = import_module("collect")
snapshot = import_module("snapshot")


class Clock:
    """A clock that moves only when the collector sleeps or a fetch takes time."""

    def __init__(self, start: datetime):
        self.moment = start
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self.moment

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.moment += timedelta(seconds=seconds)


def lima(day: int, hour: int, minute: int = 0) -> datetime:
    """A moment in October 2026. The 8th is a Thursday and a public holiday."""
    return datetime(2026, 10, day, hour, minute, tzinfo=LIMA)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def branch(tmp_path):
    """A data directory on a branch whose remote is a bare repository."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", "--initial-branch=data", str(origin))
    data = tmp_path / "data"
    git(tmp_path, "init", "--initial-branch=data", str(data))
    git(data, "remote", "add", "origin", str(origin))
    return data, origin


def recorder(clock: Clock, fetch_time: float = 0.0):
    """Record a snapshot of the captured responses, stamped by the fake clock."""

    async def record(data_dir: Path):
        async with fixture_client() as client:
            report = await perexchange.fetch_rates_report(client=client)
        clock.moment += timedelta(seconds=fetch_time)
        return snapshot.write_snapshot(report, data_dir, clock.now())

    return record


def published_times(origin: Path) -> list[str]:
    log = git(origin, "log", "--format=%s", "data")
    return [line.removeprefix("data: snapshot ") for line in log.splitlines()][::-1]


def test_an_open_day_publishes_a_snapshot_at_every_beat(branch):
    data, origin = branch
    clock = Clock(lima(9, 10))

    published = collect.collect(
        data,
        minutes=60,
        interval=15,
        record=recorder(clock),
        now=clock.now,
        sleep=clock.sleep,
    )

    assert published == 5
    assert clock.sleeps == [900.0] * 4
    assert published_times(origin) == [
        "2026-10-09T15:00:00Z",
        "2026-10-09T15:15:00Z",
        "2026-10-09T15:30:00Z",
        "2026-10-09T15:45:00Z",
        "2026-10-09T16:00:00Z",
    ]


def test_each_published_commit_carries_the_snapshot_and_the_history(branch):
    data, origin = branch
    clock = Clock(lima(9, 10))

    collect.collect(
        data,
        minutes=15,
        interval=15,
        record=recorder(clock),
        now=clock.now,
        sleep=clock.sleep,
    )

    head = json.loads(git(origin, "show", "data:latest.json"))
    history = git(origin, "show", "data:history/2026-10-09.jsonl").splitlines()
    assert head["generated_at"] == "2026-10-09T15:15:00Z"
    assert [json.loads(line)["t"] for line in history] == [
        "2026-10-09T15:00:00Z",
        "2026-10-09T15:15:00Z",
    ]


def test_a_closed_day_publishes_about_once_an_hour(branch):
    data, origin = branch
    clock = Clock(lima(11, 15))

    published = collect.collect(
        data,
        minutes=120,
        interval=15,
        record=recorder(clock),
        now=clock.now,
        sleep=clock.sleep,
    )

    assert published == 3
    assert published_times(origin) == [
        "2026-10-11T20:00:00Z",
        "2026-10-11T21:00:00Z",
        "2026-10-11T22:00:00Z",
    ]


def test_a_fetch_that_returns_nothing_is_skipped_and_the_beat_goes_on(branch, capsys):
    data, origin = branch
    clock = Clock(lima(9, 10))
    working = recorder(clock)
    calls = 0

    async def record(data_dir: Path):
        nonlocal calls
        calls += 1
        if calls == 1:
            msg = "no source returned a rate (failed: all)"
            raise snapshot.SnapshotError(msg)
        return await working(data_dir)

    published = collect.collect(
        data, minutes=15, interval=15, record=record, now=clock.now, sleep=clock.sleep
    )

    assert published == 1
    assert published_times(origin) == ["2026-10-09T15:15:00Z"]
    assert "no source returned a rate" in capsys.readouterr().err


def test_a_slow_fetch_skips_the_beat_it_overran(branch):
    data, _origin = branch
    clock = Clock(lima(9, 10))

    published = collect.collect(
        data,
        minutes=45,
        interval=15,
        record=recorder(clock, fetch_time=40 * 60),
        now=clock.now,
        sleep=clock.sleep,
    )

    # The first fetch ends at minute 40, so the beats at 15 and 30 pass unused.
    assert clock.sleeps[0] == pytest.approx(300)
    assert published == 2


def test_a_rejected_push_stops_the_run(branch):
    data, origin = branch
    clock = Clock(lima(9, 10))
    other = origin.parent / "other"
    git(origin.parent, "clone", str(origin), str(other))
    (other / "x").write_text("x", encoding="utf-8")
    git(other, "add", "x")
    git(
        other,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-m",
        "another writer",
    )
    git(other, "push", "origin", "HEAD:data")

    with pytest.raises(subprocess.CalledProcessError):
        collect.collect(
            data,
            minutes=60,
            interval=15,
            record=recorder(clock),
            now=clock.now,
            sleep=clock.sleep,
        )

    assert published_times(origin) == ["another writer"]
