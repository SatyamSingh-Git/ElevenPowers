"""Format version 3: a record stores its offset as a u32 delta from its segment's base offset."""
import struct

from eventlog import Log, LogConfig, compact, stats


def crc32c(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x82F63B78 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def varint(value):
    out = bytearray()
    while value >= 0x80:
        out.append(value & 0x7F | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_varint(data, position):
    value = shift = 0
    while True:
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, position
        shift += 7


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def parse(data):
    magic, version, base = struct.unpack_from('>4sBQ', data)
    position, records = 13, []
    while position < len(data):
        length, start = read_varint(data, position)
        body = data[start:start + length]
        assert len(body) == length
        (crc,) = struct.unpack_from('>I', body)
        assert crc == crc32c(body[4:])
        delta, timestamp, flags, key_length = struct.unpack_from('>IQBH', body, 4)
        key = body[19:19 + key_length]
        records.append((delta, timestamp, flags, key, body[19 + key_length:]))
        position = start + length
    return (magic, version, base), records


def encode(delta, timestamp, key, value, flags=0):
    checked = struct.pack('>IQBH', delta, timestamp, flags, len(key)) + key + value
    body = struct.pack('>I', crc32c(checked)) + checked
    return varint(len(body)) + body


def test_single_record_layout(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('ab', 'cde', timestamp=5)
    (path,) = segment_files(tmp_path)
    data = path.read_bytes()
    assert len(data) == 13 + 1 + 19 + 5
    assert parse(data) == ((b'EVLG', 3, 0), [(0, 5, 0, b'ab', b'cde')])


def test_deltas_count_from_each_segment_base(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=150)) as log:
        for n in range(30):
            log.append(f'k{n}', 'v' * (n % 5))
        log.delete('k1')
    seen = []
    files = segment_files(tmp_path)
    assert len(files) > 2
    for path in files:
        (magic, version, base), records = parse(path.read_bytes())
        assert (magic, version) == (b'EVLG', 3)
        assert [r[0] for r in records] == list(range(len(records)))
        seen += [(base + r[0], r[3], r[2] & 1) for r in records]
    assert seen == [(n, f'k{n}'.encode(), 0) for n in range(30)] + [(30, b'k1', 1)]


def test_compacted_segments_keep_relative_deltas(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=150)) as log:
        for n in range(40):
            # Every sealed segment mixes overwritten records with ones that survive, so it gets rewritten.
            log.append('hot' if n % 2 else f'cold{n}', f'v{n}')
        assert compact(log).segments_rewritten > 0
        survivors = [(r.offset, r.value) for r in log.replay()]
    seen = []
    for path in segment_files(tmp_path):
        (_, _, base), records = parse(path.read_bytes())
        seen += [(base + r[0], r[4]) for r in records]
    assert seen == survivors


def test_reads_a_hand_written_segment(tmp_path):
    data = struct.pack('>4sBQ', b'EVLG', 3, 1000)
    data += encode(0, 7, b'user', b'first') + encode(1, 8, b'user', b'second') + encode(2, 9, b'user', b'', 1)
    (tmp_path / '00000000000000001000.seg').write_bytes(data)
    with Log.open(tmp_path) as log:
        assert [(r.offset, r.timestamp, r.value, r.tombstone) for r in log.replay()] == [
            (1000, 7, b'first', False), (1001, 8, b'second', False), (1002, 9, b'', True)]
        assert [r.offset for r in log.replay(1002)] == [1002]
        assert log.append('user', 'again') == 1003
    summary = stats(tmp_path)
    assert (summary.records, summary.first_offset, summary.next_offset) == (4, 1000, 1004)
