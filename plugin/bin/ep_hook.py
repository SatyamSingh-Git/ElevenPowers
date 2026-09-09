"""Launcher so hooks can run from any working directory.

Claude Code runs hooks with the cwd set to the user's project, so the package
has to be located explicitly rather than found on sys.path.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.hook import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv))
