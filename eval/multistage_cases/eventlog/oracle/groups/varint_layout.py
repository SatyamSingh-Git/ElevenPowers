"""Format version 2 on disk: records carry an unsigned LEB128 varint length prefix."""
import struct

from eventlog import Log, LogConfig, ManualClock


def crc32c(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x82F63B78 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def read_varint(data, position):
    value = shift = 0
    while True:
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, position
        shift += 7


def parse(data):
    """Header fields, then (offset, timestamp, flags, key, value, prefix bytes) for every record."""
    magic, version, base = struct.unpack_from('>4sBQ', data)
    position, records = 13, []
    while position < len(data):
        length, start = read_varint(data, position)
        body = data[start:start + length]
        assert len(body) == length
        (crc,) = struct.unpack_from('>I', body)
        assert crc == crc32c(body[4:])
        offset, timestamp, flags, key_length = struct.unpack_from('>QQBH', body, 4)
        key = body[23:23 + key_length]
        records.append((offset, timestamp, flags, key, body[23 + key_length:], start - position))
        position = start + length
    return (magic, version, base), records


def test_header_is_version_2(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    (header, _), = [parse(path.read_bytes()) for path in segment_files(tmp_path)]
    assert header == (b'EVLG', 2, 0)


def test_short_and_long_length_prefixes(tmp_path):
    values = [b'', b'x' * 10, b'y' * 101, b'z' * 102, b'w' * 300, b'q' * 20_000]
    with Log.open(tmp_path, clock=ManualClock(77)) as log:
        for value in values:
            log.append('key', value)
        log.delete('key', timestamp=99)
    (_, records), = [parse(path.read_bytes()) for path in segment_files(tmp_path)]
    assert [r[0] for r in records] == list(range(len(values) + 1))
    assert [r[4] for r in records] == values + [b'']
    assert all(r[3] == b'key' for r in records)
    assert [r[1] for r in records] == [77] * len(values) + [99]
    assert [r[2] & 1 for r in records] == [0] * len(values) + [1]
    # The body is 23 bytes plus key and value: a 127-byte body fits one varint byte, 128 needs two.
    assert [r[5] for r in records] == [1, 1, 1, 2, 2, 3, 1]


def test_file_size_is_exact(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('ab', 'cde')
        log.append('ab', 'f' * 200)
    (path,) = segment_files(tmp_path)
    assert path.stat().st_size == 13 + (1 + 23 + 5) + (2 + 23 + 202)


def test_every_segment_is_well_formed(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=200)) as log:
        for n in range(30):
            log.append(f'key{n}', 'v' * n)
    seen = []
    for path in segment_files(tmp_path):
        (magic, version, base), records = parse(path.read_bytes())
        assert (magic, version) == (b'EVLG', 2)
        if records:
            assert records[0][0] == base
        seen += [r[0] for r in records]
    assert seen == list(range(30))
