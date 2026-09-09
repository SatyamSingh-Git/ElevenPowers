"""Show what the runtime currently believes about this task.

    ep-status [--cwd DIR]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.status import render  # noqa: E402


def main(argv: list[str]) -> int:
    where = Path(argv[argv.index("--cwd") + 1] if "--cwd" in argv else ".").resolve()
    print(render(where))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
