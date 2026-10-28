"""End-of-term archives: the gradebook, its scores and its grades in one zip file.

Entries carry a fixed timestamp so that archiving the same gradebook twice
gives byte-identical files, which is what the school's records system checks.
"""
import io
import zipfile
from pathlib import Path

from .gradebook_file import save_gradebook
from .grades_csv import export_grades
from .scores_export import export_scores

ENTRY_TIME = (2000, 1, 1, 0, 0, 0)


def archive_term(book, path, scratch):
    """Write the archive to `path`, using the folder `scratch` for the files it bundles."""
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    code = book.course.code
    parts = {
        f"{code}/gradebook.json": scratch / "gradebook.json",
        f"{code}/scores.csv": scratch / "scores.csv",
        f"{code}/grades.csv": scratch / "grades.csv",
    }
    save_gradebook(book, parts[f"{code}/gradebook.json"])
    export_scores(book, parts[f"{code}/scores.csv"])
    export_grades(book, parts[f"{code}/grades.csv"])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, source in parts.items():
            entry = zipfile.ZipInfo(name, date_time=ENTRY_TIME)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, source.read_bytes())
    Path(path).write_bytes(buffer.getvalue())
    return list(parts)
