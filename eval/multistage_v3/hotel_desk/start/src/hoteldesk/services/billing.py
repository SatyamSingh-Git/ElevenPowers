"""Posting charges and payments to folios."""
from ..errors import InvalidState, ValidationError
from ..model.charges import TAX, lookup, tax_rate
from ..model.folios import Charge, Payment
from ..model.reservations import IN_HOUSE
from ..money import format_money, tax_on

PAYMENT_METHODS = ("card", "cash", "transfer")


def post_charge(hotel, reservation_id, code, amount, description=None):
    """Post a charge, and the tax it carries, to an in-house guest's folio.

    Returns the charges posted: the charge itself, then its tax if there is any.
    """
    reservation = hotel.reservation(reservation_id)
    if reservation.status != IN_HOUSE:
        raise InvalidState(f"Reservation {reservation.id} is not in house")
    if amount <= 0:
        raise ValidationError("Charge amount must be positive")
    charge_code = lookup(code)
    folio = hotel.folio(reservation.id)
    charge = Charge(hotel.business_date, charge_code.code, description or charge_code.description, amount)
    posted = [charge]
    tax = tax_on(amount, tax_rate(charge_code))
    if tax:
        posted.append(Charge(hotel.business_date, TAX, f"Tax on {charge.description}", tax))
    folio.charges.extend(posted)
    return posted


def post_payment(hotel, reservation_id, amount, method="card"):
    if method not in PAYMENT_METHODS:
        raise ValidationError(f"Unknown payment method: {method}")
    if amount <= 0:
        raise ValidationError("Payment amount must be positive")
    folio = hotel.folio(reservation_id)
    if amount > folio.balance:
        raise ValidationError(
            f"Payment of {format_money(amount)} is more than the balance of {format_money(folio.balance)}")
    payment = Payment(hotel.business_date, method, amount)
    folio.payments.append(payment)
    return payment


def transfer_charge(hotel, from_id, index, to_id):
    """Move one charge (by its position on the folio) to another in-house guest's folio."""
    source = hotel.folio(from_id)
    target_reservation = hotel.reservation(to_id)
    if target_reservation.status != IN_HOUSE:
        raise InvalidState(f"Reservation {target_reservation.id} is not in house")
    if not 0 <= index < len(source.charges):
        raise ValidationError(f"Folio {from_id} has no charge {index + 1}")
    charge = source.charges.pop(index)
    hotel.folio(to_id).charges.append(charge)
    return charge
