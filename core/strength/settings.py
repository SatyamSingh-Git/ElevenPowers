"""Project-owned limits. Invalid settings are explicit, never guessed."""
from dataclasses import dataclass
import math
from .model import relative


@dataclass(frozen=True)
class Settings:
    enabled: bool = True
    seconds: float = 60
    max_mutants: int = 8
    test_seconds: float = 15
    max_files: int = 20000
    max_bytes: int = 256 * 1024 * 1024
    dependencies: tuple = ()
    command: str = ''
    python: str = ''
    stryker: str = ''


def settings(raw):
    if not isinstance(raw, dict) or set(raw) - set(Settings.__dataclass_fields__):
        raise ValueError('strength must contain recognized settings')
    if not isinstance(raw.get('dependencies', []), (list, tuple)):
        raise ValueError('dependencies must be relative paths')
    value = Settings(**{**raw, 'dependencies': tuple(raw.get('dependencies', []))})
    if type(value.enabled) is not bool:
        raise ValueError('strength.enabled must be boolean')
    for name, maximum in [('seconds', 480), ('test_seconds', 300)]:
        number = getattr(value, name)
        if type(number) not in (float, int) or not math.isfinite(number) or not 0 < number <= maximum:
            raise ValueError(f'strength.{name} must be finite, positive and at most {maximum}')
    for name, maximum in [('max_mutants', 256), ('max_files', 100000), ('max_bytes', 1024**3)]:
        number = getattr(value, name)
        if type(number) is not int or not 1 <= number <= maximum:
            raise ValueError(f'strength.{name} must be between 1 and {maximum}')
    if not isinstance(raw.get('dependencies', []), (list, tuple)):
        raise ValueError('dependencies must be relative paths')
    for item in value.dependencies:
        relative(item)
    for name in ('command', 'python', 'stryker'):
        if not isinstance(getattr(value, name), str):
            raise ValueError(f'strength.{name} must be a string')
    return value
