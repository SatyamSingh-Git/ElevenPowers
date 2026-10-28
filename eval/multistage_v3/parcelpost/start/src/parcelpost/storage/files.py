"""File writing shared by the store and the formats."""
import os
from pathlib import Path


def write_atomic(path, text):
    """Replace `path` with `text` so a reader never sees half a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def append_lines(path, lines):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")
