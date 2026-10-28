"""Stage 4: the class report shows two-decimal percents by default."""
import json

from gradebook.cli.main import main


def test_class_report_percents(tmp_path, capsys):
    course = tmp_path / "course.json"
    course.write_text(json.dumps({
        "code": "LAT",
        "title": "Latin",
        "categories": [{"name": "work", "weight": 100}],
        "assignments": [{"id": "w1", "category": "work", "max_points": 3, "due_day": 2},
                        {"id": "w2", "category": "work", "max_points": 3, "due_day": 3}],
    }), encoding="utf-8")
    book = tmp_path / "book.json"
    roster = tmp_path / "roster.csv"
    roster.write_text("student_id,last_name,first_name\ns1,Lovelace,Ada\ns2,Turing,Alan\n", encoding="utf-8")
    scores = tmp_path / "scores.csv"
    scores.write_text("student_id,assignment_id,points\ns1,w1,2\ns1,w2,3\ns2,w1,1\ns2,w2,3\n", encoding="utf-8")
    assert main(["new", str(course), "--book", str(book)]) == 0
    assert main(["import", "roster", str(roster), "--book", str(book)]) == 0
    assert main(["import", "scores", str(scores), "--book", str(book)]) == 0
    capsys.readouterr()
    assert main(["report", "--format", "csv", "--book", str(book)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [float(line.split(",")[2]) for line in lines[1:3]] == [83.33, 66.67]
