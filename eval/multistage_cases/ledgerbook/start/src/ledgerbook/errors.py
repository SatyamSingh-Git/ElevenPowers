class LedgerError(Exception):
    """Base class for every error ledgerbook raises on bad input."""


class AmountError(LedgerError):
    """An amount that cannot be read in the currency it was given in."""


class AccountError(LedgerError):
    """A malformed, duplicate or unknown account name."""


class UnbalancedError(LedgerError):
    """Postings whose amounts do not sum to zero."""


class JournalError(LedgerError):
    """A journal file that cannot be replayed; carries the 1-based line number."""

    def __init__(self, line, problem):
        super().__init__(f"line {line}: {problem}")
        self.line = line
        self.problem = problem
