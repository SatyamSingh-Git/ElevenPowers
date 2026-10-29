"""Guest profiles brought over from the old system's CSV export."""
import csv
from pathlib import Path

from ..errors import ValidationError
from ..services import guests

COLUMNS = ("name", "email", "phone", "vip", "notes")
YES = ("y", "yes", "true", "1")


def import_guests(hotel, path):
    """Save a profile for each line; returns (saved names, [(line, message)] for lines skipped)."""
    saved, skipped = [], []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "name" not in (reader.fieldnames or ()):
            raise ValidationError("Guest file has no name column")
        for line, row in enumerate(reader, start=2):
            try:
                guest = guests.save_profile(
                    hotel,
                    row["name"] or "",
                    email=row.get("email") or None,
                    phone=row.get("phone") or None,
                    vip=(row.get("vip") or "").strip().lower() in YES,
                    notes=row.get("notes") or None,
                )
            except ValidationError as error:
                skipped.append((line, str(error)))
                continue
            saved.append(guest.name)
    return saved, skipped
