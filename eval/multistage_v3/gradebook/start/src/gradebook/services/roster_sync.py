"""Bringing a course roster in line with the office's current roster file.

New students are added. Students missing from the office's file are reported,
not removed, because their scores would go with them; a teacher drops them
with `gradebook drop-student` once they have checked.
"""
from dataclasses import dataclass

from ..model.student import student_from_row
from ..storage.csv_util import read_table
from ..storage.roster_csv import ROSTER_COLUMNS


@dataclass(frozen=True)
class RosterChanges:
    added: tuple  # student ids
    renamed: tuple  # (student id, old name, new name)
    absent: tuple  # student ids on the course but not in the file


def sync_roster(book, path):
    _, rows = read_table(path, ROSTER_COLUMNS)
    listed = {}
    for _, row in rows:
        if row["student_id"]:
            student = student_from_row(row)
            listed[student.student_id] = student
    current = {student.student_id: student for student in book.students}
    added, renamed = [], []
    for student_id, student in sorted(listed.items()):
        if student_id not in current:
            book.add_student(student)
            added.append(student_id)
        elif current[student_id] != student:
            renamed.append((student_id, current[student_id].display_name, student.display_name))
            book.replace_student(student)
    absent = tuple(sorted(set(current) - set(listed)))
    return RosterChanges(tuple(added), tuple(renamed), absent)


def describe_changes(changes):
    lines = [f"Added {student_id}" for student_id in changes.added]
    lines += [f"Renamed {student_id}: {old} -> {new}" for student_id, old, new in changes.renamed]
    lines += [f"Not in the office roster: {student_id}" for student_id in changes.absent]
    return lines or ["Roster already up to date"]
