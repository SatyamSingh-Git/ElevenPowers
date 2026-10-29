"""Water use of irrigation suggestions.

A zone's ``flow_lpm`` in the layout is how many litres per minute its valve
delivers. Zones without it are left out of the totals and listed instead,
so the estimate never pretends to know more than the layout says.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class WaterEstimate:
    litres: dict
    unknown: list

    @property
    def total(self):
        return sum(self.litres.values())


def estimate(layout, suggestions):
    litres, unknown = {}, []
    for suggestion in suggestions:
        if suggestion.minutes == 0:
            continue
        flow = layout.zone(suggestion.zone).flow_lpm
        if flow is None:
            unknown.append(suggestion.zone)
        else:
            litres[suggestion.zone] = round(suggestion.minutes * flow, 1)
    return WaterEstimate(litres, unknown)


def per_square_metre(layout, water):
    """Litres per square metre for zones whose area is known."""
    return {
        zone: round(litres / layout.zone(zone).area_m2, 2)
        for zone, litres in water.litres.items()
        if layout.zone(zone).area_m2
    }
