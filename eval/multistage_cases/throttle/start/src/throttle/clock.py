"""Clocks the limiters read time from.

Limiters never look at the system clock themselves: they call ``now()`` on the
clock they were given, which returns seconds as a float. ManualClock is the
clock for simulations and tests.
"""


class ManualClock:
    """A clock that only moves when told to."""

    def __init__(self, start=0.0):
        self._now = float(start)

    def now(self):
        return self._now

    def advance(self, seconds):
        if seconds < 0:
            raise ValueError('clock cannot go backwards')
        self._now += seconds
        return self._now

    def set(self, when):
        """Jump to an absolute time, which may not be earlier than now."""
        return self.advance(when - self._now)

    def __repr__(self):
        return f'ManualClock({self._now:g})'
