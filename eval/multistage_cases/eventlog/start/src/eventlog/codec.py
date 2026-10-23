"""The record encoding shared by every segment.

A record on disk is a length prefix followed by the body it counts:

    length     u32   bytes that follow the length field
    crc        u32   CRC-32C of everything after this field
    offset     u64
    timestamp  u64   milliseconds
    flags      u8    bit 0 marks a tombstone
    key_length u16
    key, value       the value takes whatever the length leaves

All integers are big-endian.
"""
from dataclasses import dataclass
import struct

from ._generated import CRC32C_TABLE
from .errors import CorruptRecord

TOMBSTONE = 0x01
LENGTH = struct.Struct('>I')
CHECKSUM = struct.Struct('>I')
FIELDS = struct.Struct('>QQBH')
BODY_OVERHEAD = CHECKSUM.size + FIELDS.size


@dataclass(frozen=True)
class Record:
    offset: int
    timestamp: int
    key: bytes
    value: bytes
    tombstone: bool = False


def crc32c(data, crc=0):
    crc ^= 0xFFFFFFFF
    for byte in data:
        crc = CRC32C_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def encode_record(record):
    flags = TOMBSTONE if record.tombstone else 0
    fields = FIELDS.pack(record.offset, record.timestamp, flags, len(record.key))
    checked = fields + record.key + record.value
    body = CHECKSUM.pack(crc32c(checked)) + checked
    return LENGTH.pack(len(body)) + body


def decode_record(buf, position, segment='<buffer>'):
    """Decode the record that starts at `position`; return it and the position after it."""
    if position + LENGTH.size > len(buf):
        raise CorruptRecord(segment, position)
    (length,) = LENGTH.unpack_from(buf, position)
    start = position + LENGTH.size
    end = start + length
    if length < BODY_OVERHEAD or end > len(buf):
        raise CorruptRecord(segment, position)
    (crc,) = CHECKSUM.unpack_from(buf, start)
    if crc32c(memoryview(buf)[start + CHECKSUM.size:end]) != crc:
        raise CorruptRecord(segment, position)
    offset, timestamp, flags, key_length = FIELDS.unpack_from(buf, start + CHECKSUM.size)
    key_start = start + BODY_OVERHEAD
    if key_start + key_length > end:
        raise CorruptRecord(segment, position)
    key = bytes(buf[key_start:key_start + key_length])
    value = bytes(buf[key_start + key_length:end])
    return Record(offset, timestamp, key, value, bool(flags & TOMBSTONE)), end
