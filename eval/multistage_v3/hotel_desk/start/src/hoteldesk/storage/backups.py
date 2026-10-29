"""Copies of the state file taken before each night audit.

They sit in a `backups` folder beside the state file, one per business date,
and only the most recent ones are kept.
"""
from pathlib import Path
import shutil

KEEP = 14


def backup_folder(state_path):
    return Path(state_path).parent / "backups"


def take_backup(state_path, business_date):
    """Copy the state file aside under the business date it was taken on; returns the copy."""
    state_path = Path(state_path)
    folder = backup_folder(state_path)
    folder.mkdir(exist_ok=True)
    copy = folder / f"{state_path.stem}-{business_date.isoformat()}{state_path.suffix}"
    shutil.copyfile(state_path, copy)
    _prune(state_path)
    return copy


def _prune(state_path):
    # ISO dates in the names sort in date order, so the oldest come first.
    for old in list_backups(state_path)[:-KEEP]:
        old.unlink()


def list_backups(state_path):
    state_path = Path(state_path)
    return sorted(backup_folder(state_path).glob(f"{state_path.stem}-*{state_path.suffix}"))
