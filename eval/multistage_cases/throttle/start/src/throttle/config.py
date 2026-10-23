"""Building a Throttle from a small text file.

One setting per line, ``#`` starts a comment::

    default = 100/minute
    max_keys = 5000
    limit login:* = 5/minute; algorithm=sliding
    limit upload:* = 20/hour; algorithm=bucket; burst=5
"""
from .errors import ConfigError, PolicyError
from .policy import format_policy, parse_policy
from .registry import Throttle


def parse_config(text):
    """The settings in ``text`` as (throttle keyword arguments, [(pattern, Policy)])."""
    settings, limits = {}, []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        name, equals, value = (part.strip() for part in line.partition('='))
        if not equals or not name or not value:
            raise ConfigError(number, 'expected name = value')
        try:
            if name == 'default':
                settings['default'] = parse_policy(value)
            elif name == 'max_keys':
                if not value.isdigit():
                    raise ConfigError(number, f'max_keys must be an integer: {value}')
                settings['max_keys'] = int(value)
            elif name.startswith('limit '):
                limits.append((name[len('limit '):].strip(), parse_policy(value)))
            else:
                raise ConfigError(number, f'unknown setting: {name}')
        except PolicyError as exc:
            raise ConfigError(number, str(exc)) from None
    return settings, limits


def load_config(text, clock):
    settings, limits = parse_config(text)
    throttle = Throttle(clock, **settings)
    for pattern, policy in limits:
        throttle.set_policy(pattern, policy)
    return throttle


def dump_config(throttle):
    """Config text that load_config turns back into an equivalent Throttle (without its keys)."""
    lines = [f'default = {format_policy(throttle.default)}', f'max_keys = {throttle.max_keys}']
    for pattern, policy in throttle.policies():
        lines.append(f'limit {pattern} = {format_policy(policy)}')
    return '\n'.join(lines) + '\n'
