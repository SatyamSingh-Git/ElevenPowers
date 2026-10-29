"""The desk reads the time from a clock object, never from the system.

The command line builds one from `--now`; the services take it as an argument,
so a day at the desk can be replayed exactly.
"""


class FixedClock:
    """A clock that reads whatever time it was last set to."""

    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now

    def set(self, now):
        self._now = now
