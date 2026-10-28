import copy

import pytest

from gradebook.model.student import Student
from gradebook.services.gradebook import Gradebook
from gradebook.storage.course_config import course_from_dict

ALGEBRA = {
    "code": "ALG1",
    "title": "Algebra I",
    "term": "2026 fall",
    "credits": 1.0,
    "grade_decimals": 1,
    "late_rule": "per_day",
    "late": {"per_day": 10, "cap": 50},
    "categories": [
        {"name": "homework", "weight": 40, "drop_lowest": 1},
        {"name": "quizzes", "weight": 30},
        {"name": "exams", "weight": 30},
    ],
    "assignments": [
        {"id": "hw1", "title": "Homework 1", "category": "homework", "max_points": 10, "due_day": 3},
        {"id": "q1", "title": "Quiz 1", "category": "quizzes", "max_points": 5, "due_day": 5},
        {"id": "hw2", "title": "Homework 2", "category": "homework", "max_points": 10, "due_day": 7},
        {"id": "hw3", "title": "Homework 3", "category": "homework", "max_points": 10, "due_day": 10},
        {"id": "q2", "title": "Quiz 2", "category": "quizzes", "max_points": 10, "due_day": 12},
        {"id": "ex1", "title": "Midterm", "category": "exams", "max_points": 100, "due_day": 15},
    ],
}

STUDENTS = [
    Student("s1", "Lovelace", "Ada"),
    Student("s2", "Turing", "Alan"),
    Student("s3", "Hopper", "Grace"),
]


@pytest.fixture
def course_data():
    return copy.deepcopy(ALGEBRA)


@pytest.fixture
def course(course_data):
    return course_from_dict(course_data)


@pytest.fixture
def empty_book(course):
    book = Gradebook(course)
    for student in STUDENTS:
        book.add_student(student)
    return book


@pytest.fixture
def book(empty_book):
    scores = {
        "s1": {"hw1": 10, "hw2": 8, "hw3": 9, "q1": 5, "q2": 9, "ex1": 90},
        "s2": {"hw1": 6, "hw2": 7, "hw3": 8, "q1": 4, "q2": 6, "ex1": 70},
        "s3": {"hw1": 9, "hw2": 9, "q1": 3, "ex1": 85},
    }
    for student_id, entries in scores.items():
        for assignment_id, points in entries.items():
            empty_book.record_score(student_id, assignment_id, points)
    return empty_book
