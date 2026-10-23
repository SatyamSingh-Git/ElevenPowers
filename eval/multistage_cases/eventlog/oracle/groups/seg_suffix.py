"""Segment files are named with twenty digits and the .seg suffix; index files keep .idx."""
import re

from eventlog import Log, LogConfig, compact, stats

NAME = re.compile(r'^\d{20}\.seg$')


def names(directory):
    return sorted(path.name for path in directory.iterdir())


def check(directory):
    found = names(directory)
    segments = [name for name in found if not name.endswith('.idx')]
    assert segments and all(NAME.match(name) for name in segments)
    assert sorted(name[:-4] + '.idx' for name in segments) == [name for name in found if name.endswith('.idx')]
    return segments


def test_new_segments_use_seg(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(12):
            log.append(f'k{n}', 'value')
        bases = [segment.base_offset for segment in log.segments]
    segments = check(tmp_path)
    assert segments == [f'{base:020d}.seg' for base in bases]
    assert segments[0] == '00000000000000000000.seg'


def test_compaction_keeps_the_names(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(30):
            # Every sealed segment mixes overwritten records with ones that survive, so it gets rewritten.
            log.append('hot' if n % 2 else f'cold{n}', f'v{n}')
        assert compact(log).segments_rewritten > 0
        expected = [(r.offset, r.value) for r in log.replay()]
    check(tmp_path)
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        assert [(r.offset, r.value) for r in log.replay()] == expected


def test_stats_find_seg_files(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(12):
            log.append(f'k{n}', 'value')
    summary = stats(tmp_path)
    assert summary.segments == len(check(tmp_path)) > 1
    assert summary.records == 12
