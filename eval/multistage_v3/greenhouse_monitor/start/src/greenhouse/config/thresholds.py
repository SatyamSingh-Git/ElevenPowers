"""Alert limits per zone and sensor kind, read from ``thresholds.json``.

    {"*": {"humidity": {"high": 90}},
     "gh1": {"temperature": {"low": 10, "high": 30}}}

The ``"*"`` entry holds site-wide limits. A zone's own entry overrides them
one bound at a time, so a zone can tighten ``high`` and keep the site ``low``.
The file is optional; without it nothing raises a limit alert.
"""
from pathlib import Path

from ..core.errors import ConfigError
from ..core.model import Limits
from ..core.units import kinds
from .jsonfile import number, read_json

SITE_WIDE = "*"


class Thresholds:
    def __init__(self, table=None):
        self._table = table or {}

    def limits(self, zone, kind):
        site = self._table.get(SITE_WIDE, {}).get(kind, Limits())
        own = self._table.get(zone, {}).get(kind, Limits())
        return Limits(
            low=site.low if own.low is None else own.low,
            high=site.high if own.high is None else own.high,
        )

    def zones(self):
        return sorted(zone for zone in self._table if zone != SITE_WIDE)


def load_thresholds(path):
    path = Path(path)
    if not path.exists():
        return Thresholds()
    table = {}
    for zone, by_kind in read_json(path).items():
        if not isinstance(by_kind, dict):
            raise ConfigError(f"thresholds for {zone} must be an object")
        table[zone] = {kind: _limits(zone, kind, bounds) for kind, bounds in by_kind.items()}
    return Thresholds(table)


def _limits(zone, kind, bounds):
    if kind not in kinds():
        raise ConfigError(f"unknown kind: {kind}")
    if not isinstance(bounds, dict) or set(bounds) - {"low", "high"}:
        raise ConfigError(f"thresholds for {zone} {kind} take only low and high")
    low = None if bounds.get("low") is None else number(bounds["low"], f"{zone} {kind} low")
    high = None if bounds.get("high") is None else number(bounds["high"], f"{zone} {kind} high")
    if low is not None and high is not None and low >= high:
        raise ConfigError(f"thresholds for {zone} {kind}: low must be below high")
    return Limits(low=low, high=high)
