"""The index is sparse: an entry for a segment's first record, then one per index_interval_bytes."""
import struct

from eventlog import Log, LogConfig


def entries(index_path):
    data = index_path.read_bytes()
    assert len(data) % 8 == 0
    return [struct.unpack_from('>II', data, at) for at in range(0, len(data), 8)]


def check_spacing(found, interval, largest_record):
    assert found[0] == (0, 13)
    positions = [position for _, position in found]
    gaps = [later - earlier for earlier, later in zip(positions, positions[1:])]
    assert gaps, 'expected more than one entry'
    assert all(interval <= gap < interval + largest_record for gap in gaps)
    relatives = [relative for relative, _ in found]
    assert relatives == sorted(set(relatives))


def test_default_interval_is_4096(tmp_path):
    with Log.open(tmp_path) as log:
        for n in range(300):
            log.append(f'key{n:03d}', 'v' * 90)
        assert [r.offset for r in log.replay(150)] == list(range(150, 300))
    (index_path,) = [p for p in tmp_path.iterdir() if p.suffix == '.idx']
    found = entries(index_path)
    check_spacing(found, 4096, 130)
    assert 5 <= len(found) <= 9


def test_custom_interval(tmp_path):
    with Log.open(tmp_path, LogConfig(index_interval_bytes=1000)) as log:
        for n in range(120):
            log.append(f'key{n:03d}', 'v' * 40)
    (index_path,) = [p for p in tmp_path.iterdir() if p.suffix == '.idx']
    check_spacing(entries(index_path), 1000, 80)


def test_replay_scans_forward_from_the_nearest_entry(tmp_path):
    config = LogConfig(segment_bytes=3000, index_interval_bytes=500)
    with Log.open(tmp_path, config) as log:
        for n in range(150):
            log.append(f'key{n}', f'value{n}' * 3)
    with Log.open(tmp_path, config) as log:
        for start in range(151):
            records = list(log.replay(start))
            assert [r.offset for r in records] == list(range(start, 150))
            assert [r.value for r in records] == [f'value{n}'.encode() * 3 for n in range(start, 150)]


def test_rebuilt_index_is_sparse_too(tmp_path):
    config = LogConfig(index_interval_bytes=1000)
    with Log.open(tmp_path, config) as log:
        for n in range(120):
            log.append(f'key{n:03d}', 'v' * 40)
    (index_path,) = [p for p in tmp_path.iterdir() if p.suffix == '.idx']
    index_path.write_bytes(b'')
    with Log.open(tmp_path, config) as log:
        assert [r.offset for r in log.replay(77)] == list(range(77, 120))
    check_spacing(entries(index_path), 1000, 80)
