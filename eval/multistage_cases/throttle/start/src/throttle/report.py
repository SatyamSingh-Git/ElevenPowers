"""Summaries of a Throttle's state for logs, dashboards and CSV exports."""
import csv
import io

from .durations import format_duration

COLUMNS = ('key', 'policy', 'remaining', 'retry', 'resets')


def summarise(throttle):
    """Counts over every tracked key, and the key closest to its limit."""
    entries = throttle.snapshot()
    busiest = None
    if entries:
        busiest = min(entries, key=lambda entry: (entry['remaining'] / entry['limit'], entry['key']))['key']
    return {
        'keys': len(entries),
        'exhausted': sum(entry['remaining'] == 0 for entry in entries),
        'busiest': busiest,
    }


def _wait(seconds):
    return format_duration(seconds) if seconds > 0 else '-'


def render_table(throttle):
    """A plain-text table, one row per key, columns padded to line up."""
    rows = [COLUMNS]
    for entry in throttle.snapshot():
        rows.append((
            entry['key'],
            entry['policy'],
            f"{entry['remaining']}/{entry['limit']}",
            _wait(entry['retry_after']),
            _wait(entry['reset_in']),
        ))
    widths = [max(len(row[column]) for row in rows) for column in range(len(COLUMNS))]
    lines = ['  '.join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip() for row in rows]
    return '\n'.join(lines) + '\n'


def nearest_limit(throttle, count=5):
    """Up to ``count`` keys with the least of their limit left, closest first."""
    entries = sorted(throttle.snapshot(), key=lambda entry: (entry['remaining'] / entry['limit'], entry['key']))
    return [(entry['key'], entry['remaining'], entry['limit']) for entry in entries[:count]]


def render_summary(throttle):
    summary = summarise(throttle)
    if not summary['keys']:
        return 'no keys tracked'
    return f"{summary['keys']} keys, {summary['exhausted']} exhausted, busiest: {summary['busiest']}"


def to_csv(throttle):
    """The snapshot as CSV, one row per key, columns in snapshot order."""
    entries = throttle.snapshot()
    if not entries:
        return ''
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(entries[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(entries)
    return out.getvalue()
