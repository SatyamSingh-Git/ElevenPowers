"""Throttle: one limiter per key, each built from the policy its key matches."""
from collections import OrderedDict
import functools

from .errors import RateLimitExceeded
from .policy import Policy, build_limiter, format_policy, parse_policy


def _matches(pattern, key):
    if pattern.endswith('*'):
        return key.startswith(pattern[:-1])
    return key == pattern


def _policy(value):
    return value if isinstance(value, Policy) else parse_policy(value)


class Throttle:
    """Per-key rate limiting.

    Policies are attached to patterns: an exact key, or a prefix ending in
    ``*``. The longest matching pattern wins and keys matching none get the
    default. At most ``max_keys`` limiters are kept; past that the least
    recently used key is forgotten.
    """

    def __init__(self, clock, default='60/minute', max_keys=1000):
        if max_keys < 1:
            raise ValueError(f'max_keys must be at least 1: {max_keys}')
        self.clock = clock
        self.default = _policy(default)
        self.max_keys = max_keys
        self._patterns = {}
        self._limiters = OrderedDict()

    def set_policy(self, pattern, policy):
        self._patterns[pattern] = _policy(policy)
        self._forget_changed()

    def remove_policy(self, pattern):
        del self._patterns[pattern]
        self._forget_changed()

    def _forget_changed(self):
        # Keys whose policy just changed start over under the new one.
        for key, (current, _) in list(self._limiters.items()):
            if self.policy_for(key) != current:
                del self._limiters[key]

    def policies(self):
        """(pattern, Policy) pairs, in the order they were set."""
        return list(self._patterns.items())

    def policy_for(self, key):
        matching = [pattern for pattern in self._patterns if _matches(pattern, key)]
        if not matching:
            return self.default
        return self._patterns[max(matching, key=len)]

    def _limiter(self, key):
        if key in self._limiters:
            self._limiters.move_to_end(key)
            return self._limiters[key][1]
        if len(self._limiters) >= self.max_keys:
            self._limiters.popitem(last=False)
        policy = self.policy_for(key)
        limiter = build_limiter(policy, self.clock)
        self._limiters[key] = (policy, limiter)
        return limiter

    def hit(self, key, cost=1):
        return self._limiter(key).hit(cost)

    def check(self, key, cost=1):
        """Like hit, but raises RateLimitExceeded instead of returning a denial."""
        decision = self.hit(key, cost)
        if not decision.allowed:
            raise RateLimitExceeded(key, decision.retry_after)
        return decision

    def remaining(self, key):
        """Units ``key`` could spend right now; a key never hit has its full capacity."""
        if key in self._limiters:
            return self._limiters[key][1].peek().remaining
        return self.policy_for(key).capacity

    def reset(self, key):
        self._limiters.pop(key, None)

    def keys(self):
        return list(self._limiters)

    def __len__(self):
        return len(self._limiters)

    def __contains__(self, key):
        return key in self._limiters

    def snapshot(self):
        """One dict per tracked key, sorted by key: the limiter's state plus key, policy and retry_after."""
        entries = []
        for key, (policy, limiter) in sorted(self._limiters.items()):
            entries.append({
                'key': key,
                'policy': format_policy(policy),
                **limiter.state(),
                'retry_after': limiter.peek().retry_after,
            })
        return entries

    def limited(self, key, cost=1):
        """Decorator: every call to the wrapped function first checks ``key``."""
        def decorate(function):
            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                self.check(key, cost)
                return function(*args, **kwargs)
            return wrapper
        return decorate
