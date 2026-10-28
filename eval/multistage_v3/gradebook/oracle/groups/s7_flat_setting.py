"""Stage 7: `late.flat` sets the flat rule's percent."""
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "CS2",
    "title": "Data Structures",
    "late_rule": "flat",
    "late": {"flat": 35},
    "categories": [{"name": "labs", "weight": 100}],
    "assignments": [{"id": "l1", "category": "labs", "max_points": 20, "due_day": 5}],
}


def grade_for(tmp_path, points, day):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(COURSE), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "l1", points, submitted_day=day)
    return book.grade("s1")


def test_late_flat_percent(tmp_path):
    assert grade_for(tmp_path, 18, 9).percent == 55.0


def test_late_flat_never_goes_below_zero(tmp_path):
    assert grade_for(tmp_path, 5, 6).percent == 0.0
