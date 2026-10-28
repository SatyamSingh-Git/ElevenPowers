"""Collection requests: tell the carrier how much to collect from the depot on a day."""
from dataclasses import dataclass
from datetime import date

from ..core.errors import ValidationError
from ..core.shipment import BOOKED, MANIFESTED
from ..core.units import GRAMS_PER_KG, format_kg
from ..storage.files import write_atomic
from ..storage.shipments import ShipmentStore

VAN_LIMIT_GRAMS = 800 * GRAMS_PER_KG
COLLECTION_WINDOW = "16:00-18:00"


@dataclass(frozen=True)
class Pickup:
    day: date
    depot: str
    parcels: int
    weight_grams: int

    @property
    def vehicle(self):
        return "van" if self.weight_grams <= VAN_LIMIT_GRAMS else "truck"


def request_pickup(settings, day):
    shipments = [shipment for shipment in ShipmentStore(settings.store_path).find(ship_date=day)
                 if shipment.status in (BOOKED, MANIFESTED)]
    if not shipments:
        raise ValidationError(f"nothing to collect on {day.isoformat()}")
    pickup = Pickup(day, settings.depot, len(shipments),
                    sum(shipment.parcel.weight_grams for shipment in shipments))
    write_atomic(settings.data_dir / "pickups" / f"pickup-{day.isoformat()}.txt", pickup_text(pickup))
    return pickup


def pickup_text(pickup):
    return "\n".join([
        f"Collection request for depot {pickup.depot}",
        f"Day: {pickup.day.isoformat()}",
        f"Window: {COLLECTION_WINDOW}",
        f"Parcels: {pickup.parcels}",
        f"Weight: {format_kg(pickup.weight_grams)} kg",
        f"Vehicle: {pickup.vehicle}",
    ]) + "\n"
