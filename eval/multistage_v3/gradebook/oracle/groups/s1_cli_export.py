"""Stage 1: `gradebook export-grades` writes the term grades file with semicolons."""
import csv
import json

from gradebook.cli.main import main

COURSE = {
    "code": "ECON",
    "title": "Economics",
    "categories": [{"name": "work", "weight": 100}],
    "assignments": [
        {"id": "w1", "category": "work", "max_points": 10, "due_day": 2},
        {"id": "w2", "category": "work", "max_points": 10, "due_day": 4},
    ],
}


def test_export_grades_command(tmp_path, capsys):
    course = tmp_path / "course.json"
    course.write_text(json.dumps(COURSE), encoding="utf-8")
    book = tmp_path / "book.json"
    roster = tmp_path / "roster.csv"
    roster.write_text("student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan\n", encoding="utf-8")
    scores = tmp_path / "scores.csv"
    scores.write_text("student_id,assignment_id,points\ns1,w1,9\ns1,w2,8\ns2,w1,6\ns2,w2,7\n", encoding="utf-8")
    assert main(["new", str(course), "--book", str(book)]) == 0
    assert main(["import", "roster", str(roster), "--book", str(book)]) == 0
    assert main(["import", "scores", str(scores), "--book", str(book)]) == 0
    out = tmp_path / "grades.csv"
    assert main(["export-grades", str(out), "--book", str(book)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "student_id;name;course;credits;percent;letter"
    rows = list(csv.reader(text.splitlines(), delimiter=";"))
    assert [row[0] for row in rows[1:]] == ["s1", "s2"]
    assert [float(row[4]) for row in rows[1:]] == [85.0, 65.0]
    assert [row[5] for row in rows[1:]] == ["B", "D"]
