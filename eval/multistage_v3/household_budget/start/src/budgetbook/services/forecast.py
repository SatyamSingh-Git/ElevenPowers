"""Where an account's balance is heading, from what it holds today and what is due."""
from dataclasses import dataclass
import datetime as dt

from ..storage import files
from .accounts import balances, require_account
from .recurring import due_dates


@dataclass(frozen=True)
class ForecastLine:
    date: dt.date
    description: str
    amount: int
    balance: int


@dataclass(frozen=True)
class Forecast:
    account: str
    start: dt.date
    opening: int
    lines: list

    @property
    def lowest(self):
        """The lowest balance the account reaches, and the first date it does so."""
        low, on = self.opening, self.start
        for line in self.lines:
            if line.balance < low:
                low, on = line.balance, line.date
        return low, on


def forecast(workspace, account_name, today, days):
    """The account's balance at the end of `today`, then every recurring item due in the next `days` days.

    Only recurring items are projected; one-off spending is not guessed at.
    """
    account = require_account(workspace, account_name)
    opening = balances(workspace, through=today)[account.name]
    last = today + dt.timedelta(days=days)
    due = sorted(
        ((day, item) for item in files.load_recurring(workspace) if item.account == account.name
         for day in due_dates(item, today + dt.timedelta(days=1), last)),
        key=lambda pair: (pair[0], pair[1].name),
    )
    balance, lines = opening, []
    for day, item in due:
        balance += item.amount
        lines.append(ForecastLine(day, item.name, item.amount, balance))
    return Forecast(account.name, today, opening, lines)
