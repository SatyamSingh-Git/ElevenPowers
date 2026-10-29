"""Copies of the data files, taken before anything risky such as a schedule import."""
from pathlib import Path
import shutil

from ..config import SETTINGS_FILE
from ..errors import BoxOfficeError
from .customers import CUSTOMERS_FILE
from .jsonstore import HOLDS_FILE, ORDERS_FILE, PERFORMANCES_FILE, VENUE_FILE, WAITLIST_FILE
from .ledger import LEDGER_FILE

BACKUP_DIR = "backups"
DATA_FILES = (SETTINGS_FILE, VENUE_FILE, PERFORMANCES_FILE, HOLDS_FILE, ORDERS_FILE,
              CUSTOMERS_FILE, WAITLIST_FILE, LEDGER_FILE)


def create_backup(root, name):
    """Copy every data file that exists into backups/`name`; returns the names copied."""
    root = Path(root)
    target = root / BACKUP_DIR / name
    if target.exists():
        raise BoxOfficeError("backup-exists", name=name)
    target.mkdir(parents=True)
    copied = []
    for file_name in DATA_FILES:
        if (root / file_name).is_file():
            shutil.copy2(root / file_name, target / file_name)
            copied.append(file_name)
    return copied


def list_backups(root):
    folder = Path(root) / BACKUP_DIR
    if not folder.is_dir():
        return []
    return sorted(path.name for path in folder.iterdir() if path.is_dir())


def restore_backup(root, name):
    """Put the data directory back as it was in backup `name`, removing files made since."""
    root = Path(root)
    source = root / BACKUP_DIR / name
    if not source.is_dir():
        raise BoxOfficeError("unknown-backup", name=name)
    for file_name in DATA_FILES:
        current = root / file_name
        if (source / file_name).is_file():
            shutil.copy2(source / file_name, current)
        elif current.is_file():
            current.unlink()
