"""The shipment store: one JSON document holding every shipment and the next sequence number."""
from datetime import date
import json
from pathlib import Path

from ..core.address import Address
from ..core.charges import Line, Quote
from ..core.clock import format_timestamp, parse_timestamp
from ..core.errors import StoreError, UnknownShipment
from ..core.parcel import Parcel
from ..core.shipment import Shipment
from .files import write_atomic

FORMAT_VERSION = 1


class ShipmentStore:
    def __init__(self, path):
        self.path = Path(path)
        self._shipments = {}
        self._next_sequence = 1
        if self.path.is_file():
            document = json.loads(self.path.read_text(encoding="utf-8"))
            if document.get("version") != FORMAT_VERSION:
                raise StoreError(f"{self.path} has store version {document.get('version')}, "
                                 f"expected {FORMAT_VERSION}")
            self._next_sequence = document["next_sequence"]
            for record in document["shipments"]:
                shipment = _decode(record)
                self._shipments[shipment.tracking_number] = shipment

    def __contains__(self, number):
        return number in self._shipments

    def take_sequence(self):
        sequence = self._next_sequence
        self._next_sequence += 1
        return sequence

    def add(self, shipment):
        self._shipments[shipment.tracking_number] = shipment

    def remove(self, number):
        self.get(number)
        del self._shipments[number]

    def get(self, number):
        try:
            return self._shipments[number]
        except KeyError:
            raise UnknownShipment(number) from None

    def find(self, *, ship_date=None, status=None, account=None):
        """Matching shipments in the order they were booked."""
        found = [shipment for shipment in self._shipments.values()
                 if (ship_date is None or shipment.ship_date == ship_date)
                 and (status is None or shipment.status == status)
                 and (account is None or shipment.account == account)]
        return sorted(found, key=lambda shipment: shipment.sequence)

    def save(self):
        document = {
            "version": FORMAT_VERSION,
            "next_sequence": self._next_sequence,
            "shipments": [encode_shipment(shipment) for shipment in self.find()],
        }
        write_atomic(self.path, json.dumps(document, indent=2) + "\n")


def encode_shipment(shipment):
    parcel, quote, recipient = shipment.parcel, shipment.quote, shipment.recipient
    return {
        "tracking_number": shipment.tracking_number,
        "sequence": shipment.sequence,
        "account": shipment.account,
        "service": shipment.service,
        "recipient": {"name": recipient.name, "line1": recipient.line1,
                      "town": recipient.town, "postcode": recipient.postcode},
        "parcel": {"weight_grams": parcel.weight_grams, "length_cm": parcel.length_cm,
                   "width_cm": parcel.width_cm, "height_cm": parcel.height_cm,
                   "declared_pence": parcel.declared_pence},
        "quote": {"zone": quote.zone, "billable_grams": quote.billable_grams,
                  "lines": [[line.code, line.pence] for line in quote.lines]},
        "booked_at": format_timestamp(shipment.booked_at),
        "ship_date": shipment.ship_date.isoformat(),
        "expected_delivery": shipment.expected_delivery.isoformat(),
        "residential": shipment.residential,
        "signature": shipment.signature,
        "status": shipment.status,
        "return_of": shipment.return_of,
    }


def _decode(record):
    quote = record["quote"]
    return Shipment(
        tracking_number=record["tracking_number"],
        sequence=record["sequence"],
        account=record["account"],
        service=record["service"],
        recipient=Address(**record["recipient"]),
        parcel=Parcel(**record["parcel"]),
        quote=Quote(record["service"], quote["zone"], quote["billable_grams"],
                    tuple(Line(code, pence) for code, pence in quote["lines"])),
        booked_at=parse_timestamp(record["booked_at"]),
        ship_date=date.fromisoformat(record["ship_date"]),
        expected_delivery=date.fromisoformat(record["expected_delivery"]),
        residential=record["residential"],
        signature=record["signature"],
        status=record["status"],
        return_of=record["return_of"],
    )
