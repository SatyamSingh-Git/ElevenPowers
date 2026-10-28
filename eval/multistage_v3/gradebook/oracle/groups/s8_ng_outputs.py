"""Stage 8: the class report and the term grades file show NG too."""
import csv
import json

from gradebook.cli.main import main

COURSE = {
    "code": "BIO1",
    "title": "Biology",
    "categories": [{"name": "labs", "weight": 50}, {"name": "tests", "weight": 50}],
    "assignments": [
        {"id": "lab1", "category": "labs", "max_points": 20, "due_day": 5},
        {"id": "test1", "category": "tests", "max_points": 100, "due_day": 10},
    ],
}


def make_book(tmp_path):
    course = tmp_path / "course.json"
    course.write_text(json.dumps(COURSE), encoding="utf-8")
    book = tmp_path / "book.json"
    roster = tmp_path / "roster.csv"
    roster.write_text("student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan\n", encoding="utf-8")
    scores = tmp_path / "scores.csv"
    scores.write_text("student_id,assignment_id,points\ns1,lab1,18\ns2,lab1,EX\n", encoding="utf-8")
    assert main(["new", str(course), "--book", str(book)]) == 0
    assert main(["import", "roster", str(roster), "--book", str(book)]) == 0
    assert main(["import", "scores", str(scores), "--book", str(book)]) == 0
    return book


def test_class_report(tmp_path, capsys):
    book = make_book(tmp_path)
    capsys.readouterr()
    assert main(["report", "--format", "csv", "--as-of", "6", "--book", str(book)]) == 0
    rows = list(csv.reader(capsys.readouterr().out.splitlines()))
    by_id = {row[0]: row for row in rows[1:3]}
    assert by_id["s2"][2:] == ["", "NG"]
    assert by_id["s1"][3] == "A-"


def test_term_grades_file(tmp_path, capsys):
    book = make_book(tmp_path)
    out = tmp_path / "grades.csv"
    assert main(["export-grades", str(out), "--as-of", "6", "--book", str(book)]) == 0
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    by_id = {row[0]: row for row in rows[1:]}
    assert by_id["s2"][4:] == ["", "NG"]
    assert by_id["s1"][5] == "A-"
