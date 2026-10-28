"""A booked shipment and the statuses it moves through."""
from dataclasses import dataclass
from datetime import date, datetime

from .address import Address
from .charges import Quote
from .parcel import Parcel

BOOKED = "booked"
MANIFESTED = "manifested"
IN_TRANSIT = "in_transit"
DELIVERED = "delivered"
EXCEPTION = "exception"
RETURNED = "returned"

STATUSES = (BOOKED, MANIFESTED, IN_TRANSIT, DELIVERED, EXCEPTION, RETURNED)
FINAL_STATUSES = frozenset({DELIVERED, RETURNED})


@dataclass
class Shipment:
    tracking_number: str
    sequence: int
    account: str
    service: str
    recipient: Address
    parcel: Parcel
    quote: Quote
    booked_at: datetime
    ship_date: date
    expected_delivery: date
    residential: bool = False
    signature: bool = False
    status: str = BOOKED
    return_of: str | None = None

    @property
    def total(self):
        return self.quote.total
