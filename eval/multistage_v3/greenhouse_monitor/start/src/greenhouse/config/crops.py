"""Crop profiles: what each crop the site grows needs from its zone.

``base_temperature`` is the temperature below which the crop does not develop,
used for growing degree days.
"""
from dataclasses import dataclass

from ..core.errors import ConfigError


@dataclass(frozen=True)
class Crop:
    name: str
    base_temperature: float


CROPS = {
    entry.name: entry
    for entry in (
        Crop("tomato", 10.0),
        Crop("cucumber", 12.0),
        Crop("pepper", 10.0),
        Crop("lettuce", 4.0),
        Crop("strawberry", 7.0),
        Crop("basil", 10.0),
    )
}


def crop(name):
    try:
        return CROPS[name]
    except KeyError:
        raise ConfigError(f"unknown crop: {name}") from None
