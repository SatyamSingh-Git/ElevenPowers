import pytest

from gradebook.grading.calculator import compute_grade
from gradebook.services.gradebook import Gradebook
from gradebook.model.student import Student
from gradebook.storage.course_config import course_from_dict


def test_weighted_grades(book):
    assert book.grade("s1").percent == 93.0
    assert book.grade("s1").letter == "A"
    assert book.grade("s2").percent == 71.0
    assert book.grade("s2").letter == "C-"


def test_missing_work_counts_as_zero(book):
    grade = book.grade("s3")
    assert grade.category("quizzes").percent == 20.0
    assert grade.percent == 67.5
    assert grade.letter == "D+"


def test_drop_lowest_keeps_best_scores(book):
    assert book.grade("s2").category("homework").percent == 75.0


def test_drop_lowest_never_drops_the_only_score(empty_book):
    empty_book.record_score("s1", "hw1", 4)
    grade = empty_book.grade("s1", as_of=3)
    assert grade.category("homework").percent == 40.0


def test_excused_work_is_left_out(book):
    book.excuse("s3", "q2")
    assert book.grade("s3").category("quizzes").percent == 60.0


def test_upcoming_work_does_not_count(book):
    grade = book.grade("s1", as_of=7)
    assert grade.category("exams").percent is None
    assert grade.category("homework").percent == 100.0


def test_no_graded_work_has_no_percent_or_letter(empty_book):
    grade = empty_book.grade("s1", as_of=2)
    assert grade.percent is None
    assert grade.letter is None


def test_late_work_loses_points_per_day(empty_book):
    empty_book.record_score("s1", "hw1", 10, submitted_day=5)
    assert empty_book.grade("s1", as_of=3).category("homework").percent == 80.0


def test_late_penalty_is_capped(empty_book):
    empty_book.record_score("s1", "hw1", 10, submitted_day=30)
    assert empty_book.grade("s1", as_of=3).category("homework").percent == 50.0


def test_points_policy_totals_every_category(course_data):
    course_data["policy"] = "points"
    course = course_from_dict(course_data)
    book = Gradebook(course)
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "q1", 5)
    book.record_score("s1", "hw1", 5)
    assert compute_grade(course, book.sheet, "s1", as_of=5).percent == pytest.approx(66.67, abs=0.05)


def test_rounds_half_up(course_data):
    course_data["grade_decimals"] = 1
    course_data["categories"] = [{"name": "work", "weight": 100}]
    course_data["assignments"] = [
        {"id": "a", "category": "work", "max_points": 200, "due_day": 1},
    ]
    course = course_from_dict(course_data)
    book = Gradebook(course)
    book.add_student(Student("s1", "Lovelace", "Ada"))
    book.record_score("s1", "a", 178.9)
    assert book.grade("s1").percent == 89.5
    assert book.grade("s1").letter == "B+"
