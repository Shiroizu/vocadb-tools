"""Run ruff, ty and pytest in sequence."""

import subprocess
import sys

COMMANDS = (
    ["ruff", "check"],
    ["ty", "check"],
    ["pytest"],
)


def main() -> None:
    extra = sys.argv[1:]
    for command in COMMANDS:
        args = command + extra if command[0] == "pytest" else command
        print(f"\n$ {' '.join(args)}", flush=True)  # noqa: T201
        result = subprocess.run(args, check=False)  # noqa: S603
        if result.returncode:
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
