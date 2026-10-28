"""Errors the gradebook reports. Their messages are listed in docs/reference.md."""


class GradebookError(Exception):
    """Base class for every error shown to a user."""


class ConfigError(GradebookError):
    """A course file is malformed or inconsistent."""


class UnknownPolicy(ConfigError):
    def __init__(self, name, choices):
        super().__init__(f"unknown scoring policy {name}; choose {' or '.join(choices)}")
        self.name = name


class UnknownScale(ConfigError):
    def __init__(self, name):
        super().__init__(f"unknown letter scale {name}")
        self.name = name


class UnknownLateRule(ConfigError):
    def __init__(self, name):
        super().__init__(f"unknown late rule {name}")
        self.name = name


class UnknownStudent(GradebookError):
    def __init__(self, student_id):
        super().__init__(f"unknown student {student_id}")
        self.student_id = student_id


class UnknownAssignment(GradebookError):
    def __init__(self, assignment_id):
        super().__init__(f"unknown assignment {assignment_id}")
        self.assignment_id = assignment_id


class DuplicateStudent(GradebookError):
    def __init__(self, student_id):
        super().__init__(f"duplicate student {student_id}")
        self.student_id = student_id


class RosterFull(GradebookError):
    def __init__(self, limit):
        super().__init__(f"a course holds at most {limit} students")
        self.limit = limit


class ScoreOutOfRange(GradebookError):
    def __init__(self, assignment_id, points, max_points):
        super().__init__(f"{assignment_id}: points {points:g} outside 0 to {max_points:g}")
        self.assignment_id = assignment_id


class ImportFailed(GradebookError):
    """A file being imported or read cannot be used as it is."""


class UnknownImportKind(GradebookError):
    def __init__(self, kind):
        super().__init__(f"unknown import kind {kind}")
        self.kind = kind


class UnknownFormat(GradebookError):
    def __init__(self, name, choices):
        listed = ", ".join(choices[:-1]) + f" or {choices[-1]}"
        super().__init__(f"unknown format {name}; choose {listed}")
        self.name = name


class NotOnTranscript(GradebookError):
    def __init__(self, student_id):
        super().__init__(f"student {student_id} is not in any posted grades file")
        self.student_id = student_id
