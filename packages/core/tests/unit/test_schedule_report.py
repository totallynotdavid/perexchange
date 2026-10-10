"""Run the schedule report on `gh run list` JSON, as the command line does."""

import importlib.util
import json
import os

from pathlib import Path

import pytest


TOOL = Path(__file__).parents[4] / "tools" / "schedule_report.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("schedule_report_tool", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


schedule_report = load_tool()


def write_runs(path: Path, stamps: list[str], event: str = "schedule") -> Path:
    runs = [{"createdAt": stamp, "event": event} for stamp in stamps]
    path.write_text(json.dumps(runs), encoding="utf-8")
    return path


def test_it_prints_runs_and_gaps_for_each_day_and_for_all(tmp_path, capsys):
    # `gh run list` lists the newest run first.
    runs = write_runs(
        tmp_path / "runs.json",
        [
            "2026-10-09T01:00:00Z",
            "2026-10-08T23:30:00Z",
            "2026-10-08T23:00:00Z",
            "2026-10-08T22:00:00Z",
        ],
    )

    schedule_report.main(["--input", str(runs)])

    assert capsys.readouterr().out.splitlines() == [
        "2026-10-08     3 runs   median gap 45 min   max gap 60 min",
        "2026-10-09     1 run    median gap 90 min   max gap 90 min",
        "all            4 runs   median gap 60 min   max gap 90 min",
    ]


def test_a_single_run_has_no_gap(tmp_path, capsys):
    runs = write_runs(tmp_path / "runs.json", ["2026-10-08T22:00:00Z"])

    schedule_report.main(["--input", str(runs)])

    assert capsys.readouterr().out.splitlines() == [
        "2026-10-08     1 run    median gap -   max gap -",
        "all            1 run    median gap -   max gap -",
    ]


def test_runs_of_other_events_do_not_count(tmp_path):
    runs = write_runs(tmp_path / "runs.json", ["2026-10-08T22:00:00Z"], "push")

    with pytest.raises(SystemExit, match="no scheduled runs"):
        schedule_report.main(["--input", str(runs)])


def install_fake_gh(tmp_path: Path, monkeypatch, limit: int) -> None:
    """Put a `gh` on PATH that answers only the command the tool should send."""
    gh = tmp_path / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        f'test "$*" = "run list --workflow site --event schedule --limit {limit}'
        ' --json createdAt,event" || exit 1\n'
        'echo \'[{"createdAt": "2026-10-08T22:00:00Z", "event": "schedule"}]\'\n',
        encoding="utf-8",
    )
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")


@pytest.mark.skipif(os.name == "nt", reason="the fake gh is a shell script")
def test_it_asks_gh_for_the_scheduled_runs_of_the_workflow(
    tmp_path, monkeypatch, capsys
):
    install_fake_gh(tmp_path, monkeypatch, limit=50)

    schedule_report.main(["--workflow", "site", "--limit", "50"])

    output = capsys.readouterr()
    assert "all            1 run " in output.out
    assert output.err == ""


@pytest.mark.skipif(os.name == "nt", reason="the fake gh is a shell script")
def test_it_says_when_the_limit_cut_off_older_runs(tmp_path, monkeypatch, capsys):
    install_fake_gh(tmp_path, monkeypatch, limit=1)

    schedule_report.main(["--limit", "1"])

    assert "only the newest 1 runs are counted" in capsys.readouterr().err
