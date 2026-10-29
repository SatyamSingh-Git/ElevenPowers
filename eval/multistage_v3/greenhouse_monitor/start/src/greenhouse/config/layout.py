"""The zones of the greenhouse, read from ``layout.json``.

    {"zones": [{"id": "gh1", "name": "North house", "crop": "tomato",
                "valve": "V1", "target_moisture": 40, "area_m2": 120}]}

``target_moisture`` is optional; a zone without it gets no irrigation
suggestion. ``area_m2`` and ``flow_lpm`` (litres per minute through the
zone's valve) are optional and only used for water estimates.
"""
from pathlib import Path

from ..core.errors import ConfigError
from ..core.model import Zone
from .jsonfile import number, read_json

REQUIRED = ("id", "name", "crop", "valve")


class Layout:
    def __init__(self, zones):
        self._zones = {}
        for zone in zones:
            if zone.id in self._zones:
                raise ConfigError(f"duplicate zone: {zone.id}")
            self._zones[zone.id] = zone

    def __contains__(self, zone_id):
        return zone_id in self._zones

    def zone(self, zone_id):
        try:
            return self._zones[zone_id]
        except KeyError:
            raise ConfigError(f"unknown zone: {zone_id}") from None

    def zones(self):
        return list(self._zones.values())

    def ids(self):
        return list(self._zones)


def load_layout(path):
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"layout not found: {path.name}")
    entries = read_json(path).get("zones")
    if not isinstance(entries, list):
        raise ConfigError(f"{path.name}: expected a list of zones")
    return Layout(_zone(entry) for entry in entries)


def _zone(entry):
    if not isinstance(entry, dict):
        raise ConfigError("each zone must be an object")
    missing = [name for name in REQUIRED if not entry.get(name)]
    if missing:
        raise ConfigError(f"zone {entry.get('id', '?')} is missing {', '.join(missing)}")
    zone_id = str(entry["id"])
    target = entry.get("target_moisture")
    if target is not None:
        target = number(target, f"zone {zone_id} target_moisture")
        if not 0 <= target <= 100:
            raise ConfigError(f"zone {zone_id} target_moisture must be between 0 and 100")
    area = entry.get("area_m2")
    flow = entry.get("flow_lpm")
    return Zone(
        id=zone_id,
        name=str(entry["name"]),
        crop=str(entry["crop"]),
        valve=str(entry["valve"]),
        target_moisture=target,
        area_m2=None if area is None else number(area, f"zone {zone_id} area_m2"),
        flow_lpm=None if flow is None else number(flow, f"zone {zone_id} flow_lpm"),
    )
