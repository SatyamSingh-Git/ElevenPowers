"""Compaction by key, and the read-only stats view of a log directory."""
from eventlog import Log, LogConfig, compact, format_stats, snapshot, stats

CONFIG = LogConfig(segment_bytes=150)


def segment_files(directory):
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix != '.idx')


def fill(log):
    for n in range(40):
        log.append(f'k{n % 5}', f'v{n}')
    log.delete('k3')
    log.delete('k4')
    log.append('k4', 'back')
    log.append('k0', 'final')


def test_compaction_keeps_latest_values_and_offsets(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        original = {r.offset: r for r in log.replay()}
        latest = {r.key: r.offset for r in original.values()}
        before = snapshot(log)
        result = compact(log)
        after = list(log.replay())
        assert snapshot(log) == before == {b'k0': b'final', b'k1': b'v36', b'k2': b'v37', b'k4': b'back'}
        assert [r.offset for r in after] == sorted(r.offset for r in after)
        assert all(original[r.offset] == r for r in after)
        active = log.segments[-1].base_offset
        for record in after:
            if record.offset < active:
                assert latest[record.key] == record.offset and not record.tombstone
        assert result.records_removed == len(original) - len(after) > 0


def test_compaction_survives_reopen(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        compact(log)
        expected = [(r.offset, r.key, r.value) for r in log.replay()]
        next_offset = log.next_offset
    with Log.open(tmp_path, CONFIG) as log:
        assert [(r.offset, r.key, r.value) for r in log.replay()] == expected
        assert log.append('k9', 'new') == next_offset
        for offset, _, _ in expected:
            assert [r.offset for r in log.replay(offset)] == [o for o, _, _ in expected if o >= offset] + [next_offset]


def test_stats_counts(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(11):
            log.append(f'k{n % 3}', 'value')
        log.delete('k1')
        files = segment_files(tmp_path)
        summary = stats(tmp_path)
        assert summary.segments == len(files) > 1
        assert summary.records == 12
        assert summary.keys == 2
        assert summary.tombstones == 1
        assert summary.bytes == sum(path.stat().st_size for path in files)
        assert (summary.first_offset, summary.next_offset) == (0, 12)


def test_stats_after_compaction(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        compact(log)
        records = list(log.replay())
        summary = stats(tmp_path)
        assert summary.records == len(records)
        assert summary.keys == 4
        assert summary.tombstones == sum(r.tombstone for r in records)
        assert summary.segments == len(segment_files(tmp_path))
        assert (summary.first_offset, summary.next_offset) == (log.first_offset, log.next_offset)


def test_stats_summary_lines(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(6):
            log.append('k', 'v')
    summary = stats(tmp_path)
    lines = format_stats(summary).splitlines()
    assert f'segments: {summary.segments}' in lines
    assert 'records: 6' in lines
    assert 'keys: 1' in lines
    assert 'offsets: 0..6' in lines
