"""Run the release tool against a throwaway repository and a bare remote."""

import importlib.util
import subprocess

from pathlib import Path

import pytest


TOOL = Path(__file__).parents[4] / "tools" / "release.py"

PYPROJECT = """\
[project]
name = "perexchange"
version = "2.0.0"
"""

LOCKFILE = """\
[[package]]
name = "perexchange"
version = "2.0.0"
source = { editable = "packages/core" }
"""


def load_tool():
    spec = importlib.util.spec_from_file_location("release_tool", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load_tool()


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture(autouse=True)
def git_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Release Test")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "release@example.test")


@pytest.fixture
def repo(tmp_path) -> Path:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    git(tmp_path, "init", "--bare", "-b", "master", str(remote))
    git(tmp_path, "clone", str(remote), str(work))
    git(work, "checkout", "-b", "master")
    (work / "packages/core").mkdir(parents=True)
    (work / "packages/core/pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (work / "uv.lock").write_text(LOCKFILE, encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-m", "start")
    git(work, "push", "-u", "origin", "master")
    return work


def lock_to(repo: Path, version: str):
    def lock() -> None:
        path = repo / "uv.lock"
        path.write_text(
            path.read_text(encoding="utf-8").replace("2.0.0", version), encoding="utf-8"
        )

    return lock


def nothing() -> None:
    return None


def remote_of(repo: Path) -> Path:
    return Path(git(repo, "remote", "get-url", "origin"))


def test_release_pushes_the_commit_and_an_annotated_tag(repo):
    release.release(repo, "2.1.0", lock=lock_to(repo, "2.1.0"), check=nothing)

    remote = remote_of(repo)
    assert git(remote, "log", "-1", "--format=%s", "master") == (
        "build: release perexchange 2.1.0"
    )
    assert git(remote, "cat-file", "-t", "v2.1.0") == "tag"
    assert git(remote, "rev-parse", "v2.1.0^{commit}") == git(
        remote, "rev-parse", "master"
    )
    pyproject = git(remote, "show", "master:packages/core/pyproject.toml")
    assert 'version = "2.1.0"' in pyproject
    assert git(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("version", ["2.0.0", "1.9.9", "2.1", "v2.1.0", "2.1.0rc1"])
def test_rejects_a_version_that_is_not_a_newer_release(repo, version):
    with pytest.raises(release.ReleaseError):
        release.release(repo, version, lock=nothing, check=nothing)

    assert git(remote_of(repo), "tag", "--list") == ""


def test_refuses_a_dirty_tree(repo):
    (repo / "stray.txt").write_text("x", encoding="utf-8")

    with pytest.raises(release.ReleaseError, match="uncommitted"):
        release.release(repo, "2.1.0", lock=nothing, check=nothing)


def test_refuses_another_branch(repo):
    git(repo, "checkout", "-b", "topic")

    with pytest.raises(release.ReleaseError, match="release from master"):
        release.release(repo, "2.1.0", lock=nothing, check=nothing)


def test_refuses_a_master_that_differs_from_the_remote(repo):
    (repo / "later.txt").write_text("x", encoding="utf-8")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "unpushed")

    with pytest.raises(release.ReleaseError, match="differs from origin/master"):
        release.release(repo, "2.1.0", lock=nothing, check=nothing)


def test_refuses_a_tag_that_exists_on_the_remote(repo):
    git(repo, "tag", "v2.1.0")
    git(repo, "push", "origin", "v2.1.0")
    git(repo, "tag", "-d", "v2.1.0")

    with pytest.raises(release.ReleaseError, match="already exists on origin"):
        release.release(repo, "2.1.0", lock=nothing, check=nothing)


def test_a_failed_check_restores_the_files_and_pushes_nothing(repo):
    def failing_check() -> None:
        msg = "mise run check exited with 1"
        raise release.ReleaseError(msg)

    with pytest.raises(release.ReleaseError, match="exited with 1"):
        release.release(repo, "2.1.0", lock=lock_to(repo, "2.1.0"), check=failing_check)

    assert git(repo, "status", "--porcelain") == ""
    assert 'version = "2.0.0"' in (repo / "packages/core/pyproject.toml").read_text()
    assert git(remote_of(repo), "tag", "--list") == ""
    assert git(remote_of(repo), "log", "--format=%s", "master") == "start"


def reject_with_hook(hooks: Path, name: str) -> None:
    hook = hooks / name
    hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)


def assert_back_at_start(repo: Path) -> None:
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "log", "--format=%s") == "start"
    assert git(repo, "tag", "--list") == ""
    assert git(remote_of(repo), "tag", "--list") == ""
    assert 'version = "2.0.0"' in (repo / "packages/core/pyproject.toml").read_text()


def test_a_rejected_push_removes_the_local_commit_and_tag(repo):
    reject_with_hook(remote_of(repo) / "hooks", "pre-receive")

    with pytest.raises(release.ReleaseError, match="rejected"):
        release.release(repo, "2.1.0", lock=lock_to(repo, "2.1.0"), check=nothing)

    assert_back_at_start(repo)
    release.check_ready(repo, "2.1.0")


def test_a_failed_commit_restores_the_files(repo):
    reject_with_hook(repo / ".git/hooks", "pre-commit")

    with pytest.raises(release.ReleaseError, match="commit"):
        release.release(repo, "2.1.0", lock=lock_to(repo, "2.1.0"), check=nothing)

    assert_back_at_start(repo)


def test_a_lock_file_that_was_not_updated_stops_the_release(repo):
    with pytest.raises(
        release.ReleaseError, match=r"does not lock perexchange 2\.1\.0"
    ):
        release.release(repo, "2.1.0", lock=nothing, check=nothing)

    assert git(repo, "status", "--porcelain") == ""
    assert git(remote_of(repo), "tag", "--list") == ""
