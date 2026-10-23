"""Jobs files: one named schedule per line, and what is due from them."""
from collections import defaultdict
from dataclasses import dataclass
import re

from .expression import Schedule, parse
from .planner import DEFAULT_COUNT, next_runs, runs_between
from .validate import validate

COMMENT = "#"
JOB_NAME = re.compile(r"[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class Job:
    name: str
    schedule: Schedule


class JobFileError(ValueError):
    pass


def load_jobs(text):
    """Jobs from text where each line is ``<name> <expression>``; ``#`` starts a comment line."""
    jobs, seen = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(COMMENT):
            continue
        name, expression = (line.split(maxsplit=1) + [""])[:2]
        if not JOB_NAME.fullmatch(name):
            raise JobFileError(f"line {number}: invalid job name '{name}'")
        problems = validate(expression)
        if problems:
            raise JobFileError(f"line {number}: {problems[0]}")
        if name in seen:
            raise JobFileError(f"line {number}: duplicate job '{name}'")
        seen.add(name)
        jobs.append(Job(name, parse(expression)))
    return jobs


def due_jobs(jobs, now):
    """Names of the jobs that run in the minute containing `now`, in file order."""
    minute = now.replace(second=0, microsecond=0)
    return [job.name for job in jobs if next_runs(job.schedule, minute, 1) == [minute]]


def upcoming(jobs, now, count=DEFAULT_COUNT):
    """The next `count` runs across all jobs as ``(moment, name)`` pairs, earliest first."""
    timeline = []
    for job in jobs:
        timeline.extend((run, job.name) for run in next_runs(job.schedule, now, count))
    return sorted(timeline)[:count]


def overlaps(jobs, start, end):
    """Moments from `start` up to `end` when more than one job runs, with those jobs' names."""
    running = defaultdict(list)
    for job in jobs:
        for run in runs_between(job.schedule, start, end):
            running[run].append(job.name)
    return [(moment, names) for moment, names in sorted(running.items()) if len(names) > 1]
