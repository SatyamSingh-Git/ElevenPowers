"""Errors the command line reports to the user as ``error: <message>``.

Anything else that escapes is a bug and is left to show its traceback.
"""


class BudgetError(Exception):
    """A problem with the user's input or workspace."""


class ValidationError(BudgetError):
    """A value the user gave cannot be accepted."""


class NotFound(BudgetError):
    """An account, category or transaction the user named does not exist."""


class StatementError(BudgetError):
    """A statement file that cannot be imported at all."""
