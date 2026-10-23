"""Index entries are 8 bytes: offset relative to the segment base (u32), then position (u32)."""
import struct

from eventlog import Log, LogConfig, compact

DENSE = dict(index_interval_bytes=0)


def index_files(directory):
    return sorted(path for path in directory.iterdir() if path.suffix == '.idx')


def segment_for(index_path):
    (path,) = [p for p in index_path.parent.iterdir()
               if p.stem == index_path.stem and p.suffix != '.idx' and p.is_file()]
    return path


def entries(index_path):
    data = index_path.read_bytes()
    assert len(data) % 8 == 0
    return [struct.unpack_from('>II', data, at) for at in range(0, len(data), 8)]


def test_dense_entries_are_8_bytes_and_relative(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=150, **DENSE)) as log:
        for n in range(25):
            log.append(f'k{n}', f'value-{n}')
        expected = {}
        for record in log.replay():
            expected.setdefault(record.offset, record)
    files = index_files(tmp_path)
    assert len(files) > 2
    seen = []
    for path in files:
        base = int(path.stem)
        found = entries(path)
        assert [relative for relative, _ in found] == list(range(len(found)))
        positions = [position for _, position in found]
        if positions:
            assert positions[0] == 13
            assert positions == sorted(set(positions))
            assert positions[-1] < segment_for(path).stat().st_size
        seen += [base + relative for relative, _ in found]
    assert seen == list(range(25))


def test_compacted_segments_get_relative_entries(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=150, **DENSE)) as log:
        for n in range(40):
            # Every sealed segment mixes overwritten records with ones that survive, so it gets rewritten.
            log.append('hot' if n % 2 else f'cold{n}', f'v{n}')
        assert compact(log).segments_rewritten > 0
        survivors = [r.offset for r in log.replay()]
    seen = []
    for path in index_files(tmp_path):
        base = int(path.stem)
        found = entries(path)
        if found:
            assert found[0][1] == 13
        seen += [base + relative for relative, _ in found]
    assert seen == survivors


def test_replay_from_any_offset(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=150, **DENSE)) as log:
        for n in range(25):
            log.append(f'k{n}', f'value-{n}')
    with Log.open(tmp_path, LogConfig(segment_bytes=150, **DENSE)) as log:
        for start in range(26):
            assert [r.offset for r in log.replay(start)] == list(range(start, 25))
