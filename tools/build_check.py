# ruff: file-ignore[implicit-namespace-package]

import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from pathlib import Path

from tomli import load


ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "packages" / "core"
PYPROJECT = PKG_DIR / "pyproject.toml"


def package_version() -> str:
    with PYPROJECT.open("rb") as file:
        return load(file)["project"]["version"]


def assert_package(*, condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_wheel(path: Path, version: str) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name).decode("utf-8")

    assert_package(
        condition="perexchange/__init__.py" in names,
        message="wheel has no package code",
    )
    assert_package(
        condition="Name: perexchange\n" in metadata,
        message="wheel has the wrong project name",
    )
    assert_package(
        condition=f"Version: {version}\n" in metadata,
        message="wheel has the wrong version",
    )
    assert_package(
        condition=any(name.endswith("/LICENSE") for name in names),
        message="wheel does not contain the project license",
    )
    assert_package(
        condition=not any("tests/" in name for name in names),
        message="wheel contains test files",
    )
    assert_package(
        condition=not any(name.startswith("build/") for name in names),
        message="wheel contains stale build output",
    )


def verify_sdist(path: Path, version: str) -> None:
    with tarfile.open(path) as archive:
        names = archive.getnames()

    prefix = f"perexchange-{version}/"
    assert_package(
        condition=f"{prefix}README.md" in names,
        message="sdist has no README",
    )
    assert_package(
        condition=f"{prefix}LICENSE" in names,
        message="sdist has no license",
    )
    assert_package(
        condition=not any(
            "/tests/" in name or name.endswith("/tests") for name in names
        ),
        message="sdist contains test files",
    )


def clean_generated_files() -> None:
    shutil.rmtree(PKG_DIR / "build", ignore_errors=True)
    for path in PKG_DIR.glob("*.egg-info"):
        shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    version = package_version()
    print(f"Building perexchange {version}")

    try:
        clean_generated_files()
        with tempfile.TemporaryDirectory(prefix="perexchange-build-") as directory:
            output = Path(directory)
            subprocess.run(
                [
                    "uv",
                    "build",
                    "--sdist",
                    "--wheel",
                    "--out-dir",
                    str(output),
                ],
                cwd=PKG_DIR,
                check=True,
            )

            artifacts = sorted(
                path
                for path in output.iterdir()
                if path.suffix == ".whl" or path.name.endswith(".tar.gz")
            )
            wheels = [path for path in artifacts if path.suffix == ".whl"]
            sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
            assert_package(condition=len(wheels) == 1, message="expected one wheel")
            assert_package(
                condition=len(sdists) == 1,
                message="expected one source distribution",
            )

            verify_wheel(wheels[0], version)
            verify_sdist(sdists[0], version)
            subprocess.run(
                [sys.executable, "-m", "twine", "check", *map(str, artifacts)],
                check=True,
            )
    except (
        OSError,
        RuntimeError,
        StopIteration,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Package verification failed: {error}", file=sys.stderr)
        return 1
    finally:
        clean_generated_files()

    print("Package verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
