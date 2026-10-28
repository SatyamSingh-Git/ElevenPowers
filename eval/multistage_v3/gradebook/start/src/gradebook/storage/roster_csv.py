"""Roster files: one student per row."""
from ..model.student import student_from_row
from .csv_util import read_table
from .importers import ImportSummary, at_line, importer

ROSTER_COLUMNS = ("student_id", "last_name", "first_name")


@importer("roster")
def import_roster(book, path):
    _, rows = read_table(path, ROSTER_COLUMNS)
    added = 0
    for line, row in rows:
        if not row["student_id"]:
            continue
        at_line(line, lambda row=row: book.add_student(student_from_row(row)))
        added += 1
    return ImportSummary("roster", len(rows), added, len(rows) - added)
