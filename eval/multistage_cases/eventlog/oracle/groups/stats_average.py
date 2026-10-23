"""Stats report the average record size, segment headers excluded, rounded to one decimal."""
from eventlog import Log, LogConfig, format_stats, stats


def segment_files(directory):
    return [path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx']


def expected_average(directory, records):
    files = segment_files(directory)
    return round((sum(path.stat().st_size for path in files) - 13 * len(files)) / records, 1)


def test_empty_log_averages_zero(tmp_path):
    Log.open(tmp_path).close()
    summary = stats(tmp_path)
    assert summary.average_record_bytes == 0.0
    assert 'average: 0.0 B' in format_stats(summary).splitlines()


def test_average_over_several_segments(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=120)) as log:
        for n in range(17):
            log.append(f'k{n}', 'v' * (n % 7))
        log.delete('k3')
    assert len(segment_files(tmp_path)) > 2
    summary = stats(tmp_path)
    assert summary.records == 18
    assert summary.average_record_bytes == expected_average(tmp_path, 18)
    assert f'average: {summary.average_record_bytes:.1f} B' in format_stats(summary).splitlines()


def test_average_is_rounded_to_one_decimal(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', '')
        log.append('a', 'b')
        log.append('a', 'b')
    summary = stats(tmp_path)
    assert summary.average_record_bytes == expected_average(tmp_path, 3)
    assert summary.average_record_bytes != (sum(p.stat().st_size for p in segment_files(tmp_path)) - 13) / 3
