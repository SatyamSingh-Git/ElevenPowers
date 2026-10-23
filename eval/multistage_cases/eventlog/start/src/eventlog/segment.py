"""Segment files: a fixed header, then records back to back."""
from pathlib import Path
import struct

from .codec import decode_record
from .errors import NotASegment, UnsupportedFormat

MAGIC = b'EVLG'
VERSION = 1
HEADER = struct.Struct('>4sBQ')
SUFFIX = '.log'
INDEX_SUFFIX = '.idx'


def segment_name(base_offset):
    return f'{base_offset:020d}{SUFFIX}'


def encode_header(base_offset):
    return HEADER.pack(MAGIC, VERSION, base_offset)


def decode_header(data, name):
    if len(data) < HEADER.size:
        raise NotASegment(name)
    magic, version, base_offset = HEADER.unpack_from(data)
    if magic != MAGIC:
        raise NotASegment(name)
    if version != VERSION:
        raise UnsupportedFormat(name, version)
    return base_offset


class Segment:
    def __init__(self, path, base_offset, size):
        self.path = Path(path)
        self.base_offset = base_offset
        self.size = size
        self._file = None

    @classmethod
    def create(cls, directory, base_offset):
        path = Path(directory) / segment_name(base_offset)
        path.write_bytes(encode_header(base_offset))
        path.with_suffix(INDEX_SUFFIX).write_bytes(b'')
        return cls(path, base_offset, HEADER.size)

    @classmethod
    def open(cls, path):
        path = Path(path)
        with open(path, 'rb') as file:
            base_offset = decode_header(file.read(HEADER.size), path.name)
        return cls(path, base_offset, path.stat().st_size)

    @property
    def name(self):
        return self.path.name

    @property
    def index_path(self):
        return self.path.with_suffix(INDEX_SUFFIX)

    def append(self, data):
        """Write encoded records at the end; return the position they start at."""
        if self._file is None:
            self._file = open(self.path, 'ab')
        position = self.size
        self._file.write(data)
        self._file.flush()
        self.size += len(data)
        return position

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def read(self):
        return self.path.read_bytes()

    def records(self, start=None):
        data = self.read()
        position = HEADER.size if start is None else start
        while position < len(data):
            record, position = decode_record(data, position, self.name)
            yield record

    def scan(self):
        """Walk every record, stopping early at a write torn by a crash.

        Returns the (position, record) pairs found and the position where the
        intact data ends. A torn tail is expected after a crash and is left
        for the caller to cut off; a record that is all there but does not
        check out is corruption and raises.
        """
        data = self.read()
        position = HEADER.size
        found = []
        while position < len(data):
            if position + 4 > len(data):
                break
            (length,) = struct.unpack_from('>I', data, position)
            if position + 4 + length > len(data):
                break
            record, end = decode_record(data, position, self.name)
            found.append((position, record))
            position = end
        return found, position

    def truncate(self, size):
        self.close()
        with open(self.path, 'r+b') as file:
            file.truncate(size)
        self.size = size
