"""Pay periods: how the calendar is cut into weeks, fortnights or months."""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta
import re

from payroll.errors import PayrollError

# frequency -> (letter used in period ids, periods in a year)
FREQUENCIES = {
    "weekly": ("W", 52),
    "fortnightly": ("F", 26),
    "monthly": ("M", 12),
}
PERIOD_ID = re.compile(r"(\d{4})-([WFM])(\d{2})")


@dataclass(frozen=True)
class PayPeriod:
    id: str
    start: date
    end: date
    pay_date: date

    def contains(self, day):
        return self.start <= day <= self.end

    def days(self):
        return [self.start + timedelta(days=n) for n in range((self.end - self.start).days + 1)]

    def describe(self):
        return f"{self.id}: {self.start.isoformat()} to {self.end.isoformat()}, paid {self.pay_date.isoformat()}"


class PayCalendar:
    """Periods follow one another from the first period's start date and are numbered within a year.

    A weekly or fortnightly period belongs to the year it starts in. Monthly periods are
    calendar months; for them the first period's start only says which month payroll began.
    """

    def __init__(self, frequency, first_start, pay_delay_days):
        if frequency not in FREQUENCIES:
            raise PayrollError(f"unknown pay frequency {frequency}; expected one of {', '.join(FREQUENCIES)}")
        self.frequency = frequency
        self.first_start = first_start
        self.pay_delay_days = pay_delay_days
        self.letter, self.periods_per_year = FREQUENCIES[frequency]

    def periods_in_year(self, year):
        if self.frequency == "monthly":
            began = (self.first_start.year, self.first_start.month)
            return [self._month(year, month) for month in range(1, 13) if (year, month) >= began]
        length = 7 if self.frequency == "weekly" else 14
        days_to_year = (date(year, 1, 1) - self.first_start).days
        skipped = max(0, -(-days_to_year // length))
        start = self.first_start + timedelta(days=skipped * length)
        periods = []
        while start.year == year:
            number = len(periods) + 1
            end = start + timedelta(days=length - 1)
            periods.append(self._period(f"{year}-{self.letter}{number:02d}", start, end))
            start += timedelta(days=length)
        return periods

    def period(self, period_id):
        match = PERIOD_ID.fullmatch(period_id or "")
        if match and match.group(2) == self.letter:
            for period in self.periods_in_year(int(match.group(1))):
                if period.id == period_id:
                    return period
        raise PayrollError(f"not a period id: {period_id}")

    def period_containing(self, day):
        for year in (day.year, day.year - 1):
            for period in self.periods_in_year(year):
                if period.contains(day):
                    return period
        raise PayrollError(f"{day.isoformat()} is before the first pay period")

    def previous(self, period):
        """The period just before `period`, or None for the first one."""
        if period.start <= self.first_start:
            return None
        return self.period_containing(period.start - timedelta(days=1))

    def _month(self, year, month):
        last_day = calendar.monthrange(year, month)[1]
        return self._period(f"{year}-M{month:02d}", date(year, month, 1), date(year, month, last_day))

    def _period(self, period_id, start, end):
        return PayPeriod(period_id, start, end, end + timedelta(days=self.pay_delay_days))
