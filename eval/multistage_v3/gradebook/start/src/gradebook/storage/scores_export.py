"""Writing every recorded score as a score file, the format `import scores` reads."""
import csv
from pathlib import Path

from .csv_util import EXCUSED

SCORE_FILE_COLUMNS = ("student_id", "assignment_id", "points", "submitted_day")


def export_scores(book, path):
    """Write the book's scores to `path` and return how many were written."""
    entries = book.sheet.items()
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCORE_FILE_COLUMNS)
        for student_id, assignment_id, score in entries:
            if score.excused:
                points = EXCUSED
            elif score.points is None:
                points = ""
            else:
                points = f"{score.points:g}"
            day = "" if score.submitted_day is None else str(score.submitted_day)
            writer.writerow([student_id, assignment_id, points, day])
    return len(entries)
