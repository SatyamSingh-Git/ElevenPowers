"""Threshold and silence checks on each sensor's latest reading."""
from datetime import timedelta

from ..core.model import Alert


def evaluate(latest, thresholds, settings, now):
    """Alerts for the latest reading of every sensor, in sensor order.

    A sensor that has not reported for more than ``stale_minutes`` raises
    ``stale`` and is not checked against its limits: its value is old news.
    """
    alerts = []
    stale_after = timedelta(minutes=settings.stale_minutes)
    for sensor in sorted(latest):
        reading = latest[sensor]
        if now - reading.at > stale_after:
            alerts.append(_alert(reading, now, "stale", settings.stale_minutes))
            continue
        alert = _limit_alert(reading, thresholds.limits(reading.zone, reading.kind), now)
        if alert is not None:
            alerts.append(alert)
    return alerts


def _limit_alert(reading, limits, now):
    if limits.high is not None and reading.value > limits.high:
        return _alert(reading, now, "high", limits.high)
    if limits.low is not None and reading.value < limits.low:
        return _alert(reading, now, "low", limits.low)
    return None


def _alert(reading, now, code, limit):
    return Alert(
        at=now,
        zone=reading.zone,
        sensor=reading.sensor,
        kind=reading.kind,
        code=code,
        value=reading.value,
        limit=limit,
        unit=reading.unit,
    )


def unreported(alerts, logged):
    """The alerts whose key is not among the ``logged`` keys."""
    return [alert for alert in alerts if alert.key() not in logged]
