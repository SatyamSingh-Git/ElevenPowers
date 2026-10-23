"""Compaction by key: sealed segments keep only the latest record of each key.

A key whose latest record is a tombstone disappears from sealed segments
altogether. The active segment is never touched, and offsets never change, so
readers holding an offset can carry on from it.
"""
from dataclasses import dataclass
import os

from .codec import encode_record
from .index import IndexWriter
from .segment import Segment, encode_header


@dataclass(frozen=True)
class CompactionResult:
    segments_rewritten: int = 0
    segments_removed: int = 0
    records_removed: int = 0
    bytes_before: int = 0
    bytes_after: int = 0


def compact(log):
    latest = {}
    for segment in log.segments:
        for record in segment.records():
            latest[record.key] = record.offset

    sealed, rewritten, removed, dropped = [], 0, 0, 0
    bytes_before = sum(segment.size for segment in log.sealed_segments)
    for segment in log.sealed_segments:
        records = list(segment.records())
        keep = [record for record in records if latest[record.key] == record.offset and not record.tombstone]
        dropped += len(records) - len(keep)
        if len(keep) == len(records):
            sealed.append(segment)
        elif keep:
            sealed.append(_rewrite(segment, keep))
            rewritten += 1
        else:
            segment.path.unlink()
            segment.index_path.unlink(missing_ok=True)
            removed += 1
    # The active segment must stay last, so an emptied log keeps its next offset.
    log._replace_sealed(sealed)
    return CompactionResult(rewritten, removed, dropped, bytes_before, sum(segment.size for segment in sealed))


def _rewrite(segment, records):
    """Write `records` as a new copy of `segment` and swap it in atomically."""
    data = bytearray(encode_header(segment.base_offset))
    positions = []
    for record in records:
        positions.append((record.offset, len(data)))
        data += encode_record(record)

    staged = segment.path.with_name(segment.path.name + '.compacting')
    staged.write_bytes(data)
    staged_index = segment.index_path.with_name(segment.index_path.name + '.compacting')
    staged_index.unlink(missing_ok=True)
    writer = IndexWriter(staged_index)
    for offset, position in positions:
        writer.add(offset, position)
    writer.close()

    os.replace(staged, segment.path)
    os.replace(staged_index, segment.index_path)
    return Segment.open(segment.path)
