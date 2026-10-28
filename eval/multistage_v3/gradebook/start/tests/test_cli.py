import json

from gradebook.cli.main import main

from conftest import ALGEBRA


def start(tmp_path):
    course = tmp_path / "course.json"
    course.write_text(json.dumps(ALGEBRA), encoding="utf-8")
    book = tmp_path / "book.json"
    assert main(["new", str(course), "--book", str(book)]) == 0
    roster = tmp_path / "roster.csv"
    roster.write_text("student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan\n", encoding="utf-8")
    assert main(["import", "roster", str(roster), "--book", str(book)]) == 0
    return book


def test_new_import_score_report(tmp_path, capsys):
    book = start(tmp_path)
    assert main(["score", "s1", "hw1", "9", "--book", str(book)]) == 0
    assert main(["score", "s2", "hw1", "EX", "--book", str(book)]) == 0
    capsys.readouterr()
    assert main(["report", "--format", "csv", "--as-of", "3", "--book", str(book)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "student_id,name,percent,letter"
    assert lines[1] == "s1,Ada Lovelace,90.0,A-"
    assert lines[2] == "s2,Alan Turing,,"


def test_errors_exit_with_one(tmp_path, capsys):
    book = start(tmp_path)
    assert main(["score", "s9", "hw1", "5", "--book", str(book)]) == 1
    assert capsys.readouterr().err == "error: unknown student s9\n"


def test_new_refuses_to_overwrite(tmp_path, capsys):
    book = start(tmp_path)
    assert main(["new", str(tmp_path / "course.json"), "--book", str(book)]) == 1
    assert "already exists" in capsys.readouterr().err


def test_check_reports_problems(tmp_path, capsys):
    book = start(tmp_path)
    document = json.loads(book.read_text(encoding="utf-8"))
    document["scores"].append({"student_id": "s1", "assignment_id": "hw9", "points": 3,
                               "submitted_day": None, "excused": False})
    book.write_text(json.dumps(document), encoding="utf-8")
    assert main(["check", "--book", str(book)]) == 3
    assert "s1/hw9: score for an assignment the course does not have" in capsys.readouterr().out


def test_init_course_writes_a_loadable_file(tmp_path, capsys):
    path = tmp_path / "starter.json"
    assert main(["init-course", str(path), "--code", "BIO1", "--title", "Biology"]) == 0
    assert main(["new", str(path), "--book", str(tmp_path / "bio.json")]) == 0


def test_day_and_date(tmp_path, capsys):
    calendar = tmp_path / "calendar.json"
    calendar.write_text(json.dumps({"start": "2026-09-01", "days_off": ["2026-09-07"]}), encoding="utf-8")
    assert main(["day", "2026-09-08", "--calendar", str(calendar)]) == 0
    assert main(["date", "5", "--calendar", str(calendar)]) == 0
    assert capsys.readouterr().out.split() == ["5", "2026-09-08"]
