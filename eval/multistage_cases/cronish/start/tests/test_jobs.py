from datetime import datetime

import pytest

from cronish import JobFileError, due_jobs, load_jobs, overlaps, upcoming

JOBS = """\
# nightly and weekly work
backup 0 10 * * sun
report 30 9 * * mon-fri

tick * * * * *
"""


def test_load_skips_comments_and_blank_lines():
    assert [job.name for job in load_jobs(JOBS)] == ["backup", "report", "tick"]


def test_tabs_separate_the_name():
    assert load_jobs("backup\t0 2 * * *")[0].schedule.hours == (2,)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("a * * * * *\nb 61 * * * *", "line 2: minute: value 61 out of range 0-59"),
        ("a 0 0 30 2 *", "line 1: day: no selected month has a day 30"),
        ("a * * * * *\n# b\na 0 * * * *", "line 3: duplicate job 'a'"),
        ("a/b * * * * *", "line 1: invalid job name 'a/b'"),
        ("lonely", "line 1: expression: expected 5 fields, got 0"),
    ],
)
def test_load_errors(text, message):
    with pytest.raises(JobFileError) as caught:
        load_jobs(text)
    assert str(caught.value) == message


def test_due_jobs_in_the_current_minute():
    jobs = load_jobs(JOBS)
    assert due_jobs(jobs, datetime(2024, 3, 10, 10, 0)) == ["backup", "tick"]
    assert due_jobs(jobs, datetime(2024, 3, 11, 9, 30, 45)) == ["report", "tick"]
    assert due_jobs(jobs, datetime(2024, 3, 11, 9, 31)) == ["tick"]


def test_upcoming_merges_jobs():
    jobs = load_jobs(JOBS)[:2]
    assert upcoming(jobs, datetime(2024, 3, 6, 10, 17), 3) == [
        (datetime(2024, 3, 7, 9, 30), "report"),
        (datetime(2024, 3, 8, 9, 30), "report"),
        (datetime(2024, 3, 10, 10, 0), "backup"),
    ]


def test_overlaps():
    jobs = load_jobs("a 0 * * * *\nb 0 */2 * * *\nc 30 1 * * *")
    assert overlaps(jobs, datetime(2024, 3, 6, 0, 0), datetime(2024, 3, 6, 4, 0)) == [
        (datetime(2024, 3, 6, 0, 0), ["a", "b"]),
        (datetime(2024, 3, 6, 2, 0), ["a", "b"]),
    ]
