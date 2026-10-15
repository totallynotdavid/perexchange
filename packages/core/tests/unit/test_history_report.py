"""Run the history report on a data directory, as the command line does."""

import importlib.util
import json

from pathlib import Path

import pytest


TOOL = Path(__file__).parents[4] / "tools" / "history_report.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("history_report_tool", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history_report = load_tool()


def write_day(data_dir: Path, day: str, stamps: list[str]) -> None:
    history = data_dir / "history"
    history.mkdir(exist_ok=True)
    lines = [json.dumps({"t": stamp, "r": {}, "f": []}) for stamp in stamps]
    (history / f"{day}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_it_prints_snapshots_and_gaps_for_each_day_and_for_all(tmp_path, capsys):
    write_day(tmp_path, "2026-10-08", ["2026-10-08T22:00:00Z", "2026-10-08T23:00:00Z"])
    write_day(tmp_path, "2026-10-09", ["2026-10-09T00:30:00Z", "2026-10-09T00:45:00Z"])

    history_report.main(["--data-dir", str(tmp_path)])

    assert capsys.readouterr().out.splitlines() == [
        "2026-10-08     2 snapshots   median gap 60 min   max gap 60 min",
        "2026-10-09     2 snapshots   median gap 52 min   max gap 90 min",
        "all            4 snapshots   median gap 60 min   max gap 90 min",
    ]


def test_a_single_snapshot_has_no_gap(tmp_path, capsys):
    write_day(tmp_path, "2026-10-08", ["2026-10-08T22:00:00Z"])

    history_report.main(["--data-dir", str(tmp_path)])

    assert capsys.readouterr().out.splitlines() == [
        "2026-10-08     1 snapshot    median gap -   max gap -",
        "all            1 snapshot    median gap -   max gap -",
    ]


def test_an_empty_directory_is_an_error(tmp_path):
    with pytest.raises(SystemExit, match="no snapshots"):
        history_report.main(["--data-dir", str(tmp_path)])
