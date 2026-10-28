"""Parcels and the carrier's acceptance limits."""
from dataclasses import dataclass

from .errors import ValidationError
from .money import format_amount
from .units import GRAMS_PER_KG, format_kg

MAX_WEIGHT_GRAMS = 30 * GRAMS_PER_KG
MAX_SIDE_CM = 150
MAX_DECLARED_PENCE = 250_000


@dataclass(frozen=True)
class Parcel:
    weight_grams: int
    length_cm: int
    width_cm: int
    height_cm: int
    declared_pence: int = 0

    @property
    def sides(self):
        return (self.length_cm, self.width_cm, self.height_cm)

    @property
    def longest_side(self):
        return max(self.sides)

    @property
    def volume_cm3(self):
        return self.length_cm * self.width_cm * self.height_cm


def validate_parcel(parcel):
    if parcel.weight_grams <= 0:
        raise ValidationError("parcel weight must be positive")
    if parcel.weight_grams >= MAX_WEIGHT_GRAMS:
        raise ValidationError(
            f"parcel too heavy: {format_kg(parcel.weight_grams)} kg (max {format_kg(MAX_WEIGHT_GRAMS)} kg)")
    if min(parcel.sides) <= 0:
        raise ValidationError("parcel dimensions must be positive")
    if parcel.longest_side > MAX_SIDE_CM:
        raise ValidationError(f"parcel too long: {parcel.longest_side} cm (max {MAX_SIDE_CM} cm)")
    if parcel.declared_pence > MAX_DECLARED_PENCE:
        raise ValidationError(
            f"declared value {format_amount(parcel.declared_pence)} is over the limit of "
            f"{format_amount(MAX_DECLARED_PENCE)}")
    return parcel
