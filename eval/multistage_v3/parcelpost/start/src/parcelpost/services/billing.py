"""Billing: one invoice per account for each closed manifest."""
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby
from operator import attrgetter

from ..core.accounts import DEFAULT_PAYMENT_DAYS
from ..core.errors import ManifestError
from ..core.money import percent_of
from ..formats.manifest import manifest_filename
from ..reports.invoices import render_invoice
from ..storage.accounts import AccountBook
from ..storage.files import write_atomic


@dataclass(frozen=True)
class Charge:
    tracking_number: str
    account: str
    service: str
    pence: int


@dataclass(frozen=True)
class Invoice:
    number: str
    account: str
    customer: str
    day: date
    due: date
    charges: tuple
    vat_percent: Decimal

    @property
    def subtotal(self):
        return sum(charge.pence for charge in self.charges)

    @property
    def vat(self):
        return percent_of(self.subtotal, self.vat_percent)

    @property
    def total(self):
        return self.subtotal + self.vat


def invoice_number(account, day):
    return f"INV-{account}-{day:%Y%m%d}"


def read_charges(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [Charge(row["tracking_number"], row["account"], row["service"], int(row["charge"]))
                for row in csv.DictReader(handle)]


def make_invoices(day, charges, vat_percent, accounts):
    """Charges from one manifest into invoices; an unregistered account is billed under its code."""
    invoices = []
    for code, group in groupby(charges, key=attrgetter("account")):
        account = accounts.find(code)
        days = account.payment_days if account else DEFAULT_PAYMENT_DAYS
        invoices.append(Invoice(invoice_number(code, day), code, account.name if account else code, day,
                                day + timedelta(days=days), tuple(group), vat_percent))
    return invoices


def bill_day(settings, day):
    path = settings.manifest_dir / manifest_filename(day)
    if not path.is_file():
        raise ManifestError(f"no manifest for {day.isoformat()}; close the day first")
    invoices = make_invoices(day, read_charges(path), settings.vat_percent,
                             AccountBook(settings.accounts_path))
    for invoice in invoices:
        write_atomic(settings.invoices_dir / f"{invoice.number}.txt", render_invoice(invoice))
    return invoices
