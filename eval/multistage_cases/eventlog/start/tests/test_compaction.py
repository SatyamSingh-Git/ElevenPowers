from eventlog import Log, LogConfig, compact, snapshot

CONFIG = LogConfig(segment_bytes=150)


def fill(log):
    for n in range(30):
        log.append(f'k{n % 4}', f'v{n}')
    log.delete('k3')
    log.append('k0', 'final')


def test_keeps_the_latest_value_of_each_key(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        before = snapshot(log)
        compact(log)
        assert snapshot(log) == before == {b'k0': b'final', b'k1': b'v29', b'k2': b'v26'}


def test_offsets_are_kept(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        original = {r.offset: r for r in log.replay()}
        compact(log)
        after = list(log.replay())
    assert [r.offset for r in after] == sorted(r.offset for r in after)
    assert all(original[r.offset] == r for r in after)


def test_sealed_segments_hold_only_latest_live_records(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        latest = {}
        for record in log.replay():
            latest[record.key] = record
        compact(log)
        for segment in log.sealed_segments:
            for record in segment.records():
                assert latest[record.key] == record and not record.tombstone


def test_result_counts(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        before = len(list(log.replay()))
        result = compact(log)
        after = len(list(log.replay()))
    assert result.records_removed == before - after > 0
    assert result.bytes_after < result.bytes_before


def test_survives_reopen_and_keeps_appending(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        compact(log)
        expected = list(log.replay())
        next_offset = log.next_offset
    with Log.open(tmp_path, CONFIG) as log:
        assert list(log.replay()) == expected
        assert log.append('k9', 'x') == next_offset
        middle = expected[len(expected) // 2].offset
        assert [r.offset for r in log.replay(middle)] == [r.offset for r in expected if r.offset >= middle] + [next_offset]


def test_second_compaction_changes_nothing(tmp_path):
    with Log.open(tmp_path, CONFIG) as log:
        fill(log)
        compact(log)
        result = compact(log)
    assert result.records_removed == 0 and result.segments_rewritten == 0
