"""Rate plans: how a room type's base rate is adjusted for a booking."""
from dataclasses import dataclass


@dataclass
class RatePlan:
    code: str
    name: str
    discount_percent: int = 0
    min_nights: int = 1
    breakfast: bool = False
