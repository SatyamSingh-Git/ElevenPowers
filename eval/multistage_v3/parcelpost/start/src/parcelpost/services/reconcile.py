"""Reconciliation: does the carrier's invoice charge what our manifest for that day says?"""
from dataclasses import dataclass
from datetime import date

from ..core.errors import ManifestError
from ..formats.carrier_invoice import parse_carrier_invoice
from ..formats.manifest import manifest_filename
from .billing import read_charges

NOT_INVOICED = "not invoiced"
NOT_MANIFESTED = "not manifested"
AMOUNT_DIFFERS = "amount differs"


@dataclass(frozen=True)
class Difference:
    tracking_number: str
    problem: str
    ours: int | None
    theirs: int | None


@dataclass(frozen=True)
class Reconciliation:
    day: date
    matched: int
    differences: tuple

    @property
    def balanced(self):
        return not self.differences


def reconcile(settings, day, carrier_text):
    path = settings.manifest_dir / manifest_filename(day)
    if not path.is_file():
        raise ManifestError(f"no manifest for {day.isoformat()}; close the day first")
    ours = {charge.tracking_number: charge.pence for charge in read_charges(path)}
    theirs = parse_carrier_invoice(carrier_text)
    differences, matched = [], 0
    for number in sorted(ours.keys() | theirs.keys()):
        if number not in theirs:
            differences.append(Difference(number, NOT_INVOICED, ours[number], None))
        elif number not in ours:
            differences.append(Difference(number, NOT_MANIFESTED, None, theirs[number]))
        elif ours[number] != theirs[number]:
            differences.append(Difference(number, AMOUNT_DIFFERS, ours[number], theirs[number]))
        else:
            matched += 1
    return Reconciliation(day, matched, tuple(differences))
