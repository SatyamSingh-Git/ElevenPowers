"""Exceptions raised on purpose by throttle."""
from .durations import format_duration


class ThrottleError(Exception):
    """Base class for every error this library raises deliberately."""


class PolicyError(ThrottleError, ValueError):
    """A policy string or Policy value that cannot be used."""


class ConfigError(ThrottleError, ValueError):
    def __init__(self, line, problem):
        super().__init__(f'config line {line}: {problem}')
        self.line = line
        self.problem = problem


class RateLimitExceeded(ThrottleError):
    """Raised by Throttle.check when a hit is denied."""

    def __init__(self, key, retry_after):
        super().__init__(f'rate limit exceeded for {key}: retry in {format_duration(retry_after)}')
        self.key = key
        self.retry_after = retry_after
