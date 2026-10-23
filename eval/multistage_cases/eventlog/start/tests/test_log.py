import pytest

from eventlog import (ConfigError, EmptyKey, KeyTooLarge, Log, LogClosed, LogConfig, ManualClock, NotASegment,
                      OffsetOutOfRange, UnsupportedFormat, ValueTooLarge)


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.suffix == '.log')


def test_offsets_count_up_from_zero(tmp_path):
    with Log.open(tmp_path) as log:
        assert [log.append('k', str(n)) for n in range(3)] == [0, 1, 2]
        assert log.next_offset == 3


def test_replay_returns_what_was_appended(tmp_path):
    clock = ManualClock(1000)
    with Log.open(tmp_path, clock=clock) as log:
        log.append('a', 'one')
        clock.advance(5)
        log.append(b'b', b'two')
        log.delete('a', timestamp=42)
        records = list(log.replay())
    assert [(r.offset, r.timestamp, r.key, r.value, r.tombstone) for r in records] == [
        (0, 1000, b'a', b'one', False), (1, 1005, b'b', b'two', False), (2, 42, b'a', b'', True)]


def test_replay_from_an_offset(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=128)) as log:
        for n in range(20):
            log.append(f'k{n}', 'v' * n)
        for start in range(21):
            assert [r.offset for r in log.replay(start)] == list(range(start, 20))


def test_replay_outside_the_log(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
        with pytest.raises(OffsetOutOfRange, match=r'^offset 2 is outside 0\.\.1$'):
            log.replay(2)


def test_read_one_record(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(6):
            log.append('k', str(n))
        assert log.read(4).value == b'4'
        assert log.read(6) is None


def test_rolls_to_a_new_segment(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(10):
            log.append('key', 'value')
        assert len(log.segments) > 1
        assert [s.base_offset for s in log.segments] == sorted(s.base_offset for s in log.segments)
    names = [path.name for path in segment_files(tmp_path)]
    assert names[0] == '00000000000000000000.log'


def test_reopen_carries_on(tmp_path):
    config = LogConfig(segment_bytes=100)
    with Log.open(tmp_path, config) as log:
        for n in range(7):
            log.append('k', str(n))
    with Log.open(tmp_path, config) as log:
        assert log.next_offset == 7
        assert log.append('k', '7') == 7
        assert [r.value for r in log.replay(5)] == [b'5', b'6', b'7']


def test_torn_tail_is_cut_off_on_open(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', '1')
        log.append('b', '2')
    last = segment_files(tmp_path)[-1]
    last.write_bytes(last.read_bytes()[:-3])
    with Log.open(tmp_path) as log:
        assert [r.key for r in log.replay()] == [b'a']
        assert log.append('c', '3') == 1
    with Log.open(tmp_path) as log:
        assert [r.key for r in log.replay()] == [b'a', b'c']


def test_corruption_is_not_dropped(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', '1')
        log.append('b', '2')
    last = segment_files(tmp_path)[-1]
    data = bytearray(last.read_bytes())
    data[13 + 10] ^= 0xFF
    last.write_bytes(bytes(data))
    with pytest.raises(Exception, match='corrupt record at position 13'):
        Log.open(tmp_path)


def test_limits(tmp_path):
    with Log.open(tmp_path, LogConfig(max_key_bytes=4, max_value_bytes=8)) as log:
        with pytest.raises(KeyTooLarge, match='^key of 5 bytes exceeds max_key_bytes 4$'):
            log.append('abcde', 'v')
        with pytest.raises(ValueTooLarge, match='^value of 9 bytes exceeds max_value_bytes 8$'):
            log.append('k', '123456789')
        with pytest.raises(EmptyKey):
            log.append('', 'v')
        assert log.next_offset == 0


def test_config_is_checked():
    with pytest.raises(ConfigError, match='^segment_bytes must be at least 64$'):
        LogConfig(segment_bytes=10)


def test_closed_log_refuses_appends(tmp_path):
    log = Log.open(tmp_path)
    log.close()
    with pytest.raises(LogClosed):
        log.append('k', 'v')


def test_other_versions_are_refused(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    path = segment_files(tmp_path)[0]
    data = bytearray(path.read_bytes())
    data[4] = 9
    path.write_bytes(bytes(data))
    with pytest.raises(UnsupportedFormat, match=r'^00000000000000000000\.log: unsupported format version 9$'):
        Log.open(tmp_path)


def test_foreign_files_are_refused(tmp_path):
    (tmp_path / '00000000000000000000.log').write_bytes(b'hello world, not a segment')
    with pytest.raises(NotASegment):
        Log.open(tmp_path)
