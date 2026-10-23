"""Reading and writing short durations such as ``30s``, ``5m`` or ``250ms``."""
import re

from ._generated import UNIT_SECONDS

_DURATION = re.compile(r'^(\d+(?:\.\d+)?)?\s*([a-z]*)$')


def parse_duration(text):
    """Seconds in ``text``: a number, a unit, or both (``90``, ``minute``, ``1.5h``)."""
    match = _DURATION.match(text.strip().lower())
    if not match or not any(match.groups()):
        raise ValueError(f'invalid duration: {text}')
    amount, unit = match.groups()
    if unit and unit not in UNIT_SECONDS:
        raise ValueError(f'unknown unit: {unit}')
    seconds = float(amount or 1) * UNIT_SECONDS.get(unit, 1)
    if seconds <= 0:
        raise ValueError(f'invalid duration: {text}')
    return seconds


def format_duration(seconds):
    """A short human form: ``250ms`` below a second, ``1.5s`` below a minute, then ``1h2m3s``."""
    millis = round(seconds * 1000)
    if millis < 1000:
        return f'{millis}ms'
    if millis < 60_000:
        return f'{millis / 1000:g}s'
    hours, rest = divmod(round(millis / 1000), 3600)
    minutes, secs = divmod(rest, 60)
    return ''.join(f'{amount}{unit}' for amount, unit in ((hours, 'h'), (minutes, 'm'), (secs, 's')) if amount)
