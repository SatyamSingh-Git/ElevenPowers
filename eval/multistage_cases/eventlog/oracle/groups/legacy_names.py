"""A directory still holding segments named the old way (.log) is refused, not silently restarted."""
import pytest

from eventlog import Log, LogConfig


def make_log(directory):
    with Log.open(directory, LogConfig(segment_bytes=100)) as log:
        for n in range(12):
            log.append(f'k{n}', 'value')
    return sorted(path for path in directory.iterdir() if path.suffix != '.idx')


def refused(directory):
    with pytest.raises(Exception) as caught:
        Log.open(directory, LogConfig(segment_bytes=100))
    assert type(caught.value).__name__ == 'LegacySegmentName'
    return str(caught.value)


def test_all_old_names(tmp_path):
    segments = make_log(tmp_path)
    for path in segments:
        path.rename(path.with_name(path.stem + '.log'))
    assert refused(tmp_path) == '00000000000000000000.log: segment files now use the .seg suffix'


def test_names_the_lowest_offset_old_file(tmp_path):
    segments = make_log(tmp_path)
    assert len(segments) > 2
    for path in segments[1:]:
        path.rename(path.with_name(path.stem + '.log'))
    assert refused(tmp_path) == f'{segments[1].stem}.log: segment files now use the .seg suffix'


def test_unrelated_log_files_do_not_block(tmp_path):
    (tmp_path / 'service.log').write_text('started\n')
    (tmp_path / '123.log').write_text('not a segment\n')
    with Log.open(tmp_path) as log:
        assert log.append('k', 'v') == 0
    with Log.open(tmp_path) as log:
        assert [r.value for r in log.replay()] == [b'v']
