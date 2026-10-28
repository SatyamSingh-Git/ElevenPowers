"""Stage 3: drop-lowest ranks scores by percent of possible points."""
import json

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course

COURSE = {
    "code": "PHYS",
    "title": "Physics",
    "categories": [
        {"name": "quizzes", "weight": 50, "drop_lowest": 1},
        {"name": "exams", "weight": 50},
    ],
    "assignments": [
        {"id": "q1", "category": "quizzes", "max_points": 5, "due_day": 3},
        {"id": "q2", "category": "quizzes", "max_points": 10, "due_day": 6},
        {"id": "ex1", "category": "exams", "max_points": 100, "due_day": 9},
    ],
}


def make_book(tmp_path, course):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(course), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "q1", 4)
    book.record_score("s1", "q2", 6)
    book.record_score("s1", "ex1", 80)
    return book


def test_the_worse_percent_is_dropped(tmp_path):
    grade = make_book(tmp_path, COURSE).grade("s1")
    assert grade.category("quizzes").percent == 80.0
    assert grade.percent == 80.0
    assert grade.letter == "B-"


def test_drops_by_percent_with_two_dropped(tmp_path):
    course = json.loads(json.dumps(COURSE))
    course["categories"][0]["drop_lowest"] = 2
    course["assignments"].insert(2, {"id": "q3", "category": "quizzes", "max_points": 20, "due_day": 8})
    book = make_book(tmp_path, course)
    book.record_score("s1", "q3", 13)
    # 4/5 is 80%, 6/10 is 60% and 13/20 is 65%: the 4/5 is the one kept.
    assert book.grade("s1").category("quizzes").percent == 80.0
