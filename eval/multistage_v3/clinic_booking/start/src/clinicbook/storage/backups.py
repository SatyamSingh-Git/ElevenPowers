"""Copies of the bookings file taken before each save, so a bad edit can be undone."""
from pathlib import Path
import shutil

KEEP = 20
FOLDER = ".backups"


def backup_folder(path):
    return Path(path).parent / FOLDER


def take_backup(path, moment):
    """Copy `path` aside, named after `moment`, and prune to the newest KEEP copies.

    Returns the copy, or None when there is nothing to copy yet.
    """
    path = Path(path)
    if not path.exists():
        return None
    folder = backup_folder(path)
    folder.mkdir(exist_ok=True)
    copy = folder / f"{path.stem}-{moment:%Y%m%dT%H%M}{path.suffix}"
    shutil.copy2(path, copy)
    for old in backups(path)[:-KEEP]:
        old.unlink()
    return copy


def backups(path):
    """Backups of `path`, oldest first. The timestamp in the name sorts as text."""
    path = Path(path)
    folder = backup_folder(path)
    if not folder.exists():
        return []
    return sorted(folder.glob(f"{path.stem}-*{path.suffix}"))


def restore(path, copy):
    shutil.copy2(copy, path)
