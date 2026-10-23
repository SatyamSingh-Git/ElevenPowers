class EventLogError(Exception):
    """Base class for every error this package raises."""


class ConfigError(EventLogError, ValueError):
    pass


class LogClosed(EventLogError):
    def __init__(self):
        super().__init__('log is closed')


class NotASegment(EventLogError):
    def __init__(self, segment):
        super().__init__(f'{segment}: not an event log segment')
        self.segment = segment


class UnsupportedFormat(EventLogError):
    def __init__(self, segment, version):
        super().__init__(f'{segment}: unsupported format version {version}')
        self.segment = segment
        self.version = version


class CorruptRecord(EventLogError):
    def __init__(self, segment, position):
        super().__init__(f'corrupt record at position {position} in {segment}')
        self.segment = segment
        self.position = position


class OffsetOutOfRange(EventLogError, IndexError):
    def __init__(self, offset, first, next_offset):
        super().__init__(f'offset {offset} is outside {first}..{next_offset}')
        self.offset = offset


class KeyTooLarge(EventLogError, ValueError):
    def __init__(self, size, limit):
        super().__init__(f'key of {size} bytes exceeds max_key_bytes {limit}')


class ValueTooLarge(EventLogError, ValueError):
    def __init__(self, size, limit):
        super().__init__(f'value of {size} bytes exceeds max_value_bytes {limit}')


class EmptyKey(EventLogError, ValueError):
    def __init__(self):
        super().__init__('key must not be empty')
