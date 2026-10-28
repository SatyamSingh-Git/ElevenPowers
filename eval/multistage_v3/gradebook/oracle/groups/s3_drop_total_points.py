"""Stage 3: drop-lowest ranks by percent under the total points policy too."""
import json

from gradebook.cli.main import main
from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course
from gradebook.storage.gradebook_file import save_gradebook

COURSE = {
    "code": "GEO",
    "title": "Geography",
    "policy": "total_points",
    "categories": [{"name": "quizzes", "drop_lowest": 1}, {"name": "exams"}],
    "assignments": [
        {"id": "q1", "category": "quizzes", "max_points": 5, "due_day": 3},
        {"id": "q2", "category": "quizzes", "max_points": 10, "due_day": 6},
        {"id": "ex1", "category": "exams", "max_points": 100, "due_day": 9},
    ],
}


def make_book(tmp_path):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(COURSE), encoding="utf-8")
    book = Gradebook(load_course(path))
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "q1", 4)
    book.record_score("s1", "q2", 6)
    book.record_score("s1", "ex1", 80)
    return book


def test_total_points_keeps_the_better_percent(tmp_path):
    grade = make_book(tmp_path).grade("s1")
    assert grade.percent == 80.0
    assert grade.letter == "B-"


def test_class_report_shows_it(tmp_path, capsys):
    path = tmp_path / "book.json"
    save_gradebook(make_book(tmp_path), path)
    assert main(["report", "--format", "csv", "--book", str(path)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "student_id,name,percent,letter"
    row = lines[1].split(",")
    assert row[0] == "s1"
    assert float(row[2]) == 80.0
    assert row[3] == "B-"
