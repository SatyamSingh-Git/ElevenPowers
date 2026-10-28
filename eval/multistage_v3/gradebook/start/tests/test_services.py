from datetime import date

import pytest

from gradebook.errors import ConfigError, GradebookError, RosterFull, ScoreOutOfRange, UnknownStudent
from gradebook.model.calendar import TermCalendar
from gradebook.model.student import Student
from gradebook.services import gradebook as gradebook_module
from gradebook.services.checks import check_gradebook
from gradebook.services.curve import curve_assignment
from gradebook.services.forecast import forecast
from gradebook.services.gradebook import Gradebook
from gradebook.services.merge import merge_sections
from gradebook.services.roster_sync import sync_roster
from gradebook.services.what_if import parse_weights, what_if
from gradebook.model.scores import Score


def test_record_score_checks_range_and_student(empty_book):
    with pytest.raises(ScoreOutOfRange, match="hw1: points 12 outside 0 to 10"):
        empty_book.record_score("s1", "hw1", 12)
    with pytest.raises(UnknownStudent, match="unknown student s9"):
        empty_book.record_score("s9", "hw1", 5)


def test_roster_limit(course, monkeypatch):
    monkeypatch.setattr(gradebook_module, "MAX_STUDENTS", 1)
    book = Gradebook(course)
    book.add_student(Student("s1", "Lovelace", "Ada"))
    with pytest.raises(RosterFull, match="a course holds at most 1 students"):
        book.add_student(Student("s2", "Turing", "Alan"))


def test_forecast_needed_percent(book):
    book.clear_score("s2", "ex1")
    assert forecast(book, "s2", "B", as_of=12).needed is None
    result = forecast(book, "s2", "C", as_of=12)
    assert result.remaining == ("ex1",)
    assert result.needed == 76.5


def test_forecast_out_of_reach_and_already_there(book):
    book.clear_score("s3", "ex1")
    assert not forecast(book, "s3", "A", as_of=12).reachable
    book.clear_score("s1", "ex1")
    assert forecast(book, "s1", "D", as_of=12).needed == 0.0


def test_curve_add_caps_at_max(book):
    assert curve_assignment(book, "q2", add=2) == 2
    assert book.sheet.get("s1", "q2").points == 10
    assert book.sheet.get("s2", "q2").points == 8


def test_curve_top(book):
    curve_assignment(book, "ex1", top=100)
    assert book.sheet.get("s1", "ex1").points == 100
    assert book.sheet.get("s2", "ex1").points == 77.78


def test_curve_needs_one_method(book):
    with pytest.raises(GradebookError):
        curve_assignment(book, "ex1")


def test_check_finds_hand_edits(book):
    assert check_gradebook(book) == []
    book.sheet.set("s9", "hw1", Score(5))
    book.sheet.set("s1", "hw1", Score(15))
    assert check_gradebook(book) == [
        "s1/hw1: points 15 outside 0 to 10",
        "s9/hw1: score for a student not on the roster",
    ]


def test_merge_sections(course, book):
    other = Gradebook(course)
    other.add_student(Student("s4", "Noether", "Emmy"))
    other.record_score("s4", "hw1", 10)
    assert merge_sections(book, other) == 1
    assert book.sheet.get("s4", "hw1").points == 10
    with pytest.raises(GradebookError, match="students in both sections: s4"):
        merge_sections(book, other)


def test_sync_roster(tmp_path, book):
    path = tmp_path / "office.csv"
    path.write_text("student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan M.\ns4,Noether,Emmy\n",
                    encoding="utf-8")
    changes = sync_roster(book, path)
    assert changes.added == ("s4",)
    assert changes.renamed == (("s2", "Alan Turing", "Alan M. Turing"),)
    assert changes.absent == ("s3",)


def test_what_if(book):
    table = what_if(book, parse_weights("homework=20,quizzes=30,exams=50"))
    assert table.column("new_percent") == ["66.5", "92.0", "70.0"]
    assert table.notes == ["2 letter(s) would change"]
    with pytest.raises(ConfigError, match="give a weight for exams"):
        what_if(book, parse_weights("homework=50,quizzes=50"))


def test_calendar_days_and_dates():
    calendar = TermCalendar(date(2026, 9, 1), frozenset({date(2026, 9, 7)}))
    assert calendar.date_of(1) == date(2026, 9, 1)
    assert calendar.date_of(5) == date(2026, 9, 8)
    assert calendar.day_of(date(2026, 9, 8)) == 5
    assert calendar.day_of(date(2026, 9, 5)) == 5
