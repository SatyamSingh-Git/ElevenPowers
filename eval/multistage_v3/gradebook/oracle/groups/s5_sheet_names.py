"""Stage 5: score sheets carry each student's name after student_id."""
import csv
import json

from gradebook.model.student import Student
from gradebook.reports.score_sheet import write_score_sheet
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "MUS",
    "title": "Music",
    "categories": [{"name": "work", "weight": 100}],
    "assignments": [
        {"id": "m2", "category": "work", "max_points": 10, "due_day": 8},
        {"id": "m1", "category": "work", "max_points": 10, "due_day": 3},
    ],
}


def read_sheet(tmp_path):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(COURSE), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s2", "Turing", "Alan"))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "m1", 7)
    sheet = tmp_path / "sheet.csv"
    write_score_sheet(book, sheet)
    with sheet.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_header_has_name_after_student_id(tmp_path):
    rows = read_sheet(tmp_path)
    assert rows[0] == ["student_id", "name", "m1", "m2"]


def test_names_are_last_comma_first(tmp_path):
    rows = read_sheet(tmp_path)
    by_id = {row[0]: row for row in rows[1:]}
    assert by_id["s1"][1:] == ["Lovelace, Ada", "7", ""]
    assert by_id["s2"][1] == "Turing, Alan"
