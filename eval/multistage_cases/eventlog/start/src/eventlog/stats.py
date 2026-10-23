"""A read-only summary of a log directory.

It reads the segment files directly instead of opening a `Log`, so it never
repairs or truncates anything and is safe to run beside a live writer.
"""
from dataclasses import dataclass
from pathlib import Path
import re

from .codec import decode_record
from .errors import CorruptRecord
from .segment import HEADER, decode_header

# Matches only finished segment files, not the staging copies compaction writes.
SEGMENT_FILE = re.compile(r'^\d{20}\.log$')


@dataclass(frozen=True)
class LogStats:
    segments: int
    records: int
    keys: int
    tombstones: int
    bytes: int
    first_offset: int
    next_offset: int


def stats(directory):
    paths = sorted(path for path in Path(directory).iterdir() if SEGMENT_FILE.match(path.name))
    records = tombstones = size = 0
    first_offset = next_offset = 0
    live = {}
    for number, path in enumerate(paths):
        data = path.read_bytes()
        base_offset = decode_header(data, path.name)
        if number == 0:
            first_offset = base_offset
        next_offset = max(next_offset, base_offset)
        size += len(data)
        position = HEADER.size
        while position < len(data):
            try:
                record, position = decode_record(data, position, path.name)
            except CorruptRecord:
                # The writer may be part-way through a record at the very end.
                if number == len(paths) - 1:
                    break
                raise
            records += 1
            tombstones += record.tombstone
            live[record.key] = not record.tombstone
            next_offset = record.offset + 1
    return LogStats(segments=len(paths), records=records, keys=sum(live.values()), tombstones=tombstones,
                    bytes=size, first_offset=first_offset, next_offset=next_offset)


def format_stats(summary):
    return '\n'.join([
        f'segments: {summary.segments}',
        f'records: {summary.records}',
        f'keys: {summary.keys}',
        f'tombstones: {summary.tombstones}',
        f'bytes: {summary.bytes}',
        f'offsets: {summary.first_offset}..{summary.next_offset}',
    ])
