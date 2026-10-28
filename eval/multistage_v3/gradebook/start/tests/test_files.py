import csv
import json
import zipfile

import pytest

from gradebook.errors import ConfigError
from gradebook.reports.score_sheet import write_score_sheet
from gradebook.storage.archive import archive_term
from gradebook.storage.gradebook_file import load_gradebook, save_gradebook
from gradebook.storage.grades_csv import export_grades
from gradebook.storage.scores_export import export_scores


def test_gradebook_round_trip(tmp_path, book):
    book.excuse("s3", "q2")
    book.record_score("s2", "hw3", 8, submitted_day=12)
    path = tmp_path / "book.json"
    save_gradebook(book, path)
    loaded = load_gradebook(path)
    assert loaded.course == book.course
    assert loaded.students == book.students
    assert loaded.sheet.items() == book.sheet.items()


def test_gradebook_file_format_is_checked(tmp_path, book):
    path = tmp_path / "book.json"
    save_gradebook(book, path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["format"] = 7
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ConfigError, match="gradebook format 7 is not supported"):
        load_gradebook(path)


def test_export_grades(tmp_path, book):
    path = tmp_path / "grades.csv"
    assert export_grades(book, path) == 3
    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == ["student_id", "name", "course", "credits", "percent", "letter"]
    first = rows[1]
    assert first[:4] == ["s1", "Ada Lovelace", "ALG1", "1"]
    assert float(first[4]) == 93.0
    assert first[5] == "A"


def test_export_grades_leaves_ungraded_blank(tmp_path, book):
    path = tmp_path / "grades.csv"
    export_grades(book, path, as_of=2)
    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[1][4:] == ["", ""]


def test_export_scores_reads_back(tmp_path, book):
    book.excuse("s3", "q2")
    book.record_score("s2", "hw3", 8, submitted_day=12)
    path = tmp_path / "scores.csv"
    export_scores(book, path)
    copy = type(book)(book.course)
    for student in book.students:
        copy.add_student(student)
    copy.import_file("scores", path)
    assert copy.sheet.items() == book.sheet.items()


def test_score_sheet(tmp_path, book):
    path = tmp_path / "sheet.csv"
    assert write_score_sheet(book, path) == 3
    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == ["student_id", "hw1", "q1", "hw2", "hw3", "q2", "ex1"]
    assert rows[3] == ["s3", "9", "3", "9", "", "", "85"]


def test_archive_is_repeatable(tmp_path, book):
    first, second = tmp_path / "a.zip", tmp_path / "b.zip"
    names = archive_term(book, first, tmp_path / "a")
    archive_term(book, second, tmp_path / "b")
    assert first.read_bytes() == second.read_bytes()
    assert zipfile.ZipFile(first).namelist() == names
