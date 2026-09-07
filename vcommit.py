"""Commit the staged changes with automatic versioning.

Usage: uv run vcommit.py [--package <name>] <patch|minor|major> <message>.
"""

import subprocess
import sys
from pathlib import Path

PACKAGES_DIR = "packages"
ROOT_PACKAGE = "vocadb-tools"
IGNORED_PATHS = {"uv.lock"}


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()  # noqa: S603


def staged_packages(staged: list[str]) -> set[str]:
    names: set[str] = set()
    for path in staged:
        if path in IGNORED_PATHS:
            continue
        parts = Path(path).parts
        if len(parts) > 1 and parts[0] == PACKAGES_DIR:
            names.add(parts[1])
        else:
            names.add(ROOT_PACKAGE)
    return names


def pyproject_path(package: str) -> str:
    if package == ROOT_PACKAGE:
        return "pyproject.toml"
    return f"{PACKAGES_DIR}/{package}/pyproject.toml"


def bump_package(package: str, bump: str) -> str:
    run(["uv", "version", "--package", package, "--bump", bump])
    version = run(["uv", "version", "--package", package])
    run(["git", "add", pyproject_path(package)])
    return version


def main() -> None:
    argv = sys.argv[1:]

    package = None
    if argv and argv[0] == "--package":
        if len(argv) < 2:
            print(__doc__)  # noqa: T201
            sys.exit(1)
        package, argv = argv[1], argv[2:]

    if len(argv) < 2 or argv[0] not in {"patch", "minor", "major"}:
        print(__doc__)  # noqa: T201
        sys.exit(1)

    bump, message = argv[0], " ".join(argv[1:])

    staged = run(["git", "diff", "--cached", "--name-only"]).splitlines()
    if not staged:
        print("No staged files. Stage changes before committing.")  # noqa: T201
        sys.exit(1)

    packages = {package} if package else staged_packages(staged)
    ordered = [*sorted(packages - {ROOT_PACKAGE}), ROOT_PACKAGE]
    versions = " + ".join(bump_package(name, bump) for name in ordered)

    run(["git", "add", "uv.lock"])
    run(["git", "commit", "-m", f"{versions}, {message}"])
    print(f"Committed: {versions}, {message}")  # noqa: T201


if __name__ == "__main__":
    main()
