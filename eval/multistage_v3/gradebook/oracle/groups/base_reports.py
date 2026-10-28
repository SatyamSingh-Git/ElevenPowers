"""Reports that restate course grades: the term grades file, transcripts and progress reports."""
import json

from gradebook.model.student import Student
from gradebook.reports.progress import progress_report
from gradebook.services.gradebook import Gradebook
from gradebook.services.transcript import build_transcript
from gradebook.storage.course_config import load_course
from gradebook.storage.grades_csv import export_grades

STUDENTS = [Student("s1", "Lovelace", "Ada"), Student("s2", "Turing", "Alan"), Student("s3", "Hopper", "Grace")]

ALGEBRA = {
    "code": "ALG1",
    "title": "Algebra I",
    "credits": 1,
    "categories": [
        {"name": "homework", "weight": 40, "drop_lowest": 1},
        {"name": "quizzes", "weight": 30},
        {"name": "exams", "weight": 30},
    ],
    "assignments": [
        {"id": "hw1", "category": "homework", "max_points": 10, "due_day": 3},
        {"id": "q1", "category": "quizzes", "max_points": 5, "due_day": 5},
        {"id": "hw2", "category": "homework", "max_points": 10, "due_day": 7},
        {"id": "hw3", "category": "homework", "max_points": 20, "due_day": 10},
        {"id": "q2", "category": "quizzes", "max_points": 10, "due_day": 12},
        {"id": "ex1", "category": "exams", "max_points": 100, "due_day": 15},
    ],
}
ALGEBRA_SCORES = {
    "s1": {"hw1": 10, "hw2": 9, "hw3": 19, "q1": 5, "q2": 9, "ex1": 92},
    "s2": {"hw1": 7, "hw2": 8, "hw3": 16, "q1": 4, "q2": 7, "ex1": 75},
    "s3": {"hw1": 5, "hw2": 9, "hw3": 8, "q1": 3, "q2": 6, "ex1": 70},
}

HISTORY = {
    "code": "HIST",
    "title": "World History",
    "credits": 0.5,
    "policy": "points",
    "categories": [{"name": "papers"}, {"name": "tests"}],
    "assignments": [
        {"id": "p1", "category": "papers", "max_points": 50, "due_day": 4},
        {"id": "p2", "category": "papers", "max_points": 50, "due_day": 9},
        {"id": "t1", "category": "tests", "max_points": 100, "due_day": 14},
    ],
}
HISTORY_SCORES = {
    "s1": {"p1": 44, "p2": 46, "t1": 85},
    "s2": {"p1": 30, "p2": 41, "t1": 77},
    "s3": {"p1": 25, "t1": 64},
}

BIOLOGY = {
    "code": "BIO1",
    "title": "Biology",
    "credits": 1,
    "categories": [{"name": "labs", "weight": 50}, {"name": "tests", "weight": 50}],
    "assignments": [
        {"id": "lab1", "category": "labs", "max_points": 20, "due_day": 5},
        {"id": "test1", "category": "tests", "max_points": 100, "due_day": 10},
    ],
}


def make_book(tmp_path, data, scores):
    path = tmp_path / f"{data['code']}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    book = Gradebook(load_course(path))
    for student in STUDENTS:
        book.add_student(student)
    for student_id, entries in scores.items():
        for assignment_id, points in entries.items():
            book.record_score(student_id, assignment_id, points)
    return book


def test_transcript_from_posted_grades_files(tmp_path):
    algebra = make_book(tmp_path, ALGEBRA, ALGEBRA_SCORES)
    history = make_book(tmp_path, HISTORY, HISTORY_SCORES)
    biology = make_book(tmp_path, BIOLOGY, {})
    files = [tmp_path / "alg1-grades.csv", tmp_path / "hist-grades.csv", tmp_path / "bio1-grades.csv"]
    export_grades(algebra, files[0])
    export_grades(history, files[1])
    # Posted at mid-term, before any biology work was due.
    export_grades(biology, files[2], as_of=2)

    transcript = build_transcript("s1", files)
    assert transcript.name == "Ada Lovelace"
    assert [line.course for line in transcript.lines] == ["ALG1", "BIO1", "HIST"]
    for book, code in ((algebra, "ALG1"), (history, "HIST")):
        grade = book.grade("s1")
        line = transcript.line(code)
        assert line.percent == grade.percent
        assert line.letter == grade.letter
        assert line.credits == book.course.credits
    assert transcript.line("ALG1").letter == "A"
    assert transcript.line("HIST").letter == "B+"
    assert transcript.line("BIO1").percent is None
    assert transcript.credits_attempted == 1.5
    assert transcript.credits_earned == 1.5
    assert transcript.gpa == 3.77


def test_transcript_for_every_student_matches_their_grades(tmp_path):
    algebra = make_book(tmp_path, ALGEBRA, ALGEBRA_SCORES)
    history = make_book(tmp_path, HISTORY, HISTORY_SCORES)
    files = [tmp_path / "alg1.csv", tmp_path / "hist.csv"]
    export_grades(algebra, files[0])
    export_grades(history, files[1])
    for student in STUDENTS:
        transcript = build_transcript(student.student_id, files)
        assert transcript.line("ALG1").percent == algebra.grade(student.student_id).percent
        assert transcript.line("HIST").percent == history.grade(student.student_id).percent


def assert_matches_grade(report, grade):
    assert report.percent == grade.percent
    assert report.letter == grade.letter
    for result in grade.categories:
        assert report.category(result.name).percent == result.percent


def test_progress_report_matches_the_course_grade(tmp_path):
    algebra = make_book(tmp_path, ALGEBRA, ALGEBRA_SCORES)
    for student in STUDENTS:
        report = progress_report(algebra, student.student_id)
        assert_matches_grade(report, algebra.grade(student.student_id))
        assert sum(item.status == "dropped" for item in report.category("homework").items) == 1


def test_progress_report_for_a_points_course(tmp_path):
    history = make_book(tmp_path, HISTORY, HISTORY_SCORES)
    for student in STUDENTS:
        report = progress_report(history, student.student_id)
        assert_matches_grade(report, history.grade(student.student_id))
    report = progress_report(history, "s3")
    assert report.item("p2").status == "missing"


def test_progress_report_part_way_through(tmp_path):
    algebra = make_book(tmp_path, ALGEBRA, ALGEBRA_SCORES)
    report = progress_report(algebra, "s3", as_of=10)
    assert_matches_grade(report, algebra.grade("s3", as_of=10))
    assert report.item("ex1").status == "upcoming"
