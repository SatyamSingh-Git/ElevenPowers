"""Views of the effective configuration.

The INI view can be loaded back as a configuration file and gives the same
values, apart from secrets, which every view masks unless asked not to.
"""
import json

from ._generated import DURATION_UNITS, SIZE_UNITS

MASK = '***'
FORMATS = ('ini', 'json', 'sources')


def _with_unit(amount, units):
    """`amount` in the largest unit that divides it exactly."""
    if amount == 0:
        return '0' + min(units, key=units.get)
    for unit, factor in sorted(units.items(), key=lambda item: item[1], reverse=True):
        if amount % factor == 0:
            return f'{amount // factor}{unit}'


def format_value(option, value):
    """The value written the way a configuration file would write it."""
    if value is None:
        return ''
    if option.type == 'bool':
        return 'true' if value else 'false'
    if option.type == 'list':
        return ', '.join(value)
    if option.type == 'duration':
        return _with_unit(round(value * 1000), DURATION_UNITS)
    if option.type == 'size':
        return _with_unit(value, SIZE_UNITS)
    if option.type == 'float':
        return repr(value)
    return str(value)


def shown(option, value, reveal=False):
    if option.secret and value is not None and not reveal:
        return MASK
    return format_value(option, value)


def render_ini(config, reveal=False):
    lines = []
    for section, options in config.schema.sections().items():
        if lines:
            lines.append('')
        lines.append(f'[{section}]')
        for option in options:
            value = config[option.key]
            if value is None:
                lines.append(f'; {option.name} =')
            else:
                lines.append(f'{option.name} = {shown(option, value, reveal)}')
    return '\n'.join(lines) + '\n'


def render_json(config, reveal=False):
    data = {}
    for option in config.schema:
        value = config[option.key]
        data[option.key] = MASK if option.secret and value is not None and not reveal else value
    return json.dumps(data, indent=2) + '\n'


def render_sources(config, reveal=False):
    rows = []
    for option in config.schema:
        value = config[option.key]
        text = '(unset)' if value is None else shown(option, value, reveal)
        rows.append((f'{option.key} = {text}', config.source(option.key)))
    width = max(len(left) for left, _ in rows)
    return ''.join(f'{left.ljust(width)}  ({source})\n' for left, source in rows)


RENDERERS = {'ini': render_ini, 'json': render_json, 'sources': render_sources}


def explain(config, option):
    """Everything about one option: its value, where it came from and how to set it."""
    value = config[option.key]
    lines = [
        f"{option.key} = {'(unset)' if value is None else shown(option, value)}",
        f'  type: {option.type}',
        f"  default: {'(unset)' if option.default is None else option.default}",
        f'  set by: {config.source(option.key)}',
        f"  env: {config.env_prefix}{option.key.upper().replace('.', '__')}",
    ]
    aliases = config.schema.aliases_of(option.key)
    if aliases:
        lines.append(f"  aliases: {', '.join(aliases)}")
    if option.choices:
        lines.append(f"  choices: {', '.join(option.choices)}")
    if option.minimum is not None or option.maximum is not None:
        lines.append(f"  range: {option.minimum or ''}..{option.maximum or ''}")
    if option.secret:
        lines.append('  secret: yes')
    if option.help:
        lines.append(f'  {option.help}')
    return '\n'.join(lines) + '\n'
