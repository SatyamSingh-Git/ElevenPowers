"""Scores: what a student earned on one assignment, and the sheet that holds them."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    points: float | None
    submitted_day: int | None = None
    excused: bool = False

    @property
    def missing(self):
        return self.points is None and not self.excused


class ScoreSheet:
    """Every recorded score in a course, keyed by student and assignment."""

    def __init__(self):
        self._scores = {}

    def __len__(self):
        return len(self._scores)

    def get(self, student_id, assignment_id):
        return self._scores.get((student_id, assignment_id))

    def set(self, student_id, assignment_id, score):
        self._scores[(student_id, assignment_id)] = score

    def remove(self, student_id, assignment_id):
        self._scores.pop((student_id, assignment_id), None)

    def for_student(self, student_id):
        return {assignment_id: score for (owner, assignment_id), score in self._scores.items()
                if owner == student_id}

    def for_assignment(self, assignment_id):
        return {student_id: score for (student_id, owner), score in self._scores.items()
                if owner == assignment_id}

    def copy(self):
        twin = ScoreSheet()
        twin._scores = dict(self._scores)
        return twin

    def items(self):
        """(student_id, assignment_id, score), sorted so saved files are stable."""
        return [(student_id, assignment_id, score)
                for (student_id, assignment_id), score in sorted(self._scores.items())]
