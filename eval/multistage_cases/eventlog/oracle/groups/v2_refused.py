"""Segments written in format version 2 are refused when a log is opened."""
import pytest

from eventlog import Log, LogConfig


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def set_version(path, version):
    data = bytearray(path.read_bytes())
    data[4] = version
    path.write_bytes(bytes(data))


def refused(directory, config=None):
    with pytest.raises(Exception) as caught:
        Log.open(directory, config)
    assert type(caught.value).__name__ == 'UnsupportedFormat'
    return str(caught.value)


def test_version_2_segment_is_refused(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    (path,) = segment_files(tmp_path)
    assert path.read_bytes()[4] == 3
    set_version(path, 2)
    assert refused(tmp_path) == f'{path.name}: unsupported format version 2'


def test_version_2_sealed_segment_is_refused(tmp_path):
    config = LogConfig(segment_bytes=100)
    with Log.open(tmp_path, config) as log:
        for n in range(10):
            log.append('key', f'value{n}')
    files = segment_files(tmp_path)
    assert len(files) > 2
    set_version(files[0], 2)
    assert refused(tmp_path, config) == f'{files[0].name}: unsupported format version 2'
