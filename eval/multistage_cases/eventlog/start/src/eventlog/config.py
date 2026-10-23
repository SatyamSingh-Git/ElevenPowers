from dataclasses import dataclass

from .errors import ConfigError

MIN_SEGMENT_BYTES = 64
MAX_KEY_BYTES = 65_535


@dataclass(frozen=True)
class LogConfig:
    segment_bytes: int = 1_048_576
    max_key_bytes: int = 1024
    max_value_bytes: int = 65_536

    def __post_init__(self):
        if self.segment_bytes < MIN_SEGMENT_BYTES:
            raise ConfigError(f'segment_bytes must be at least {MIN_SEGMENT_BYTES}')
        if not 1 <= self.max_key_bytes <= MAX_KEY_BYTES:
            raise ConfigError(f'max_key_bytes must be between 1 and {MAX_KEY_BYTES}')
        if self.max_value_bytes < 0:
            raise ConfigError('max_value_bytes must not be negative')
