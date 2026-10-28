"""The rate card for one service, as a table of weight bands by zone."""
from .._generated import BASE_RATES, CARD_VERSION, EXTRA_KG_PENCE
from ..core.money import format_amount
from ..core.units import format_kg
from ..rating.tariff import check_service, service_name
from .tables import render_table


def render_rate_card(service):
    bands = BASE_RATES[check_service(service)]
    zones = [f"Zone {zone}" for zone in range(1, len(bands[0][1]) + 1)]
    rows = [(f"up to {format_kg(limit)} kg", *(format_amount(price) for price in prices))
            for limit, prices in bands]
    footer = (f"Above {format_kg(bands[-1][0])} kg: the top band plus "
              f"{format_amount(EXTRA_KG_PENCE[service])} per started kg.")
    heading = f"{service_name(service)} rate card {CARD_VERSION} (base postage, before surcharges)"
    return "\n\n".join([heading, render_table(("Weight", *zones), rows, right=tuple(zones)), footer])
