"""Segments written in format version 1 are refused when a log is opened."""
import pytest

from eventlog import Log, LogConfig


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def set_version(path, version):
    data = bytearray(path.read_bytes())
    data[4] = version
    path.write_bytes(bytes(data))


def test_version_1_newest_segment_is_refused(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    (path,) = segment_files(tmp_path)
    set_version(path, 1)
    with pytest.raises(Exception) as caught:
        Log.open(tmp_path)
    assert type(caught.value).__name__ == 'UnsupportedFormat'
    assert str(caught.value) == f'{path.name}: unsupported format version 1'


def test_version_1_sealed_segment_is_refused(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(10):
            log.append('key', f'value{n}')
    files = segment_files(tmp_path)
    assert len(files) > 2
    set_version(files[1], 1)
    with pytest.raises(Exception) as caught:
        Log.open(tmp_path, LogConfig(segment_bytes=100))
    assert type(caught.value).__name__ == 'UnsupportedFormat'
    assert str(caught.value) == f'{files[1].name}: unsupported format version 1'


def test_current_version_still_opens(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    with Log.open(tmp_path) as log:
        assert [r.value for r in log.replay()] == [b'v']
