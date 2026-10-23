from datetime import datetime
import json

import pytest

from cronish.cli import main

NOW = "2024-03-06T10:17"


def run(capsys, *argv):
    code = main(list(argv), clock=lambda: datetime(2024, 3, 6, 10, 17))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_next(capsys):
    assert run(capsys, "next", "30 9 * * mon-fri", "-n", "2", "--now", NOW) == (
        0,
        "2024-03-07 09:30 Thu\n2024-03-08 09:30 Fri\n",
        "",
    )


def test_next_uses_the_clock_without_now(capsys):
    code, out, _ = run(capsys, "next", "0 12 * * *", "-n", "1")
    assert out == "2024-03-06 12:00 Wed\n"


def test_next_json(capsys):
    code, out, _ = run(capsys, "next", "0 12 * * *", "-n", "2", "--json", "--now", NOW)
    assert json.loads(out) == ["2024-03-06T12:00:00", "2024-03-07T12:00:00"]


def test_last_and_between(capsys):
    assert run(capsys, "last", "0 10 * * sun", "--now", NOW)[1] == "2024-03-03 10:00 Sun\n"
    out = run(capsys, "between", "0 */12 * * *", "2024-03-06T00:00", "2024-03-07T00:00")[1]
    assert out == "2024-03-06 00:00 Wed\n2024-03-06 12:00 Wed\n"


def test_describe(capsys):
    assert run(capsys, "describe", "0 0 13 * fri")[1] == "at 00:00, on day 13 of the month or on Friday\n"


def test_check(capsys):
    assert run(capsys, "check", "@daily") == (0, "ok\n", "")
    assert run(capsys, "check", "61 * * * *") == (1, "minute: value 61 out of range 0-59\n", "")


def test_fields(capsys):
    assert run(capsys, "fields", "*/30 9 * * mon")[1] == (
        "minute: 0, 30\nhour: 9\nday: every value\nmonth: every value\nweekday: 1\n"
    )


def test_errors_go_to_stderr(capsys):
    assert run(capsys, "next", "* * *", "--now", NOW) == (1, "", "cronish: expression: expected 5 fields, got 3\n")


def test_usage_errors_exit_2(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["next"])
    assert caught.value.code == 2


@pytest.fixture
def jobs_file(tmp_path):
    path = tmp_path / "jobs.txt"
    path.write_text("backup 0 10 * * sun\nreport 30 9 * * mon-fri\n", encoding="utf-8")
    return str(path)


def test_jobs_commands(capsys, jobs_file):
    assert run(capsys, "list", jobs_file)[1] == (
        "backup: at 10:00, on Sunday\nreport: at 09:30, on Monday, Tuesday, Wednesday, Thursday and Friday\n"
    )
    assert run(capsys, "due", jobs_file, "--now", "2024-03-10T10:00")[1] == "backup\n"
    assert run(capsys, "upcoming", jobs_file, "-n", "2", "--now", NOW)[1] == (
        "2024-03-07 09:30 Thu report\n2024-03-08 09:30 Fri report\n"
    )


def test_upcoming_json(capsys, jobs_file):
    out = run(capsys, "upcoming", jobs_file, "-n", "1", "--json", "--now", NOW)[1]
    assert json.loads(out) == [{"at": "2024-03-07T09:30:00", "job": "report"}]


def test_overlaps_command(capsys, tmp_path):
    path = tmp_path / "jobs.txt"
    path.write_text("a 0 * * * *\nb 0 */2 * * *\n", encoding="utf-8")
    out = run(capsys, "overlaps", str(path), "--hours", "3", "--now", "2024-03-06T00:00")[1]
    assert out == "2024-03-06 00:00 Wed a, b\n2024-03-06 02:00 Wed a, b\n"


def test_missing_jobs_file(capsys, tmp_path):
    code, _, err = run(capsys, "due", str(tmp_path / "absent.txt"), "--now", NOW)
    assert code == 1 and err.startswith("cronish: ")
