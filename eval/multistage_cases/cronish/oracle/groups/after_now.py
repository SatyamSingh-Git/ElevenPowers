from datetime import datetime

from cronish import next_runs, parse
from cronish.cli import main


def test_a_run_exactly_at_now_is_skipped():
    now = datetime(2024, 3, 6, 9, 0)
    assert next_runs(parse("0 9 * * *"), now, 2) == [datetime(2024, 3, 7, 9), datetime(2024, 3, 8, 9)]
    assert next_runs(parse("* * * * *"), now, 1) == [datetime(2024, 3, 6, 9, 1)]


def test_seconds_still_round_up():
    assert next_runs(parse("0 9 * * *"), datetime(2024, 3, 6, 8, 59, 30), 1) == [datetime(2024, 3, 6, 9)]
    assert next_runs(parse("0 9 * * *"), datetime(2024, 3, 6, 9, 0, 30), 1) == [datetime(2024, 3, 7, 9)]


def test_next_command_starts_after_now(capsys):
    assert main(["next", "0 9 * * *", "--now", "2024-03-06T09:00", "-n", "2"]) == 0
    assert capsys.readouterr().out == "2024-03-07 09:00 Thu\n2024-03-08 09:00 Fri\n"
    assert main(["next", "30 14 * * *", "--now", "2024-03-06T09:00", "-n", "1"]) == 0
    assert capsys.readouterr().out == "2024-03-06 14:30 Wed\n"
