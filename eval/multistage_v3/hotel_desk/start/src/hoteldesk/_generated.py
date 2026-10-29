# Generated from the county lodging and sales tax table. Do not edit by hand:
# regenerate it from the published table when the county issues a new edition.
from decimal import Decimal

TAX_TABLE_EDITION = "2026-01"

TAX_RATES = {
    "lodging": Decimal("0.1175"),
    "sales": Decimal("0.0725"),
    "exempt": Decimal("0"),
}
