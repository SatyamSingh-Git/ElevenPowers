"""Window limiters: a fixed window that resets on period boundaries, and an exact sliding log."""
from collections import deque

from .base import Limiter


class FixedWindow(Limiter):
    """At most ``limit`` units per window; windows start at multiples of ``period``."""

    kind = 'fixed'

    def __init__(self, limit, period, clock):
        super().__init__(limit, clock)
        if period <= 0:
            raise ValueError(f'period must be positive: {period}')
        self.period = period
        self._start = None
        self._used = 0

    def _roll(self):
        now = self._clock.now()
        start = now - now % self.period
        if start != self._start:
            self._start, self._used = start, 0
        return now

    def _take(self, cost, consume):
        now = self._roll()
        left = self.limit - self._used
        if cost <= left:
            if consume:
                self._used += cost
            return self._decision(True, self.limit - self._used, 0)
        return self._decision(False, left, self._start + self.period - now)

    def state(self):
        now = self._roll()
        return {
            'kind': self.kind,
            'limit': self.limit,
            'remaining': self.limit - self._used,
            'reset_in': self._start + self.period - now if self._used else 0.0,
        }


class SlidingWindow(Limiter):
    """At most ``limit`` units in any span of ``period`` seconds.

    Keeps one timestamp per unit spent, so memory grows with the limit.
    """

    kind = 'sliding'

    def __init__(self, limit, period, clock):
        super().__init__(limit, clock)
        if period <= 0:
            raise ValueError(f'period must be positive: {period}')
        self.period = period
        self._hits = deque()

    def _expire(self):
        now = self._clock.now()
        while self._hits and self._hits[0] <= now - self.period:
            self._hits.popleft()
        return now

    def _take(self, cost, consume):
        now = self._expire()
        left = self.limit - len(self._hits)
        if cost <= left:
            if consume:
                self._hits.extend([now] * cost)
            return self._decision(True, self.limit - len(self._hits), 0)
        # The hit fits once the oldest (cost - left) units have aged out.
        freed_by = self._hits[cost - left - 1]
        return self._decision(False, left, freed_by + self.period - now)

    def state(self):
        now = self._expire()
        return {
            'kind': self.kind,
            'limit': self.limit,
            'remaining': self.limit - len(self._hits),
            'reset_in': self._hits[-1] + self.period - now if self._hits else 0.0,
        }
