import pytest

from gradebook.errors import DuplicateStudent, ImportFailed, UnknownImportKind
from gradebook.services.gradebook import Gradebook


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_roster_import(tmp_path, course):
    book = Gradebook(course)
    path = write(tmp_path / "roster.csv", "student_id,last_name,first_name\ns1,Lovelace,Ada\ns2, Turing ,Alan\n")
    summary = book.import_file("roster", path)
    assert summary.recorded == 2
    assert [s.display_name for s in book.students] == ["Ada Lovelace", "Alan Turing"]


def test_roster_rejects_duplicates(tmp_path, course):
    book = Gradebook(course)
    path = write(tmp_path / "roster.csv", "student_id,last_name,first_name\ns1,Lovelace,Ada\ns1,Byron,Ada\n")
    with pytest.raises(ImportFailed, match="line 3: duplicate student s1"):
        book.import_file("roster", path)


def test_roster_needs_its_columns(tmp_path, course):
    path = write(tmp_path / "roster.csv", "id,last_name,first_name\ns1,Lovelace,Ada\n")
    with pytest.raises(ImportFailed, match="roster.csv: missing column student_id"):
        Gradebook(course).import_file("roster", path)


def test_scores_import(tmp_path, empty_book):
    path = write(tmp_path / "scores.csv",
                 "student_id,assignment_id,points,submitted_day\n"
                 "s1,hw1,9,\n"
                 "s1,hw2,EX,\n"
                 "s2,hw1,,\n"
                 "s2,hw2,7.5,9\n")
    summary = empty_book.import_file("scores", path)
    assert (summary.rows, summary.recorded, summary.skipped) == (4, 3, 1)
    assert empty_book.sheet.get("s1", "hw1").points == 9
    assert empty_book.sheet.get("s1", "hw2").excused
    assert empty_book.sheet.get("s2", "hw1") is None
    assert empty_book.sheet.get("s2", "hw2").submitted_day == 9


def test_scores_import_reports_bad_rows(tmp_path, empty_book):
    path = write(tmp_path / "scores.csv", "student_id,assignment_id,points\ns1,hw1,ten\n")
    with pytest.raises(ImportFailed, match="line 2: cannot read points ten"):
        empty_book.import_file("scores", path)
    path = write(tmp_path / "scores.csv", "student_id,assignment_id,points\ns1,hw1,11\n")
    with pytest.raises(ImportFailed, match="line 2: hw1: points 11 outside 0 to 10"):
        empty_book.import_file("scores", path)


def test_sheet_import(tmp_path, empty_book):
    path = write(tmp_path / "sheet.csv", "student_id,hw1,q1\ns1,9,EX\ns2,,4\n")
    summary = empty_book.import_file("sheet", path)
    assert summary.recorded == 3
    assert empty_book.sheet.get("s1", "q1").excused
    assert empty_book.sheet.get("s2", "q1").points == 4


def test_sheet_import_keeps_submission_days(tmp_path, empty_book):
    empty_book.record_score("s1", "hw1", 5, submitted_day=6)
    path = write(tmp_path / "sheet.csv", "student_id,hw1\ns1,8\n")
    empty_book.import_file("sheet", path)
    assert empty_book.sheet.get("s1", "hw1").submitted_day == 6


def test_sheet_with_unknown_assignment(tmp_path, empty_book):
    path = write(tmp_path / "sheet.csv", "student_id,hw9\ns1,9\n")
    with pytest.raises(ImportFailed, match="sheet.csv: unknown assignment hw9"):
        empty_book.import_file("sheet", path)


def test_lms_import(tmp_path, empty_book):
    path = write(tmp_path / "lms.csv",
                 "Student,ID,Section,Homework 1 (hw1),Quiz 1 (q1)\n"
                 "Points Possible,,,10,5\n"
                 "\"Lovelace, Ada\",s1,A,10,EX\n"
                 "\"Turing, Alan\",s2,A,,3\n")
    summary = empty_book.import_file("lms", path)
    assert summary.recorded == 3
    assert empty_book.sheet.get("s1", "hw1").points == 10
    assert empty_book.sheet.get("s2", "q1").points == 3


def test_lms_points_possible_must_match(tmp_path, empty_book):
    path = write(tmp_path / "lms.csv",
                 "Student,ID,Homework 1 (hw1)\nPoints Possible,,20\n")
    with pytest.raises(ImportFailed, match="hw1 is out of 20 in the LMS but 10 in the course"):
        empty_book.import_file("lms", path)


def test_unknown_import_kind(tmp_path, empty_book):
    with pytest.raises(UnknownImportKind, match="unknown import kind grades"):
        empty_book.import_file("grades", tmp_path / "x.csv")


def test_duplicate_student_through_the_api(empty_book):
    with pytest.raises(DuplicateStudent):
        empty_book.add_student(empty_book.student("s1"))
