"""Loan terms by material, as the branch settings give them."""
from ..model.dates import add_days


def loan_days(settings, material):
    return settings.loan_days[material]


def due_date(library, material, start):
    """A loan or renewal made on `start` is due this many days later, or the next day the library opens."""
    return library.calendar.next_open_day(add_days(start, loan_days(library.settings, material)))


def daily_fine(settings, material):
    return settings.fine_per_day[material]
