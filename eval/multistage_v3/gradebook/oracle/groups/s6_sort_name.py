"""Stage 6: `--sort name` is today's order and stays the default."""
import json

from gradebook.cli.main import main

COURSE = {
    "code": "SPAN",
    "title": "Spanish",
    "categories": [{"name": "work", "weight": 100}],
    "assignments": [{"id": "w1", "category": "work", "max_points": 10, "due_day": 2}],
}
ROSTER = ("student_id,last_name,first_name\n"
          "s1,Lovelace,Ada\ns2,Turing,Alan\ns3,Hopper,Grace\ns4,Noether,Emmy\ns5,Curie,Marie\n")
SCORES = "student_id,assignment_id,points\ns1,w1,7\ns2,w1,9\ns3,w1,EX\ns4,w1,4\ns5,w1,8\n"
BY_NAME = ["s5", "s3", "s1", "s4", "s2"]


def run_report(tmp_path, capsys, *options):
    course = tmp_path / "course.json"
    course.write_text(json.dumps(COURSE), encoding="utf-8")
    book = tmp_path / "book.json"
    (tmp_path / "roster.csv").write_text(ROSTER, encoding="utf-8")
    (tmp_path / "scores.csv").write_text(SCORES, encoding="utf-8")
    if not book.exists():
        assert main(["new", str(course), "--book", str(book)]) == 0
        assert main(["import", "roster", str(tmp_path / "roster.csv"), "--book", str(book)]) == 0
        assert main(["import", "scores", str(tmp_path / "scores.csv"), "--book", str(book)]) == 0
    capsys.readouterr()
    assert main(["report", *options, "--format", "csv", "--book", str(book)]) == 0
    return [line.split(",")[0] for line in capsys.readouterr().out.splitlines()[1:6]]


def test_sort_name_and_default_agree(tmp_path, capsys):
    assert run_report(tmp_path, capsys, "--sort", "name") == BY_NAME
    assert run_report(tmp_path, capsys) == BY_NAME
