"""Commit the staged changes with automatic versioning.

Usage: uv run vcommit.py <patch|minor|major> <message>.
"""

import subprocess
import sys


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()  # noqa: S603


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in {"patch", "minor", "major"}:
        print(__doc__)  # noqa: T201
        sys.exit(1)

    bump, message = sys.argv[1], " ".join(sys.argv[2:])

    run(["uv", "version", "--bump", bump])
    version = run(["uv", "version"])
    run(["git", "add", "pyproject.toml"])
    run(["git", "commit", "-m", f"{version}, {message}"])
    print(f"Committed: {version}, {message}")  # noqa: T201


if __name__ == "__main__":
    main()
