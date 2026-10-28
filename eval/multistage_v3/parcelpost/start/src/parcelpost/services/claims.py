"""Claims against the carrier for lost or damaged parcels."""
from dataclasses import asdict, dataclass
from datetime import date, timedelta
import json

from ..core.errors import ValidationError
from ..core.shipment import DELIVERED, EXCEPTION, FINAL_STATUSES
from ..formats.events import latest_by_number, read_events
from ..storage.files import write_atomic
from ..storage.shipments import ShipmentStore

STANDARD_COVER_PENCE = 2000
LOST_AFTER_DAYS = 10
REASONS = ("lost", "damaged")


@dataclass(frozen=True)
class Claim:
    number: str
    tracking_number: str
    reason: str
    pence: int
    raised_on: str


def compensation(shipment):
    """Declared value when the parcel was insured; otherwise the standard cover at most."""
    declared = shipment.parcel.declared_pence
    if shipment.quote.amount("insurance"):
        return declared
    return min(declared, STANDARD_COVER_PENCE) if declared else STANDARD_COVER_PENCE


def _claims_path(settings):
    return settings.data_dir / "claims.json"


def load_claims(settings):
    path = _claims_path(settings)
    if not path.is_file():
        return []
    return [Claim(**record) for record in json.loads(path.read_text(encoding="utf-8"))["claims"]]


def raise_claim(settings, number, reason, *, clock):
    if reason not in REASONS:
        raise ValidationError(f"claim reason must be one of: {', '.join(REASONS)}")
    shipment = ShipmentStore(settings.store_path).get(number.strip().upper())
    claims = load_claims(settings)
    if any(claim.tracking_number == shipment.tracking_number for claim in claims):
        raise ValidationError(f"{shipment.tracking_number} already has a claim")
    today = clock.now().date()
    if reason == "damaged" and shipment.status != DELIVERED:
        raise ValidationError(f"{shipment.tracking_number} is {shipment.status}; "
                              "damage can only be claimed after delivery")
    if reason == "lost" and not _presumed_lost(settings, shipment, today):
        raise ValidationError(f"{shipment.tracking_number} is not yet presumed lost "
                              f"(no scan for {LOST_AFTER_DAYS} days, or a delivery exception)")
    claim = Claim(f"CLM-{len(claims) + 1:05d}", shipment.tracking_number, reason,
                  compensation(shipment), today.isoformat())
    document = {"claims": [asdict(existing) for existing in claims + [claim]]}
    write_atomic(_claims_path(settings), json.dumps(document, indent=2) + "\n")
    return claim


def _presumed_lost(settings, shipment, today):
    if shipment.status == EXCEPTION:
        return True
    if shipment.status in FINAL_STATUSES:
        return False
    last = latest_by_number(read_events(settings.events_path)).get(shipment.tracking_number)
    since = last.at.date() if last else shipment.ship_date
    return today - since > timedelta(days=LOST_AFTER_DAYS)


def claims_since(settings, start):
    return [claim for claim in load_claims(settings) if date.fromisoformat(claim.raised_on) >= start]
