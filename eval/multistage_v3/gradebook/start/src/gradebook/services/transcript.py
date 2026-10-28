"""Transcripts, built from the term grades files each course posts.

A course whose posted letter is blank has no grade yet: it is listed but
counts toward neither credits nor the GPA. P and NP earn or fail credits
without counting toward the GPA.
"""
import csv
from dataclasses import dataclass
from pathlib import Path

from .._generated import GRADE_POINTS
from ..errors import ImportFailed, NotOnTranscript
from ..grading.rounding import exact, round_half_up

POSTED_COLUMNS = ("student_id", "name", "course", "credits", "percent", "letter")
NO_CREDIT = {"F", "NP"}
GPA_DECIMALS = 2


@dataclass(frozen=True)
class PostedGrade:
    student_id: str
    name: str
    course: str
    credits: float
    percent: float | None
    letter: str


@dataclass(frozen=True)
class TranscriptLine:
    course: str
    credits: float
    percent: float | None
    letter: str


@dataclass(frozen=True)
class Transcript:
    student_id: str
    name: str
    lines: tuple
    credits_attempted: float
    credits_earned: float
    gpa: float | None

    def line(self, course):
        for line in self.lines:
            if line.course == course:
                return line
        raise KeyError(course)


def read_posted_grades(path):
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for column in POSTED_COLUMNS:
            if column not in (reader.fieldnames or []):
                raise ImportFailed(f"{path.name}: missing column {column}")
        return [_posted(row, path, reader.line_num) for row in reader]


def _posted(row, path, line):
    try:
        credits = float(row["credits"])
        percent = float(row["percent"]) if row["percent"] else None
    except ValueError:
        raise ImportFailed(f"{path.name} line {line}: credits and percent must be numbers") from None
    return PostedGrade(row["student_id"], row["name"], row["course"], credits, percent, row["letter"])


def build_transcript(student_id, paths):
    """The student's transcript from posted grades files; a later file wins for the same course."""
    lines, name = {}, None
    for path in paths:
        for posted in read_posted_grades(path):
            if posted.student_id != student_id:
                continue
            name = posted.name
            lines[posted.course] = TranscriptLine(posted.course, posted.credits, posted.percent, posted.letter)
    if name is None:
        raise NotOnTranscript(student_id)
    ordered = tuple(lines[course] for course in sorted(lines))
    attempted, earned, gpa = _credit_totals(ordered)
    return Transcript(student_id, name, ordered, attempted, earned, gpa)


def _credit_totals(lines):
    attempted = earned = gpa_credits = quality = exact(0)
    for line in lines:
        if not line.letter:
            continue
        credits = exact(line.credits)
        attempted += credits
        if line.letter not in NO_CREDIT:
            earned += credits
        if line.letter in GRADE_POINTS:
            quality += exact(GRADE_POINTS[line.letter]) * credits
            gpa_credits += credits
    gpa = round_half_up(quality / gpa_credits, GPA_DECIMALS) if gpa_credits else None
    return float(attempted), float(earned), gpa


def render_transcript(transcript):
    out = [f"Transcript for {transcript.name} ({transcript.student_id})", ""]
    for line in transcript.lines:
        percent = "" if line.percent is None else f"{line.percent:g}"
        out.append(f"{line.course:<10} {line.credits:>5g}  {percent:>6}  {line.letter or '-'}")
    out.append("")
    out.append(f"Credits attempted: {transcript.credits_attempted:g}")
    out.append(f"Credits earned: {transcript.credits_earned:g}")
    gpa = "-" if transcript.gpa is None else f"{transcript.gpa:.{GPA_DECIMALS}f}"
    out.append(f"GPA: {gpa}")
    return "\n".join(out) + "\n"
