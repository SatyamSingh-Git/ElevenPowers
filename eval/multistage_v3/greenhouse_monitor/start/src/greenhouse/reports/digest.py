"""The alert digest the on-call phone gateway sends each evening, and alert counts over days.

The gateway picks up ``outbox/digest-YYYY-MM-DD.txt`` and sends it as one
message, so the digest groups the day's alerts by zone and keeps lines short.
"""
from collections import Counter
from pathlib import Path

from .formatting import table
from .messages import describe


def digest_text(day, records):
    if not records:
        return f"{day.isoformat()}: no alerts"
    lines = [f"{day.isoformat()}: {len(records)} alerts"]
    zones = sorted({record["zone"] for record in records})
    for zone in zones:
        lines.append(f"[{zone}]")
        lines += [f"{r['at'][11:16]} {describe(r)}" for r in records if r["zone"] == zone]
    return "\n".join(lines)


def write_digest(outbox, day, text):
    outbox = Path(outbox)
    outbox.mkdir(exist_ok=True)
    target = outbox / f"digest-{day.isoformat()}.txt"
    target.write_text(text + "\n", encoding="utf-8")
    return target


def alert_counts(records):
    """How many alerts each zone raised per code."""
    return Counter((record["zone"], record["code"]) for record in records)


def counts_text(counts, first, last):
    title = f"Alerts {first.isoformat()} to {last.isoformat()}"
    if not counts:
        return f"{title}: none"
    rows = [[zone, code, count] for (zone, code), count in sorted(counts.items())]
    return f"{title}\n" + table(["zone", "code", "alerts"], rows)
