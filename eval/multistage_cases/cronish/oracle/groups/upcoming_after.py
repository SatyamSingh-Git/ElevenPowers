from datetime import datetime

from cronish import load_jobs, upcoming
from cronish.cli import main

JOBS = "a 0 9 * * *\nb 30 9 * * *\n"


def test_upcoming_skips_runs_exactly_at_now():
    assert upcoming(load_jobs(JOBS), datetime(2024, 3, 6, 9, 0), 3) == [
        (datetime(2024, 3, 6, 9, 30), "b"),
        (datetime(2024, 3, 7, 9, 0), "a"),
        (datetime(2024, 3, 7, 9, 30), "b"),
    ]


def test_upcoming_command(capsys, tmp_path):
    path = tmp_path / "jobs.txt"
    path.write_text(JOBS, encoding="utf-8")
    assert main(["upcoming", str(path), "--now", "2024-03-06T09:00", "-n", "3"]) == 0
    assert capsys.readouterr().out == "2024-03-06 09:30 Wed b\n2024-03-07 09:00 Thu a\n2024-03-07 09:30 Thu b\n"


def test_due_command_still_sees_the_current_minute(capsys, tmp_path):
    path = tmp_path / "jobs.txt"
    path.write_text(JOBS, encoding="utf-8")
    assert main(["due", str(path), "--now", "2024-03-06T09:30"]) == 0
    assert capsys.readouterr().out == "b\n"
