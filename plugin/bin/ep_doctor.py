"""Check that the runtime is actually seeing what its host sends.

    ep-doctor [--cwd DIR]

Exits non-zero when something is wrong, so it works in continuous integration
as well as by hand.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.doctor import report  # noqa: E402


def main(argv: list[str]) -> int:
    where = Path(argv[argv.index("--cwd") + 1] if "--cwd" in argv else ".").resolve()
    body, ok = report(where)
    print(body)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
