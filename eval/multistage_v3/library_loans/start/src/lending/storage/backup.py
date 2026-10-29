"""Zip backups of a library directory, named by the desk date.

Only the files this tool owns go into the archive; scan files and exports
lying around in the directory are left out.
"""
import zipfile

from ..config import FILE as SETTINGS
from .catalogue_store import FILE as CATALOGUE
from .holds_store import FILE as HOLDS
from .holidays_store import FILE as HOLIDAYS
from .ledger import FILE as LEDGER
from .members_store import FILE as MEMBERS
from .notes_store import FILE as NOTES
from .outbox import FILE as OUTBOX
from .transit_store import FILE as TRANSIT

OWNED = (CATALOGUE, MEMBERS, NOTES, HOLDS, LEDGER, TRANSIT, HOLIDAYS, OUTBOX, SETTINGS)


def write_backup(directory, target, day):
    """Write `lending-<day>.zip` into `target`; returns its path and the files it holds."""
    target.mkdir(parents=True, exist_ok=True)
    archive = target / f'lending-{day.isoformat()}.zip'
    present = [name for name in OWNED if (directory / name).exists()]
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name in present:
            out.write(directory / name, arcname=name)
    return archive, present


def restore_backup(archive, directory):
    """Unpack a backup over `directory`; files the backup does not hold are left alone."""
    with zipfile.ZipFile(archive) as source:
        names = [name for name in source.namelist() if name in OWNED]
        for name in names:
            (directory / name).write_bytes(source.read(name))
    return names
