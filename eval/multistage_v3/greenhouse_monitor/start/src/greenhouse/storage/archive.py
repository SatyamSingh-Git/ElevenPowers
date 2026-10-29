"""Moving old rows out of the readings log into monthly archive files.

Rows from before the cutoff day move to ``archive/readings-YYYY-MM.csv`` in
the data directory. Each archive file starts with the log's own first line,
and rows are moved as text, so archiving never reinterprets a value.
"""
from pathlib import Path


def archive_readings(log_path, archive_dir, cutoff):
    """Move rows dated before ``cutoff`` and return how many went to each month."""
    log_path, archive_dir = Path(log_path), Path(archive_dir)
    lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    if not lines:
        return {}
    first, *rows = lines
    keep, moving = [], {}
    for row in filter(None, rows):
        stamp = row[:10]
        if stamp < cutoff.isoformat():
            moving.setdefault(stamp[:7], []).append(row)
        else:
            keep.append(row)
    if not moving:
        return {}
    archive_dir.mkdir(exist_ok=True)
    for month, moved in sorted(moving.items()):
        target = archive_dir / f"readings-{month}.csv"
        lines = moved if target.exists() else [first, *moved]
        with target.open("a", encoding="utf-8") as handle:
            handle.write("".join(line + "\n" for line in lines))
    log_path.write_text("".join(line + "\n" for line in [first, *keep]), encoding="utf-8")
    return {month: len(moved) for month, moved in sorted(moving.items())}
