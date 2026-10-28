import pytest

from gradebook.errors import UnknownFormat
from gradebook.grading.explain import explain_grade
from gradebook.reports.assignments import assignment_report
from gradebook.reports.attention import at_risk, missing_work
from gradebook.reports.categories import category_report
from gradebook.reports.course_outline import course_outline
from gradebook.reports.formatting import render
from gradebook.reports.late_work import late_work
from gradebook.reports.progress import progress_report, render_progress
from gradebook.reports.summary import class_summary


def test_class_summary_rows_by_name(book):
    table = class_summary(book)
    assert table.column("name") == ["Grace Hopper", "Ada Lovelace", "Alan Turing"]
    assert table.column("percent") == ["67.5", "93.0", "71.0"]
    assert table.column("letter") == ["D+", "A", "C-"]
    assert "Class average: 77.2" in table.notes


def test_class_summary_marks_ungraded_students(book):
    table = class_summary(book, as_of=2)
    assert table.column("letter") == ["", "", ""]
    assert table.notes == ["Students: 3, none graded yet"]


def test_formats(book):
    table = class_summary(book)
    assert render(table, "csv").splitlines()[1] == "s3,Grace Hopper,67.5,D+"
    markdown = render(table, "markdown")
    assert "| student_id | name | percent | letter |" in markdown
    assert "|---|---|---:|---|" in markdown
    text = render(table, "text")
    assert text.splitlines()[0] == "ALG1 Algebra I"


def test_unknown_format(book):
    with pytest.raises(UnknownFormat, match="unknown format pdf; choose text, csv or markdown"):
        render(class_summary(book), "pdf")


def test_progress_report(book):
    book.record_score("s2", "q2", 6, submitted_day=13)
    report = progress_report(book, "s2")
    assert report.percent == book.grade("s2").percent
    assert report.basis == "Weighted categories: homework 40%, quizzes 30%, exams 30%"
    assert report.item("hw1").status == "dropped"
    assert report.item("q2").status == "late"
    assert report.item("q2").earned == 5.0
    assert report.category("homework").percent == 75.0
    assert "Progress for Alan Turing (s2) in ALG1" in render_progress(report)


def test_progress_report_upcoming_and_missing(book):
    report = progress_report(book, "s3", as_of=12)
    assert report.item("hw3").status == "dropped"
    assert report.item("q2").status == "missing"
    assert report.item("ex1").status == "upcoming"


def test_assignment_report(book):
    table = assignment_report(book)
    row = table.rows[table.column("assignment_id").index("hw3")]
    assert row[4:] == ["2", "1", "0", "85.0", "90.0", "80.0"]


def test_category_report(book):
    table = category_report(book)
    assert table.rows[1] == ["quizzes", "30", "0", "3", "60.0", "93.3", "20.0"]


def test_missing_work_and_at_risk(book):
    missing = missing_work(book, as_of=12)
    assert [row[2] for row in missing.rows] == ["hw3", "q2"]
    risky = at_risk(book, as_of=15, below=72)
    assert risky.column("student_id") == ["s3", "s2"]
    assert risky.column("missing") == ["2", "0"]


def test_late_work(book):
    book.record_score("s1", "hw2", 10, submitted_day=9)
    table = late_work(book)
    assert table.rows == [["s1", "Ada Lovelace", "hw2", "2", "10", "8"]]


def test_course_outline(course):
    table = course_outline(course)
    assert table.column("assignment_id") == ["hw1", "q1", "hw2", "hw3", "q2", "ex1"]
    assert "Category homework: weight 40%, lowest 1 dropped, 3 assignments" in table.notes
    assert "Late rule: per_day (per_day 10, cap 50)" in table.notes


def test_explain_grade(book):
    lines = explain_grade(book.course, book.grade("s1"))
    assert lines[0] == "homework: 19 of 20 points = 95%"
    assert lines[-1] == "Final: 93.0%, rounded half up to 1 decimal(s), which is A on the standard scale"
