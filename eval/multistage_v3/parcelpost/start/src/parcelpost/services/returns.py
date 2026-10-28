"""Returns: a prepaid shipment back to the depot for something already delivered."""
from ..core.address import Address
from ..core.errors import ValidationError
from ..core.shipment import DELIVERED
from ..storage.shipments import ShipmentStore
from .booking import Order, book

RETURNS_ADDRESS = Address("Returns desk", "Unit 4 Tyburn Road", "Birmingham", "B24 8HJ")
RETURN_SERVICE = "economy"
RETURN_WINDOW_DAYS = 30


def book_return(settings, number, *, clock):
    store = ShipmentStore(settings.store_path)
    original = store.get(number.strip().upper())
    if original.return_of is not None:
        raise ValidationError(f"{original.tracking_number} is itself a return")
    if original.status != DELIVERED:
        raise ValidationError(f"{original.tracking_number} is {original.status}; "
                              "only delivered shipments can be returned")
    if (clock.now().date() - original.expected_delivery).days > RETURN_WINDOW_DAYS:
        raise ValidationError(f"{original.tracking_number} is outside the {RETURN_WINDOW_DAYS}-day "
                              "return window")
    taken = [shipment.tracking_number for shipment in store.find()
             if shipment.return_of == original.tracking_number]
    if taken:
        raise ValidationError(f"{original.tracking_number} already has return {taken[0]}")
    order = Order(account=original.account, recipient=RETURNS_ADDRESS, parcel=original.parcel,
                  service=RETURN_SERVICE, return_of=original.tracking_number)
    return book(settings, order, clock=clock)
