from decimal import Decimal

import pytest

from parcelpost.core.errors import RatingError
from parcelpost.core.parcel import Parcel
from parcelpost.rating.quote import quote, quote_all
from parcelpost.rating.tariff import base_rate, billable_grams, transit_days
from parcelpost.rating.zones import areas_by_zone, zone_for

FUEL = Decimal("7.5")


def test_zone_by_postcode_area():
    assert zone_for("B1 1AA") == 1
    assert zone_for("SW1A 1AA") == 4
    assert zone_for("G1 1AA") == 6


def test_unserved_area():
    with pytest.raises(RatingError, match="no service to postcode area JE"):
        zone_for("JE2 3AB")


def test_areas_by_zone_lists_every_zone():
    assert list(areas_by_zone()) == [1, 2, 3, 4, 5, 6]


def test_billable_weight_uses_volume_and_rounds_up():
    assert billable_grams(Parcel(1200, 20, 15, 10)) == 1500
    # 50 x 40 x 30 cm is 12 kg by volume.
    assert billable_grams(Parcel(3000, 50, 40, 30)) == 12000


def test_base_rate_bands_and_extra_kilograms():
    assert base_rate("ground", 1, 1000) == 395
    assert base_rate("ground", 1, 1001) == 450
    assert base_rate("ground", 4, 30000) == 1640
    assert base_rate("ground", 4, 31500) == 1640 + 2 * 45


def test_unknown_service():
    with pytest.raises(RatingError, match="unknown service: overnight"):
        transit_days("overnight")


def test_quote_lines_and_fuel():
    found = quote(Parcel(2500, 20, 15, 10), "SW1A 1AA", "ground", fuel_percent=FUEL)
    assert [line.code for line in found.lines] == ["base", "fuel"]
    assert found.amount("base") == 710
    assert found.amount("fuel") == 53
    assert found.total == 763


def test_surcharges():
    found = quote(Parcel(2500, 110, 20, 20, declared_pence=30_000), "B1 1AA", "ground",
                  fuel_percent=FUEL, residential=True, signature=True)
    assert found.surcharge_codes == ["residential", "signature", "oversize", "insurance"]
    assert found.amount("oversize") == 1200
    assert found.amount("insurance") == 450


def test_heavy_parcels_pay_oversize():
    found = quote(Parcel(26_000, 40, 30, 30), "B1 1AA", "ground", fuel_percent=FUEL)
    assert found.amount("oversize") == 1200


def test_insurance_has_a_minimum():
    found = quote(Parcel(1000, 20, 15, 10, declared_pence=10_100), "B1 1AA", "ground", fuel_percent=FUEL)
    assert found.amount("insurance") == 200


def test_quote_all_is_cheapest_first():
    quotes = quote_all(Parcel(1000, 20, 15, 10), "B1 1AA", fuel_percent=FUEL)
    assert [found.service for found in quotes] == ["economy", "ground", "express"]
