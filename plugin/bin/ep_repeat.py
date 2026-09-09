"""Run a command many times and report whether it is stable.

    ep-repeat 50 -- pytest tests/test_race.py -q
    ep-repeat 50 --jobs 8 -- pytest tests/test_race.py -q

Prints a human summary and one machine-readable line the runtime turns into
stability evidence. Exits non-zero when the command failed at least once, so it
also works as a plain flakiness check in a shell or in continuous integration.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.repeat import run  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="ep-repeat", add_help=True,
        usage="ep-repeat <times> [--jobs N] [--timeout S] [--stop-on-fail] [--cwd DIR] -- <command>",
    )
    parser.add_argument("times", type=int, help="how many times to run it")
    parser.add_argument("--jobs", type=int, default=1, help="run this many at once")
    parser.add_argument("--timeout", type=int, default=300, help="seconds per run")
    parser.add_argument("--stop-on-fail", action="store_true",
                        help="stop at the first failure instead of measuring a rate")
    parser.add_argument("--cwd", default=".", help="directory to run in")

    # Split on the first bare `--` rather than using REMAINDER, which would
    # swallow this tool's own flags into the command being repeated.
    rest = argv[1:]
    if "--" not in rest:
        parser.error("no command given; put it after --")
    cut = rest.index("--")
    args = parser.parse_args(rest[:cut])
    command = rest[cut + 1:]
    if not command:
        parser.error("no command given; put it after --")

    outcome = run(" ".join(command), args.times, Path(args.cwd).resolve(),
                  jobs=args.jobs, timeout=args.timeout, stop_on_fail=args.stop_on_fail)
    print(outcome.summary())
    print(outcome.line())
    return 0 if outcome.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
