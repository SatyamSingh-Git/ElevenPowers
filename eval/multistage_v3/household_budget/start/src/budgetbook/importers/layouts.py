"""The statement layouts budgetbook knows. Each bank's export maps onto one of them."""
from ..errors import ValidationError
from ..model.money import parse_amount
from .base import Layout
from .registry import register


def _signed_amount(values):
    return parse_amount(values["Amount"])


def _debit_credit_amount(values):
    debit, credit = values["Debit"], values["Credit"]
    if bool(debit) == bool(credit):
        raise ValidationError("exactly one of Debit and Credit must be filled in")
    return -parse_amount(debit) if debit else parse_amount(credit)


def _amount_less_fee(values):
    # App banks report a card fee in its own column, as a positive number taken on top.
    fee = parse_amount(values["Fee"]) if values.get("Fee") else 0
    return parse_amount(values["Amount"]) - fee


def _charge_amount(values):
    # Card exports show a purchase as a positive charge; to the ledger it is money out.
    return -parse_amount(values["Amount"])


register(Layout(
    name="standard",
    columns=("Date", "Description", "Amount"),
    date_column="Date",
    date_style="iso",
    payee_column="Description",
    amount=_signed_amount,
))

register(Layout(
    name="debit_credit",
    columns=("Date", "Description", "Debit", "Credit"),
    date_column="Date",
    date_style="dmy",
    payee_column="Description",
    amount=_debit_credit_amount,
))

register(Layout(
    name="card",
    columns=("Transaction Date", "Merchant", "Amount"),
    date_column="Transaction Date",
    date_style="mdy",
    payee_column="Merchant",
    amount=_charge_amount,
    memo_column="Reference",
))

register(Layout(
    name="app_export",
    columns=("Type", "Started Date", "Description", "Amount", "Fee"),
    date_column="Started Date",
    date_style="iso_time",
    payee_column="Description",
    amount=_amount_less_fee,
    memo_column="Type",
))
