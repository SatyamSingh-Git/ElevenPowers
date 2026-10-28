"""Course grades end to end: course files, imports, save and load, and score sheets."""
import csv
import json

from gradebook.reports.score_sheet import write_score_sheet
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import load_course
from gradebook.storage.gradebook_file import load_gradebook, save_gradebook

ALGEBRA = {
    "code": "ALG1",
    "title": "Algebra I",
    "late_rule": "per_day",
    "late": {"per_day": 10, "cap": 50},
    "categories": [
        {"name": "homework", "weight": 40, "drop_lowest": 1},
        {"name": "quizzes", "weight": 30},
        {"name": "exams", "weight": 30},
    ],
    "assignments": [
        {"id": "hw1", "category": "homework", "max_points": 10, "due_day": 3},
        {"id": "q1", "category": "quizzes", "max_points": 5, "due_day": 5},
        {"id": "hw2", "category": "homework", "max_points": 10, "due_day": 7},
        {"id": "hw3", "category": "homework", "max_points": 10, "due_day": 10},
        {"id": "q2", "category": "quizzes", "max_points": 10, "due_day": 12},
        {"id": "ex1", "category": "exams", "max_points": 100, "due_day": 15},
    ],
}
ROSTER = "student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan\ns3,Hopper,Grace\n"
SCORES = {
    "s1": {"hw1": 10, "hw2": 8, "hw3": 9, "q1": 5, "q2": 9, "ex1": 90},
    "s2": {"hw1": 6, "hw2": 7, "hw3": 8, "q1": 4, "q2": 6, "ex1": 70},
    "s3": {"hw1": 9, "hw2": 9, "q1": 3, "ex1": 85},
}


def course_at(tmp_path, data, name="course.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return load_course(path)


def algebra_book(tmp_path):
    book = Gradebook(course_at(tmp_path, ALGEBRA))
    roster = tmp_path / "roster.csv"
    roster.write_text(ROSTER, encoding="utf-8")
    book.import_file("roster", roster)
    lines = ["student_id,assignment_id,points,submitted_day"]
    for student_id, entries in SCORES.items():
        for assignment_id, points in entries.items():
            day = "12" if (student_id, assignment_id) == ("s2", "hw3") else ""
            lines.append(f"{student_id},{assignment_id},{points},{day}")
    scores = tmp_path / "scores.csv"
    scores.write_text("\n".join(lines) + "\n", encoding="utf-8")
    book.import_file("scores", scores)
    return book


def test_weighted_grades_from_imported_files(tmp_path):
    book = algebra_book(tmp_path)
    assert (book.grade("s1").percent, book.grade("s1").letter) == (93.0, "A")
    # hw3 is two days late: 8 points less 20% of 10.
    assert (book.grade("s2").percent, book.grade("s2").letter) == (67.0, "D+")
    assert (book.grade("s3").percent, book.grade("s3").letter) == (67.5, "D+")
    assert book.grade("s3").category("quizzes").percent == 20.0


def test_grades_as_of_a_day(tmp_path):
    book = algebra_book(tmp_path)
    grade = book.grade("s1", as_of=7)
    assert grade.category("exams").percent is None
    assert grade.percent == 100.0


def test_points_policy_course(tmp_path):
    data = {
        "code": "HIST",
        "title": "World History",
        "policy": "points",
        "categories": [{"name": "papers"}, {"name": "tests"}],
        "assignments": [
            {"id": "p1", "category": "papers", "max_points": 20, "due_day": 4},
            {"id": "p2", "category": "papers", "max_points": 20, "due_day": 9},
            {"id": "t1", "category": "tests", "max_points": 60, "due_day": 14},
        ],
    }
    book = Gradebook(course_at(tmp_path, data))
    roster = tmp_path / "roster.csv"
    roster.write_text(ROSTER, encoding="utf-8")
    book.import_file("roster", roster)
    for assignment_id, points in {"p1": 18, "p2": 14, "t1": 48}.items():
        book.record_score("s1", assignment_id, points)
    assert (book.grade("s1").percent, book.grade("s1").letter) == (80.0, "B-")


def test_save_and_load_keep_every_grade(tmp_path):
    book = algebra_book(tmp_path)
    book.excuse("s3", "q2")
    path = tmp_path / "book.json"
    save_gradebook(book, path)
    loaded = load_gradebook(path)
    for student in book.students:
        assert loaded.grade(student.student_id) == book.grade(student.student_id)
    assert loaded.grade("s3").category("quizzes").percent == 60.0


def test_pass_fail_course(tmp_path):
    data = dict(ALGEBRA, code="PE", scale="pass_fail")
    book = Gradebook(course_at(tmp_path, data))
    roster = tmp_path / "roster.csv"
    roster.write_text(ROSTER, encoding="utf-8")
    book.import_file("roster", roster)
    for assignment_id, points in SCORES["s1"].items():
        book.record_score("s1", assignment_id, points)
    assert book.grade("s1").letter == "P"


def fill_sheet(path, entries):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    header = rows[0]
    id_column = header.index("student_id")
    for row in rows[1:]:
        for assignment_id, points in entries.get(row[id_column], {}).items():
            row[header.index(assignment_id)] = str(points)
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def test_filled_in_score_sheet_imports(tmp_path):
    book = Gradebook(course_at(tmp_path, ALGEBRA))
    roster = tmp_path / "roster.csv"
    roster.write_text(ROSTER, encoding="utf-8")
    book.import_file("roster", roster)
    book.record_score("s3", "hw1", 9)
    sheet = tmp_path / "sheet.csv"
    write_score_sheet(book, sheet)
    fill_sheet(sheet, {
        "s1": SCORES["s1"],
        "s2": SCORES["s2"],
        "s3": {"hw2": 9, "q1": 3, "ex1": 85, "q2": "EX"},
    })
    book.import_file("sheet", sheet)
    assert book.grade("s1").percent == 93.0
    assert book.grade("s2").percent == 71.0
    assert book.sheet.get("s3", "hw1").points == 9
    assert book.grade("s3").category("quizzes").percent == 60.0
    assert book.grade("s3").percent == 79.5
