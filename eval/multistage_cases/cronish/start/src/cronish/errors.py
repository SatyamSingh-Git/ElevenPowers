"""The error raised for expressions that cannot be read or never run."""


class ScheduleError(ValueError):
    """A problem with a schedule, tied to the field it was found in when there is one."""

    def __init__(self, field, problem):
        super().__init__(f"{field}: {problem}" if field else problem)
        self.field = field
        self.problem = problem
