"""Short-term trends: how fast each sensor's value has been moving over the last hours.

The rate is the least-squares slope of the sensor's readings in the window,
in canonical units per hour. A sensor needs at least ``MIN_POINTS`` readings
in the window, spread over at least ``MIN_SPAN`` minutes, to have a trend.
"""
from dataclasses import dataclass
from datetime import timedelta

MIN_POINTS = 3
MIN_SPAN = 30


@dataclass(frozen=True)
class Trend:
    sensor: str
    zone: str
    kind: str
    unit: str
    per_hour: float
    points: int

    @property
    def direction(self):
        if abs(self.per_hour) < 0.05:
            return "steady"
        return "rising" if self.per_hour > 0 else "falling"


def slope_per_hour(points):
    """Least-squares slope of (hours, value) points."""
    count = len(points)
    mean_x = sum(x for x, _ in points) / count
    mean_y = sum(y for _, y in points) / count
    spread = sum((x - mean_x) ** 2 for x, _ in points)
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / spread


def trends(readings, now, hours):
    """A Trend for every sensor with enough readings in the ``hours`` before ``now``."""
    since = now - timedelta(hours=hours)
    by_sensor = {}
    for reading in readings:
        if since <= reading.at <= now:
            by_sensor.setdefault(reading.sensor, []).append(reading)
    found = []
    for sensor, items in sorted(by_sensor.items()):
        items.sort(key=lambda r: r.at)
        if len(items) < MIN_POINTS or items[-1].at - items[0].at < timedelta(minutes=MIN_SPAN):
            continue
        points = [((r.at - since).total_seconds() / 3600, r.value) for r in items]
        last = items[-1]
        found.append(Trend(sensor, last.zone, last.kind, last.unit, round(slope_per_hour(points), 2), len(items)))
    return found
