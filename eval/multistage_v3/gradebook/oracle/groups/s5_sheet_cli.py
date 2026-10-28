"""Stage 5: `gradebook sheet` writes the name column too."""
import csv
import json

from gradebook.cli.main import main


def test_sheet_command(tmp_path, capsys):
    course = tmp_path / "course.json"
    course.write_text(json.dumps({
        "code": "DRA",
        "title": "Drama",
        "categories": [{"name": "work", "weight": 100}],
        "assignments": [{"id": "d1", "category": "work", "max_points": 10, "due_day": 2}],
    }), encoding="utf-8")
    book = tmp_path / "book.json"
    roster = tmp_path / "roster.csv"
    roster.write_text("student_id,last_name,first_name\ns7,Hopper,Grace\n", encoding="utf-8")
    assert main(["new", str(course), "--book", str(book)]) == 0
    assert main(["import", "roster", str(roster), "--book", str(book)]) == 0
    out = tmp_path / "sheet.csv"
    assert main(["sheet", str(out), "--book", str(book)]) == 0
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [["student_id", "name", "d1"], ["s7", "Hopper, Grace", ""]]
