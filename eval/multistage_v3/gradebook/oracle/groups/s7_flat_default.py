"""Stage 7: the `flat` late rule with its default percent."""
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "CS1",
    "title": "Computing",
    "late_rule": "flat",
    "categories": [{"name": "labs", "weight": 100}],
    "assignments": [
        {"id": "l1", "category": "labs", "max_points": 10, "due_day": 5},
        {"id": "l2", "category": "labs", "max_points": 10, "due_day": 5},
        {"id": "l3", "category": "labs", "max_points": 10, "due_day": 5},
    ],
}


def make_book(tmp_path, course):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(course), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    return book


def lab(book, points, day):
    book.record_score("s1", "l1", points, submitted_day=day)
    return book.grade("s1", as_of=5).category("labs")


def test_late_work_loses_twenty_percent_however_late(tmp_path):
    book = make_book(tmp_path, dict(COURSE, assignments=COURSE["assignments"][:1]))
    assert lab(book, 9, 6).percent == 70.0
    assert lab(book, 9, 40).percent == 70.0


def test_on_time_work_keeps_every_point(tmp_path):
    book = make_book(tmp_path, dict(COURSE, assignments=COURSE["assignments"][:1]))
    assert lab(book, 9, 5).percent == 90.0
    assert lab(book, 9, None).percent == 90.0


def test_mixed_class(tmp_path):
    book = make_book(tmp_path, COURSE)
    book.record_score("s1", "l1", 10, submitted_day=7)
    book.record_score("s1", "l2", 10, submitted_day=5)
    book.record_score("s1", "l3", 5, submitted_day=6)
    # 8 + 10 + 3 of 30
    assert book.grade("s1").percent == 70.0
