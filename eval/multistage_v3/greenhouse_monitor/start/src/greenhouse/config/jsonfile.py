"""Reading the JSON configuration files with errors that name the file."""
import json
from pathlib import Path

from ..core.errors import ConfigError


def read_json(path, expected=dict):
    """Parse a JSON file whose top level must be an ``expected`` value."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path.name}: {error.msg} at line {error.lineno}") from None
    if not isinstance(data, expected):
        raise ConfigError(f"{path.name}: expected a JSON {expected.__name__}")
    return data


def number(value, what):
    """A JSON number as a float; true and false are not numbers here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{what} must be a number")
    return float(value)
