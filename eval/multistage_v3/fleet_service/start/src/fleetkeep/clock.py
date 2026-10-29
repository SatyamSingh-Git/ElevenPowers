"""Where "today" comes from, so commands can be run as of any date."""
from datetime import date


class SystemClock:
    def today(self):
        return date.today()


class FixedClock:
    def __init__(self, day):
        self.day = day

    def today(self):
        return self.day
