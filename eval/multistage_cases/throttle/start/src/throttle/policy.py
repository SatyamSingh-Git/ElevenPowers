"""Policies: how much, over how long, and with which algorithm.

A policy is written ``<limit>/<period>`` followed by optional ``; name=value``
options, for example ``100/minute``, ``5/30s; algorithm=sliding`` or
``10/second; algorithm=bucket; burst=50``.
"""
from dataclasses import dataclass
import re

from ._generated import CANONICAL_UNITS, UNIT_SECONDS
from .bucket import TokenBucket
from .durations import parse_duration
from .errors import PolicyError
from .window import FixedWindow, SlidingWindow

ALGORITHMS = ('fixed', 'sliding', 'bucket')
DEFAULT_ALGORITHM = 'fixed'

_HEAD = re.compile(r'^\s*(\d+)\s*/\s*(\S.*?)\s*$')


@dataclass(frozen=True)
class Policy:
    limit: int
    period: float
    algorithm: str = DEFAULT_ALGORITHM
    burst: int | None = None

    def __post_init__(self):
        if self.limit <= 0:
            raise PolicyError(f'limit must be positive: {self.limit}')
        if self.period <= 0:
            raise PolicyError(f'period must be positive: {self.period}')
        if self.algorithm not in ALGORITHMS:
            raise PolicyError(f'unknown algorithm: {self.algorithm}')
        if self.burst is not None and self.algorithm != 'bucket':
            raise PolicyError('burst only applies to the bucket algorithm')

    @property
    def capacity(self):
        """Units available at once: the burst for a bucket, otherwise the limit."""
        return self.burst if self.burst is not None else self.limit

    def __str__(self):
        return format_policy(self)


def parse_policy(text):
    head, *options = text.split(';')
    match = _HEAD.match(head)
    if not match:
        raise PolicyError(f'invalid policy: {text.strip()}')
    try:
        period = parse_duration(match[2])
    except ValueError as exc:
        raise PolicyError(str(exc)) from None
    fields = {}
    for option in options:
        name, equals, value = (part.strip() for part in option.partition('='))
        if not equals or not name:
            raise PolicyError(f'invalid option: {option.strip()}')
        if name == 'algorithm':
            fields['algorithm'] = value
        elif name == 'burst':
            if not value.isdigit() or int(value) == 0:
                raise PolicyError(f'burst must be a positive integer: {value}')
            fields['burst'] = int(value)
        else:
            raise PolicyError(f'unknown option: {name}')
    return Policy(int(match[1]), period, **fields)


def format_policy(policy):
    """The policy as text that parse_policy reads back to an equal Policy."""
    text = f'{policy.limit}/{_period_text(policy.period)}'
    if policy.algorithm != DEFAULT_ALGORITHM:
        text += f'; algorithm={policy.algorithm}'
    if policy.burst is not None:
        text += f'; burst={policy.burst}'
    return text


def _period_text(seconds):
    for name, short in CANONICAL_UNITS:
        size = UNIT_SECONDS[name]
        if seconds == size:
            return name
        if seconds % size == 0:
            return f'{int(seconds // size)}{short}'
    return f'{round(seconds * 1000)}ms'


def build_limiter(policy, clock):
    """A fresh limiter enforcing ``policy`` against ``clock``."""
    if policy.algorithm == 'bucket':
        return TokenBucket(policy.capacity, policy.limit / policy.period, clock)
    if policy.algorithm == 'sliding':
        return SlidingWindow(policy.limit, policy.period, clock)
    return FixedWindow(policy.limit, policy.period, clock)
