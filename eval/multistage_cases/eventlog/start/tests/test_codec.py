import struct

import pytest

from eventlog.codec import Record, crc32c, decode_record, encode_record
from eventlog.errors import CorruptRecord


def test_crc32c_matches_the_published_check_value():
    assert crc32c(b'123456789') == 0xE3069283


def test_round_trip():
    record = Record(7, 1_700_000_000_000, b'user-1', b'{"name": "Ada"}')
    data = encode_record(record)
    assert decode_record(data, 0) == (record, len(data))


def test_tombstone_round_trip():
    record = Record(3, 5, b'user-1', b'', tombstone=True)
    assert decode_record(encode_record(record), 0)[0].tombstone


def test_layout():
    data = encode_record(Record(258, 9, b'ab', b'xyz'))
    (length,) = struct.unpack_from('>I', data)
    assert length == len(data) - 4 == 23 + 2 + 3
    assert struct.unpack_from('>QQBH', data, 8) == (258, 9, 0, 2)
    assert data[-5:] == b'abxyz'


def test_decode_from_the_middle_of_a_buffer():
    first, second = Record(0, 0, b'a', b'1'), Record(1, 0, b'b', b'2')
    data = encode_record(first) + encode_record(second)
    record, end = decode_record(data, len(encode_record(first)))
    assert record == second and end == len(data)


def test_flipped_byte_is_corruption():
    data = bytearray(encode_record(Record(0, 0, b'key', b'value')))
    data[-1] ^= 0xFF
    with pytest.raises(CorruptRecord, match='corrupt record at position 0 in seg'):
        decode_record(bytes(data), 0, 'seg')


def test_short_buffer_is_corruption():
    data = encode_record(Record(0, 0, b'key', b'value'))
    with pytest.raises(CorruptRecord):
        decode_record(data[:-1], 0)
