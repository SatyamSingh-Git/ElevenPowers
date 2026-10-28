"""The gradebook: one course, its roster and its scores."""
from pathlib import Path

from ..errors import DuplicateStudent, RosterFull, ScoreOutOfRange, UnknownStudent
from ..grading.calculator import compute_grade
from ..model.scores import Score, ScoreSheet
from ..storage.importers import get_importer

MAX_STUDENTS = 500


class Gradebook:
    def __init__(self, course):
        self.course = course
        self.sheet = ScoreSheet()
        self._students = {}

    @property
    def students(self):
        """The roster, by student id."""
        return [self._students[key] for key in sorted(self._students)]

    def student(self, student_id):
        try:
            return self._students[student_id]
        except KeyError:
            raise UnknownStudent(student_id) from None

    def add_student(self, student):
        if student.student_id in self._students:
            raise DuplicateStudent(student.student_id)
        if len(self._students) >= MAX_STUDENTS:
            raise RosterFull(MAX_STUDENTS)
        self._students[student.student_id] = student

    def replace_student(self, student):
        """Update a student's name; their scores stay with their id."""
        self.student(student.student_id)
        self._students[student.student_id] = student

    def remove_student(self, student_id):
        self.student(student_id)
        del self._students[student_id]
        for assignment_id in self.sheet.for_student(student_id):
            self.sheet.remove(student_id, assignment_id)

    def record_score(self, student_id, assignment_id, points, submitted_day=None):
        self.student(student_id)
        assignment = self.course.assignment(assignment_id)
        if not 0 <= points <= assignment.max_points:
            raise ScoreOutOfRange(assignment_id, points, assignment.max_points)
        self.sheet.set(student_id, assignment_id, Score(points, submitted_day))

    def excuse(self, student_id, assignment_id):
        self.student(student_id)
        self.course.assignment(assignment_id)
        self.sheet.set(student_id, assignment_id, Score(None, excused=True))

    def clear_score(self, student_id, assignment_id):
        self.student(student_id)
        self.course.assignment(assignment_id)
        self.sheet.remove(student_id, assignment_id)

    def submitted_day(self, student_id, assignment_id):
        score = self.sheet.get(student_id, assignment_id)
        return None if score is None else score.submitted_day

    def grade(self, student_id, as_of=None):
        self.student(student_id)
        return compute_grade(self.course, self.sheet, student_id, as_of)

    def grades(self, as_of=None):
        """(student, course grade) for the whole roster, by student id."""
        return [(student, compute_grade(self.course, self.sheet, student.student_id, as_of))
                for student in self.students]

    def import_file(self, kind, path):
        return get_importer(kind)(self, Path(path))
