"""Offset index: one fixed-size entry per record, mapping offset to file position.

    offset    u64
    position  u32   byte position of the record in its segment file
"""
from bisect import bisect_right
from pathlib import Path
import struct

ENTRY = struct.Struct('>QI')


class IndexWriter:
    def __init__(self, path):
        self.path = Path(path)
        self._file = open(self.path, 'ab')

    def add(self, offset, position):
        self._file.write(ENTRY.pack(offset, position))
        self._file.flush()

    def close(self):
        self._file.close()


def read_entries(path):
    """The (offset, position) pairs in an index file, oldest first."""
    path = Path(path)
    data = path.read_bytes() if path.exists() else b''
    # A crash can leave half an entry at the end; it describes nothing yet.
    usable = len(data) - len(data) % ENTRY.size
    return [ENTRY.unpack_from(data, at) for at in range(0, usable, ENTRY.size)]


def lookup(entries, offset):
    """Position of the last entry at or before `offset`, or None if there is none."""
    at = bisect_right(entries, offset, key=lambda entry: entry[0])
    return entries[at - 1][1] if at else None


def rebuild(segment, found):
    """Rewrite a segment's index from the (position, record) pairs a scan found."""
    segment.index_path.write_bytes(b''.join(ENTRY.pack(record.offset, position) for position, record in found))
