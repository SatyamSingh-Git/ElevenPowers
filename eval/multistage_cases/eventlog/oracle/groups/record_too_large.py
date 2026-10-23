"""A record that cannot fit even in an empty segment is refused with RecordTooLarge."""
import pytest

from eventlog import Log, LogConfig


def files(directory):
    return {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}


def encoded_size(directory, key, value):
    with Log.open(directory) as log:
        log.append(key, value)
    (segment,) = [path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx']
    return segment.stat().st_size - 13


def test_refused_with_the_encoded_size(tmp_path):
    size = encoded_size(tmp_path / 'probe', 'key', 'v' * 60)
    directory = tmp_path / 'log'
    with Log.open(directory, LogConfig(segment_bytes=64)) as log:
        log.append('a', '1')
        before = files(directory)
        with pytest.raises(Exception) as caught:
            log.append('key', 'v' * 60)
        assert type(caught.value).__name__ == 'RecordTooLarge'
        assert str(caught.value) == f'record of {size} bytes exceeds segment_bytes 64'
        assert files(directory) == before
        assert log.next_offset == 1
        assert log.append('b', '2') == 1
        assert [r.key for r in log.replay()] == [b'a', b'b']


def test_largest_record_that_fits_is_accepted(tmp_path):
    size = encoded_size(tmp_path / 'probe', 'key', 'v' * 40)
    directory = tmp_path / 'log'
    with Log.open(directory, LogConfig(segment_bytes=13 + size)) as log:
        assert log.append('key', 'v' * 40) == 0
        with pytest.raises(Exception) as caught:
            log.append('key', 'v' * 41)
        assert str(caught.value) == f'record of {size + 1} bytes exceeds segment_bytes {13 + size}'
        assert log.append('key', 'v' * 40) == 1


def test_value_limit_still_applies(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=64, max_value_bytes=10)) as log:
        with pytest.raises(Exception) as caught:
            log.append('k', 'v' * 11)
        assert type(caught.value).__name__ == 'ValueTooLarge'
