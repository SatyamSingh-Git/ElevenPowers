from eventlog import Log, LogConfig
from eventlog.index import lookup, read_entries


def test_one_entry_per_record(tmp_path):
    with Log.open(tmp_path) as log:
        for n in range(5):
            log.append('k', str(n))
        segment = log.segments[0]
        entries = read_entries(segment.index_path)
    assert [offset for offset, _ in entries] == [0, 1, 2, 3, 4]
    assert entries[0][1] == 13
    assert (tmp_path / '00000000000000000000.idx').stat().st_size == 5 * 12


def test_lookup_finds_the_entry_at_or_before():
    entries = [(10, 13), (12, 60), (15, 120)]
    assert lookup(entries, 9) is None
    assert lookup(entries, 10) == 13
    assert lookup(entries, 14) == 60
    assert lookup(entries, 99) == 120


def test_half_written_entry_is_ignored(tmp_path):
    path = tmp_path / 'x.idx'
    path.write_bytes(bytes(12) + b'\x00\x01')
    assert read_entries(path) == [(0, 0)]


def test_index_is_rebuilt_on_open(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=1000)) as log:
        for n in range(4):
            log.append('k', str(n))
        index_path = log.segments[-1].index_path
    index_path.write_bytes(b'')
    with Log.open(tmp_path) as log:
        assert [offset for offset, _ in read_entries(index_path)] == [0, 1, 2, 3]
        assert [r.value for r in log.replay(2)] == [b'2', b'3']
