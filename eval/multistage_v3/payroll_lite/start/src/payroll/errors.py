class PayrollError(Exception):
    """A problem the user can fix: bad input, missing data or a request that conflicts with saved data."""


class ImportRejected(PayrollError):
    """An uploaded timesheet had rows that could not be accepted; nothing from it was kept."""

    def __init__(self, problems):
        super().__init__(f"{len(problems)} row(s) rejected")
        self.problems = problems
