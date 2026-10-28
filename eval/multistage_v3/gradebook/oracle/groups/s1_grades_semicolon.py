"""Stage 1: the term grades file separates its fields with semicolons."""
import csv
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course
from gradebook.storage.grades_csv import export_grades

COURSE = {
    "code": "CHEM",
    "title": "Chemistry, Honors",
    "credits": 1,
    "categories": [{"name": "labs", "weight": 50}, {"name": "tests", "weight": 50}],
    "assignments": [
        {"id": "lab1", "category": "labs", "max_points": 20, "due_day": 5},
        {"id": "test1", "category": "tests", "max_points": 100, "due_day": 10},
    ],
}


def make_book(tmp_path):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(COURSE), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.add_student(Student("s2", "Turing", "Alan"))
    book.record_score("s1", "lab1", 18)
    book.record_score("s1", "test1", 90)
    book.record_score("s2", "lab1", 15)
    book.record_score("s2", "test1", 75)
    return book


def test_header_uses_semicolons(tmp_path):
    out = tmp_path / "grades.csv"
    export_grades(make_book(tmp_path), out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "student_id;name;course;credits;percent;letter"
    assert all("," not in line for line in lines)


def test_rows_split_on_semicolons(tmp_path):
    out = tmp_path / "grades.csv"
    book = make_book(tmp_path)
    export_grades(book, out)
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    assert len(rows) == 3
    assert all(len(row) == 6 for row in rows)
    assert rows[1][:4] == ["s1", "Ada Lovelace", "CHEM", "1"]
    assert float(rows[1][4]) == book.grade("s1").percent
    assert rows[2][5] == book.grade("s2").letter
