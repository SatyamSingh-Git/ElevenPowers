"""Stage 4: courses that do not set grade_decimals round to two decimals."""
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "LIT",
    "title": "Literature",
    "categories": [{"name": "essays", "weight": 60}, {"name": "reading", "weight": 40}],
    "assignments": [
        {"id": "e1", "category": "essays", "max_points": 3, "due_day": 4},
        {"id": "r1", "category": "reading", "max_points": 9, "due_day": 6},
    ],
}


def make_book(tmp_path, course):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(course), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "e1", 2)
    book.record_score("s1", "r1", 7)
    return book


def test_default_is_two_decimals(tmp_path):
    grade = make_book(tmp_path, COURSE).grade("s1")
    assert grade.category("essays").percent == 66.67
    assert grade.category("reading").percent == 77.78
    # 0.6 x 66.666... + 0.4 x 77.777... = 71.111...
    assert grade.percent == 71.11


def test_a_course_can_still_choose_one_decimal(tmp_path):
    assert make_book(tmp_path, dict(COURSE, grade_decimals=1)).grade("s1").percent == 71.1
    assert make_book(tmp_path, COURSE).grade("s1").percent == 71.11
