"""Account statements: every shipment an account sent in a period, with its charge."""
from dataclasses import dataclass
from datetime import date

from ..core.money import format_amount, percent_of
from ..storage.shipments import ShipmentStore
from .tables import render_table


@dataclass(frozen=True)
class Statement:
    account: str
    start: date
    end: date
    shipments: tuple
    vat_percent: object

    @property
    def subtotal(self):
        return sum(shipment.total for shipment in self.shipments)

    @property
    def vat(self):
        return percent_of(self.subtotal, self.vat_percent)


def account_statement(settings, account, start, end):
    shipments = [shipment for shipment in ShipmentStore(settings.store_path).find(account=account)
                 if start <= shipment.ship_date <= end]
    return Statement(account, start, end, tuple(shipments), settings.vat_percent)


def render_statement(statement):
    heading = (f"Statement for {statement.account}, "
               f"{statement.start.isoformat()} to {statement.end.isoformat()}")
    if not statement.shipments:
        return heading + "\n\nNo shipments in this period."
    rows = [(shipment.ship_date.isoformat(), shipment.tracking_number, shipment.service,
             format_amount(shipment.total)) for shipment in statement.shipments]
    rows += [
        ("", "", "Subtotal", format_amount(statement.subtotal)),
        ("", "", f"VAT {statement.vat_percent}%", format_amount(statement.vat)),
    ]
    table = render_table(("Ships", "Tracking number", "Service", "Amount"), rows, right=("Amount",))
    return heading + "\n\n" + table
