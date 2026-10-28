"""Score files: one score per row, as an LMS or a spreadsheet exports them.

`submitted_day` is optional; without it, work counts as on time. A blank
points cell is skipped, so a partly filled file can be imported again later.
"""
from .csv_util import parse_cell, parse_day, read_table
from .importers import ImportSummary, at_line, importer

SCORE_COLUMNS = ("student_id", "assignment_id", "points")


@importer("scores")
def import_scores(book, path):
    header, rows = read_table(path, SCORE_COLUMNS)
    has_days = "submitted_day" in header
    recorded = 0
    for line, row in rows:
        kind, points = parse_cell(row["points"], line)
        if kind == "blank":
            continue
        student_id, assignment_id = row["student_id"], row["assignment_id"]
        if kind == "excused":
            at_line(line, lambda: book.excuse(student_id, assignment_id))
        else:
            day = parse_day(row["submitted_day"], line) if has_days else None
            at_line(line, lambda: book.record_score(student_id, assignment_id, points, day))
        recorded += 1
    return ImportSummary("scores", len(rows), recorded, len(rows) - recorded)
