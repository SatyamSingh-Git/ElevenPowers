import pytest

from cronish import JobFileError, load_jobs
from cronish.cli import main


def test_check_reports_a_zero_step(capsys):
    assert main(["check", "*/0 * * * *"]) == 1
    assert capsys.readouterr().out == "minute: step must be at least 1\n"


def test_next_reports_a_zero_step(capsys):
    assert main(["next", "0 */0 * * *", "--now", "2024-03-06T09:00"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "hour: step must be at least 1" in captured.err


def test_jobs_file_with_a_zero_step():
    with pytest.raises(JobFileError) as caught:
        load_jobs("ok 0 9 * * *\nbad */0 * * * *")
    assert str(caught.value) == "line 2: minute: step must be at least 1"
