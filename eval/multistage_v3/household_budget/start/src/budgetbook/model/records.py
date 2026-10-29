"""The records a workspace stores. Every amount is integer cents."""
from dataclasses import dataclass
import datetime as dt

ACCOUNT_KINDS = ("checking", "savings", "credit")
FREQUENCIES = ("month", "week")


@dataclass(frozen=True)
class Account:
    name: str
    kind: str
    opening: int = 0


@dataclass(frozen=True)
class Transaction:
    id: int
    date: dt.date
    account: str
    payee: str
    amount: int
    category: str = ""
    memo: str = ""
    source: str = "manual"

    @property
    def uncategorised(self):
        return not self.category


@dataclass(frozen=True)
class Rule:
    match: str
    pattern: str
    category: str
    account: str = ""

    def applies_to(self, account):
        return not self.account or self.account == account


@dataclass(frozen=True)
class RecurringItem:
    name: str
    account: str
    payee: str
    amount: int
    category: str
    every: str
    day: int
    start: dt.date
    end: dt.date | None = None

    @property
    def source(self):
        return f"recurring:{self.name}"


@dataclass(frozen=True)
class BudgetLine:
    category: str
    amount: int
    rollover: bool = False


@dataclass(frozen=True)
class Goal:
    name: str
    account: str
    target: int
    by: dt.date
