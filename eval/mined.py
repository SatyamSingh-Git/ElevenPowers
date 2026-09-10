"""Load mined instances as tasks.

    python -m eval.live --suite mined --arm vanilla --runs 1

The file is whatever `python -m eval.mine` last validated, named by EP_MINED or
found beside the repository. Nothing here is written by this project: the code,
the bug, the tests and the wording of the report all come from the upstream
history.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .task import Task


def path() -> Path:
    return Path(os.environ.get("EP_MINED", "mined.json"))


def load() -> list[Task]:
    where = path()
    if not where.exists():
        return []
    out = []
    for row in json.loads(where.read_text(encoding="utf-8")):
        out.append(Task(
            name=row["name"],
            prompt=row["prompt"],
            files={},
            hidden="",
            why=f"{len(row['f2p'])} test(s) from {row['fix'][:8]} must go green",
            source={k: row[k] for k in ("repo", "base", "env", "hidden_files", "f2p")},
        ))
    return out
