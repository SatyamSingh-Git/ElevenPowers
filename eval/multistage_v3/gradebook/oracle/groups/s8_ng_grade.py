"""Stage 8: a student with no graded work gets the letter NG."""
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "BIO1",
    "title": "Biology",
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
    return book


def test_nothing_due_yet(tmp_path):
    grade = make_book(tmp_path).grade("s1", as_of=3)
    assert grade.percent is None
    assert grade.letter == "NG"


def test_everything_excused(tmp_path):
    book = make_book(tmp_path)
    book.excuse("s2", "lab1")
    book.excuse("s2", "test1")
    grade = book.grade("s2")
    assert grade.percent is None
    assert grade.letter == "NG"
    assert book.grade("s1").letter == "F"
