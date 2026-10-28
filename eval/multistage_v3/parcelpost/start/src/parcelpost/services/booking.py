"""Booking: check an order, price it, give it a tracking number and keep it."""
from dataclasses import dataclass

from ..core.accounts import check_account_code
from ..core.calendar import add_business_days, ship_date
from ..core.errors import ValidationError
from ..core.ids import new_tracking_number
from ..core.parcel import validate_parcel
from ..core.shipment import BOOKED, Shipment
from ..formats.labels import LABEL_FORMATS, label_filename, render_label
from ..rating.quote import quote, quote_all
from ..rating.tariff import service_name, transit_days
from ..storage.files import write_atomic
from ..storage.shipments import ShipmentStore


@dataclass(frozen=True)
class Order:
    account: str
    recipient: object
    parcel: object
    service: str | None = None
    residential: bool = False
    signature: bool = False
    return_of: str | None = None


def quote_parcel(settings, parcel, postcode, service=None, *, residential=False, signature=False):
    validate_parcel(parcel)
    return quote(parcel, postcode, service or settings.default_service,
                 fuel_percent=settings.fuel_percent, residential=residential, signature=signature)


def quote_every_service(settings, parcel, postcode, *, residential=False, signature=False):
    validate_parcel(parcel)
    return quote_all(parcel, postcode, fuel_percent=settings.fuel_percent,
                     residential=residential, signature=signature)


def expected_delivery(settings, service, booked_at):
    """When a parcel booked now on `service` should arrive, as quoted and as booked."""
    return add_business_days(ship_date(booked_at, settings.cutoff), transit_days(service))


def label_path(settings, shipment):
    return settings.labels_dir / label_filename(shipment.tracking_number, settings.label_format)


def book(settings, order, *, clock):
    check_account_code(order.account)
    price = quote_parcel(settings, order.parcel, order.recipient.postcode, order.service,
                         residential=order.residential, signature=order.signature)
    store = ShipmentStore(settings.store_path)
    booked_at = clock.now()
    sequence = store.take_sequence()
    shipment = Shipment(
        tracking_number=new_tracking_number(sequence),
        sequence=sequence,
        account=order.account,
        service=price.service,
        recipient=order.recipient,
        parcel=order.parcel,
        quote=price,
        booked_at=booked_at,
        ship_date=ship_date(booked_at, settings.cutoff),
        expected_delivery=expected_delivery(settings, price.service, booked_at),
        residential=order.residential,
        signature=order.signature,
        return_of=order.return_of,
    )
    store.add(shipment)
    store.save()
    write_atomic(label_path(settings, shipment),
                 render_label(shipment, service_name(shipment.service), settings.label_format))
    return shipment


def void(settings, number):
    """Cancel a booking the carrier has not been told about yet."""
    store = ShipmentStore(settings.store_path)
    shipment = store.get(number.strip().upper())
    if shipment.status != BOOKED:
        raise ValidationError(f"{shipment.tracking_number} is {shipment.status}; "
                              "only shipments not yet manifested can be voided")
    store.remove(shipment.tracking_number)
    store.save()
    for extension, _ in LABEL_FORMATS.values():
        (settings.labels_dir / (shipment.tracking_number + extension)).unlink(missing_ok=True)
    return shipment
