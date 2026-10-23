"""The stats summary prints sizes in binary units, with an average line after bytes."""
from eventlog import Log, LogConfig, format_stats, stats


def segment_bytes_on_disk(directory):
    return sum(path.stat().st_size for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def lines(directory):
    return format_stats(stats(directory)).splitlines()


def test_small_sizes_are_whole_bytes(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
        log.append('k', 'w')
    size = segment_bytes_on_disk(tmp_path)
    assert size < 1024
    assert f'bytes: {size} B' in lines(tmp_path)


def test_kibibytes_have_one_decimal(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=1000)) as log:
        for n in range(60):
            log.append(f'key{n}', 'x' * 50)
    size = segment_bytes_on_disk(tmp_path)
    assert 1024 <= size < 1024 ** 2
    assert f'bytes: {size / 1024:.1f} KiB' in lines(tmp_path)


def test_mebibytes(tmp_path):
    with Log.open(tmp_path) as log:
        for n in range(20):
            log.append(f'blob{n}', bytes(60_000))
    size = segment_bytes_on_disk(tmp_path)
    assert size >= 1024 ** 2
    assert f'bytes: {size / 1024 ** 2:.1f} MiB' in lines(tmp_path)


def test_average_line_follows_bytes(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('k', 'v')
    shown = lines(tmp_path)
    at = next(n for n, line in enumerate(shown) if line.startswith('bytes: '))
    assert shown[at + 1].startswith('average: ') and shown[at + 1].endswith(' B')
    assert shown[0] == 'segments: 1'
    assert 'records: 1' in shown
