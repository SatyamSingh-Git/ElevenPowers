"""Reporting gaps: stretches longer than ``gap_minutes`` in which a sensor sent nothing.

A day is measured from midnight to the next midnight, or to ``until`` when
that comes first, so asking about today counts only the time already passed.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Gap:
    sensor: str
    zone: str
    start: datetime
    end: datetime

    @property
    def minutes(self):
        return int((self.end - self.start).total_seconds() // 60)


def find_gaps(readings, day, gap_minutes, until):
    """Gaps per sensor on ``day``, sorted by sensor and then start."""
    start = datetime.combine(day, datetime.min.time())
    end = min(start + timedelta(days=1), until)
    longest = timedelta(minutes=gap_minutes)
    times = {}
    for reading in readings:
        if start <= reading.at < end:
            times.setdefault((reading.sensor, reading.zone), []).append(reading.at)
    gaps = []
    for (sensor, zone), stamps in sorted(times.items()):
        edges = [start, *sorted(stamps), end]
        gaps += [
            Gap(sensor, zone, earlier, later)
            for earlier, later in zip(edges, edges[1:])
            if later - earlier > longest
        ]
    return gaps


def uptime(gaps, sensors, day, until):
    """Share of the measured day, in percent, each sensor was not in a gap."""
    start = datetime.combine(day, datetime.min.time())
    measured = (min(start + timedelta(days=1), until) - start).total_seconds()
    lost = {sensor: 0.0 for sensor in sensors}
    for gap in gaps:
        lost[gap.sensor] += (gap.end - gap.start).total_seconds()
    return {sensor: round(100 * (1 - lost[sensor] / measured), 1) for sensor in sorted(sensors)}
