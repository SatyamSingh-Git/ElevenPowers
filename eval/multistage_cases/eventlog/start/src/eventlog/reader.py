from . import index
from .errors import OffsetOutOfRange


def replay(log, from_offset=None):
    """Iterate the log's records in offset order, from `from_offset` or the start.

    Any offset from the first segment's base up to the next offset to be
    written is accepted; offsets that compaction removed are skipped.
    """
    first, next_offset = log.first_offset, log.next_offset
    if from_offset is None:
        from_offset = first
    if not first <= from_offset <= next_offset:
        raise OffsetOutOfRange(from_offset, first, next_offset)
    return _records(log.segments, from_offset)


def _records(segments, from_offset):
    for number, segment in enumerate(segments):
        following = segments[number + 1] if number + 1 < len(segments) else None
        if following is not None and following.base_offset <= from_offset:
            continue
        start = None
        if from_offset > segment.base_offset:
            start = index.lookup(index.read_entries(segment.index_path), from_offset)
        for record in segment.records(start):
            if record.offset >= from_offset:
                yield record


def snapshot(log):
    """The latest value of every key that has not been deleted."""
    values = {}
    for record in replay(log):
        if record.tombstone:
            values.pop(record.key, None)
        else:
            values[record.key] = record.value
    return values


def tail(log, count):
    """The last `count` records, oldest first."""
    if count <= 0:
        return []
    kept = []
    for segment in reversed(log.segments):
        kept[:0] = list(segment.records())
        if len(kept) >= count:
            break
    return kept[-count:]
