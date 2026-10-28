"""Stage 2: the `points` scoring policy is called `total_points`."""
import json

from gradebook.model.student import Student
from gradebook.reports.progress import progress_report
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "HIST",
    "title": "World History",
    "categories": [{"name": "papers", "weight": 40}, {"name": "tests", "weight": 60}],
    "assignments": [
        {"id": "p1", "category": "papers", "max_points": 50, "due_day": 4},
        {"id": "p2", "category": "papers", "max_points": 50, "due_day": 9},
        {"id": "t1", "category": "tests", "max_points": 100, "due_day": 14},
    ],
}
SCORES = {"p1": 44, "p2": 46, "t1": 85}


def book_for(tmp_path, policy):
    path = tmp_path / f"{policy}.json"
    path.write_text(json.dumps(dict(COURSE, policy=policy)), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    for assignment_id, points in SCORES.items():
        book.record_score("s1", assignment_id, points)
    return book


def test_total_points_policy_adds_up_every_point(tmp_path):
    grade = book_for(tmp_path, "total_points").grade("s1")
    assert grade.percent == 87.5
    assert grade.letter == "B+"


def test_old_name_grades_the_same(tmp_path):
    assert book_for(tmp_path, "points").grade("s1") == book_for(tmp_path, "total_points").grade("s1")


def test_progress_report_for_a_total_points_course(tmp_path):
    book = book_for(tmp_path, "total_points")
    report = progress_report(book, "s1")
    assert report.percent == 87.5
    assert report.category("papers").percent == 90.0
