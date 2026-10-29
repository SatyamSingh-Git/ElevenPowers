# Generated from the finance team's calendar and tax sheet (calendar-2026.2.xlsx).
# Do not edit by hand: change the sheet and regenerate.
from datetime import date
from decimal import Decimal

CALENDAR_VERSION = "2026.2"

HOLIDAYS = {
    date(2026, 1, 1): "New Year's Day",
    date(2026, 1, 16): "Founders' Day",
    date(2026, 4, 3): "Spring Holiday",
    date(2026, 5, 4): "May Day",
    date(2026, 8, 31): "Late Summer Holiday",
    date(2026, 12, 25): "Christmas Day",
    date(2026, 12, 28): "Boxing Day (observed)",
    date(2027, 1, 1): "New Year's Day",
    date(2027, 1, 15): "Founders' Day",
    date(2027, 3, 26): "Spring Holiday",
    date(2027, 5, 3): "May Day",
    date(2027, 8, 30): "Late Summer Holiday",
    date(2027, 12, 27): "Christmas Day (observed)",
    date(2027, 12, 28): "Boxing Day (observed)",
}

# Annual income bands as (upper limit, rate); the last band has no upper limit.
TAX_BANDS = (
    (Decimal("12000"), Decimal("0")),
    (Decimal("45000"), Decimal("0.15")),
    (None, Decimal("0.30")),
)
