"""Appending, replaying, rolling, reopening and recovering a log."""
import pytest

from eventlog import Log, LogConfig, ManualClock


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def raises(name, message, call, *args):
    with pytest.raises(Exception) as caught:
        call(*args)
    assert type(caught.value).__name__ == name
    assert str(caught.value) == message


def fields(record):
    return (record.offset, record.timestamp, record.key, record.value, record.tombstone)


def test_offsets_count_up_from_zero(tmp_path):
    with Log.open(tmp_path) as log:
        assert [log.append('k', str(n)) for n in range(4)] == [0, 1, 2, 3]
        assert log.next_offset == 4


def test_replay_returns_what_was_appended(tmp_path):
    clock = ManualClock(1_000)
    with Log.open(tmp_path, clock=clock) as log:
        log.append('a', 'one')
        clock.advance(250)
        log.append(b'b', b'\x00two')
        log.delete('a', timestamp=7)
        assert [fields(r) for r in log.replay()] == [
            (0, 1_000, b'a', b'one', False), (1, 1_250, b'b', b'\x00two', False), (2, 7, b'a', b'', True)]


def test_replay_from_every_offset_across_segments(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=128)) as log:
        for n in range(24):
            log.append(f'k{n}', 'v' * n)
        assert len(segment_files(tmp_path)) > 2
        for start in range(25):
            records = list(log.replay(start))
            assert [r.offset for r in records] == list(range(start, 24))
            assert [r.value for r in records] == [b'v' * n for n in range(start, 24)]


def test_replay_bounds(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
        log.append('k', 'w')
        assert list(log.replay(2)) == []
        raises('OffsetOutOfRange', 'offset 3 is outside 0..2', log.replay, 3)


def test_reopen_carries_on(tmp_path):
    config = LogConfig(segment_bytes=100)
    with Log.open(tmp_path, config) as log:
        for n in range(9):
            log.append(f'key{n % 2}', f'value{n}')
    with Log.open(tmp_path, config) as log:
        assert log.next_offset == 9
        assert log.append('key0', 'value9') == 9
        for start in range(11):
            assert [r.value for r in log.replay(start)] == [f'value{n}'.encode() for n in range(start, 10)]
    with Log.open(tmp_path, config) as log:
        assert log.next_offset == 10


def test_torn_tail_is_cut_off_on_open(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', 'first')
        log.append('b', 'second')
        log.append('c', 'third')
    last = segment_files(tmp_path)[-1]
    last.write_bytes(last.read_bytes()[:-4])
    with Log.open(tmp_path) as log:
        assert [r.key for r in log.replay()] == [b'a', b'b']
        assert log.next_offset == 2
        assert log.append('d', 'fourth') == 2
    with Log.open(tmp_path) as log:
        assert [r.value for r in log.replay()] == [b'first', b'second', b'fourth']


def test_limits(tmp_path):
    with Log.open(tmp_path, LogConfig(max_key_bytes=4, max_value_bytes=8)) as log:
        raises('KeyTooLarge', 'key of 5 bytes exceeds max_key_bytes 4', log.append, 'abcde', 'v')
        raises('ValueTooLarge', 'value of 9 bytes exceeds max_value_bytes 8', log.append, 'k', '123456789')
        assert log.next_offset == 0
        assert log.append('abcd', '12345678') == 0
