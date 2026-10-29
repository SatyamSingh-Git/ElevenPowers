"""A copy out with a member."""
from dataclasses import dataclass
from datetime import date

from .dates import days_late


@dataclass
class Loan:
    barcode: str
    card: str
    issued: date
    due: date
    renewals: int = 0

    def is_overdue(self, today):
        return days_late(self.due, today) > 0

    def days_overdue(self, today):
        return max(0, days_late(self.due, today))
