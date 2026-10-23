from eventlog import Log, LogConfig, LogStats, compact, format_stats, stats


def test_empty_log(tmp_path):
    Log.open(tmp_path).close()
    assert stats(tmp_path) == LogStats(segments=1, records=0, keys=0, tombstones=0, bytes=13,
                                       first_offset=0, next_offset=0)


def test_counts(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(8):
            log.append(f'k{n % 3}', 'v')
        log.delete('k1')
        summary = stats(tmp_path)
        assert summary.segments == len(log.segments)
        assert summary.records == 9
        assert summary.keys == 2
        assert summary.tombstones == 1
        assert summary.bytes == sum(segment.size for segment in log.segments)
        assert (summary.first_offset, summary.next_offset) == (0, 9)


def test_after_compaction(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(12):
            log.append('same', str(n))
        compact(log)
        summary = stats(tmp_path)
        assert summary.records == len(list(log.replay()))
        assert summary.first_offset == log.first_offset
        assert summary.next_offset == log.next_offset == 12


def test_torn_tail_is_ignored(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', '1')
        log.append('b', '2')
        path = log.segments[-1].path
    path.write_bytes(path.read_bytes()[:-2])
    assert stats(tmp_path).records == 1


def test_format(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', '1')
    text = format_stats(stats(tmp_path))
    assert text.splitlines() == ['segments: 1', 'records: 1', 'keys: 1', 'tombstones: 0',
                                 f'bytes: {13 + 27 + 2}', 'offsets: 0..1']
