"""Token bucket: bursts up to a capacity, refilled at a steady rate."""
from .base import Limiter


class TokenBucket(Limiter):
    kind = 'bucket'

    def __init__(self, capacity, refill_per_second, clock):
        super().__init__(capacity, clock)
        if refill_per_second <= 0:
            raise ValueError(f'refill_per_second must be positive: {refill_per_second}')
        self.rate = refill_per_second
        self._tokens = float(capacity)
        self._updated = clock.now()

    @property
    def capacity(self):
        return self.limit

    def _refill(self):
        now = self._clock.now()
        self._tokens = min(self.limit, self._tokens + (now - self._updated) * self.rate)
        self._updated = now

    def _take(self, cost, consume):
        self._refill()
        if self._tokens >= cost:
            if consume:
                self._tokens -= cost
            return self._decision(True, int(self._tokens), 0)
        return self._decision(False, int(self._tokens), (cost - self._tokens) / self.rate)

    def state(self):
        self._refill()
        return {
            'kind': self.kind,
            'limit': self.limit,
            'remaining': int(self._tokens),
            'reset_in': (self.limit - self._tokens) / self.rate,
        }
