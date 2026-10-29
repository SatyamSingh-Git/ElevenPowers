"""The records passed between storage, services and reports."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    crop: str
    valve: str
    target_moisture: float | None = None
    area_m2: float | None = None
    flow_lpm: float | None = None


@dataclass(frozen=True)
class Reading:
    """One sensor value in its kind's canonical unit, calibration applied."""

    at: datetime
    zone: str
    sensor: str
    kind: str
    value: float
    unit: str
    raw: float | None = None


@dataclass(frozen=True)
class Limits:
    low: float | None = None
    high: float | None = None

    def is_empty(self):
        return self.low is None and self.high is None


@dataclass(frozen=True)
class Alert:
    at: datetime
    zone: str
    sensor: str
    kind: str
    code: str
    value: float
    limit: float
    unit: str

    def key(self) -> tuple[date, str, str]:
        """Alerts with the same key are reported once a day."""
        return (self.at.date(), self.sensor, self.code)


@dataclass(frozen=True)
class DailyStats:
    zone: str
    kind: str
    unit: str
    count: int
    low: float
    high: float
    mean: float


@dataclass(frozen=True)
class Suggestion:
    zone: str
    minutes: int
    reason: str
