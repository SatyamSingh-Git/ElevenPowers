from pathlib import Path

from . import index, reader
from .clock import ManualClock
from .codec import Record, encode_record
from .config import LogConfig
from .errors import EmptyKey, KeyTooLarge, LogClosed, ValueTooLarge
from .index import IndexWriter
from .segment import SUFFIX, Segment


def _as_bytes(data):
    return data.encode('utf-8') if isinstance(data, str) else bytes(data)


class Log:
    """An append-only log of keyed events, kept as a run of segment files.

    Only the newest segment is written to. Once it reaches
    `config.segment_bytes` it is sealed and a new one starts at the next
    offset. Use `Log.open` rather than constructing one directly.
    """

    def __init__(self, directory, segments, config, clock):
        self.directory = Path(directory)
        self.config = config
        self.clock = clock
        self._segments = segments
        self._next_offset = segments[-1].base_offset
        self._index = None
        self._closed = False

    @classmethod
    def open(cls, directory, config=None, clock=None):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        segments = [Segment.open(path) for path in directory.glob(f'*{SUFFIX}')]
        segments.sort(key=lambda segment: segment.base_offset)
        if not segments:
            segments = [Segment.create(directory, 0)]
        log = cls(directory, segments, config or LogConfig(), clock or ManualClock())
        log._recover()
        return log

    def _recover(self):
        active = self._segments[-1]
        found, end = active.scan()
        if end < active.size:
            active.truncate(end)
        index.rebuild(active, found)
        self._next_offset = found[-1][1].offset + 1 if found else active.base_offset
        self._index = IndexWriter(active.index_path)

    @property
    def segments(self):
        return tuple(self._segments)

    @property
    def sealed_segments(self):
        return tuple(self._segments[:-1])

    @property
    def first_offset(self):
        return self._segments[0].base_offset

    @property
    def next_offset(self):
        return self._next_offset

    def append(self, key, value, *, timestamp=None):
        """Append an event and return its offset."""
        return self._write(_as_bytes(key), _as_bytes(value), False, timestamp)

    def delete(self, key, *, timestamp=None):
        """Append a tombstone for `key`; compaction later drops the key entirely."""
        return self._write(_as_bytes(key), b'', True, timestamp)

    def _write(self, key, value, tombstone, timestamp):
        if self._closed:
            raise LogClosed()
        if not key:
            raise EmptyKey()
        if len(key) > self.config.max_key_bytes:
            raise KeyTooLarge(len(key), self.config.max_key_bytes)
        if len(value) > self.config.max_value_bytes:
            raise ValueTooLarge(len(value), self.config.max_value_bytes)
        record = Record(self._next_offset, self.clock() if timestamp is None else timestamp,
                        key, value, tombstone)
        active = self._segments[-1]
        position = active.append(encode_record(record))
        self._index.add(record.offset, position)
        self._next_offset += 1
        if active.size >= self.config.segment_bytes:
            self._roll()
        return record.offset

    def _roll(self):
        self._segments[-1].close()
        self._index.close()
        segment = Segment.create(self.directory, self._next_offset)
        self._segments.append(segment)
        self._index = IndexWriter(segment.index_path)

    def _replace_sealed(self, sealed):
        """Swap in rewritten sealed segments; compaction is the only caller."""
        self._segments[:-1] = sealed

    def replay(self, from_offset=None):
        return reader.replay(self, from_offset)

    def read(self, offset):
        """The record at `offset`, or None if compaction removed it."""
        for record in reader.replay(self, offset):
            return record if record.offset == offset else None
        return None

    def close(self):
        if self._closed:
            return
        self._segments[-1].close()
        self._index.close()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
