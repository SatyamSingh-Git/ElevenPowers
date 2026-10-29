"""Readings taken by hand with a hand-held meter while a controller is down.

The staff enter the probe's id and what the meter shows; the reading is
checked, converted and calibrated like a controller row and logged at once.
Light is never entered by hand: the hand-held meters have no light probe.
"""
from ..core.errors import ValidationError
from ..core.model import Reading
from ..core.units import canonical_unit, check_kind, check_range, round_for, to_canonical

HANDHELD_KINDS = ("temperature", "humidity", "soil_moisture")


def record_manual(log, layout, calibration, *, zone, sensor, kind, value, unit, at):
    """Log one hand-entered reading taken at ``at`` and return it."""
    zone = layout.zone(zone.strip()).id
    sensor = sensor.strip()
    if not sensor:
        raise ValidationError("missing sensor")
    kind = check_kind(kind)
    if kind not in HANDHELD_KINDS:
        raise ValidationError(f"{kind} cannot be entered by hand")
    raw = to_canonical(kind, value, unit)
    calibrated = check_range(kind, raw + calibration.offset_for(sensor))
    reading = Reading(
        at=at,
        zone=zone,
        sensor=sensor,
        kind=kind,
        value=round_for(kind, calibrated),
        unit=canonical_unit(kind),
        raw=round_for(kind, raw),
    )
    log.write(reading)
    return reading
