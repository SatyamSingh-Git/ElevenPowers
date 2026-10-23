"""segment_bytes is a ceiling: the log rolls before an append that would cross it."""
import struct

from eventlog import Log, LogConfig


def segments(directory):
    files = [path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx']
    return sorted(files, key=lambda path: int(path.stem))


def record_starts(segment):
    data = segment.with_suffix('.idx').read_bytes()
    return [struct.unpack_from('>II', data, at)[1] for at in range(0, len(data), 8)]


def check(directory, limit):
    files = segments(directory)
    assert len(files) > 2
    sizes = [path.stat().st_size for path in files]
    assert max(sizes) <= limit
    for earlier, later in zip(files, files[1:]):
        # A log may also roll once a segment is exactly full, leaving an empty newest segment.
        if later.stat().st_size == 13:
            continue
        starts = record_starts(later) + [later.stat().st_size]
        first_record = starts[1] - starts[0]
        # It rolled only because the next record would not have fit.
        assert earlier.stat().st_size + first_record > limit


def test_never_past_the_limit(tmp_path):
    for limit in (100, 150, 333):
        directory = tmp_path / str(limit)
        with Log.open(directory, LogConfig(segment_bytes=limit, index_interval_bytes=0)) as log:
            for n in range(40):
                log.append(f'k{n}', 'v' * (n * 7 % 23))
            assert [r.offset for r in log.replay()] == list(range(40))
        check(directory, limit)


def test_ceiling_holds_across_reopen(tmp_path):
    config = LogConfig(segment_bytes=120, index_interval_bytes=0)
    for round_ in range(4):
        with Log.open(tmp_path, config) as log:
            for n in range(5):
                log.append(f'r{round_}', 'x' * (n * 5))
    with Log.open(tmp_path, config) as log:
        assert [r.offset for r in log.replay()] == list(range(20))
    check(tmp_path, 120)
