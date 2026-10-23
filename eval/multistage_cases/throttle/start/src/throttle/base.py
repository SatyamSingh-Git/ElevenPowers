"""What every limiter shares: the Decision it returns and the hit/peek protocol."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    """The outcome of one hit.

    ``remaining`` is what is left after this hit; ``retry_after`` is how long
    to wait, in seconds, before the same hit would be allowed (0 when allowed).
    """

    allowed: bool
    remaining: int
    retry_after: float
    limit: int


class Limiter:
    """Base class. Subclasses implement ``_take`` and ``state``."""

    kind = None

    def __init__(self, limit, clock):
        if limit <= 0:
            raise ValueError(f'limit must be positive: {limit}')
        self.limit = limit
        self._clock = clock

    def hit(self, cost=1):
        """Spend ``cost`` units if they are available."""
        if cost < 1:
            raise ValueError(f'cost must be at least 1: {cost}')
        return self._take(cost, consume=True)

    def peek(self):
        """What a hit of 1 would be told now, without spending anything."""
        return self._take(1, consume=False)

    def _decision(self, allowed, remaining, wait):
        return Decision(allowed, remaining, wait if not allowed else 0.0, self.limit)

    def _take(self, cost, consume):
        raise NotImplementedError

    def state(self):
        """A plain dict describing the limiter: kind, limit, remaining, reset_in."""
        raise NotImplementedError

    def __repr__(self):
        return f'{type(self).__name__}(limit={self.limit})'
