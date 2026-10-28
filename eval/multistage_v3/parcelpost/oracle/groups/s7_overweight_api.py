"""Heavy parcels pay overweight, long parcels oversize, heavy and long parcels both."""
from parcelpost.config import load_settings
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import quote_parcel


def _quote(tmp_path, parcel):
    return quote_parcel(load_settings(tmp_path), parcel, "B1 1AA", "ground")


def test_heavy_parcel_pays_overweight(tmp_path):
    found = _quote(tmp_path, Parcel(27_000, 40, 30, 30))
    assert found.amount("overweight") == 1800
    assert found.amount("oversize") == 0


def test_long_parcel_pays_oversize(tmp_path):
    found = _quote(tmp_path, Parcel(2_500, 110, 20, 20))
    assert found.amount("oversize") == 1200
    assert found.amount("overweight") == 0


def test_heavy_long_parcel_pays_both(tmp_path):
    found = _quote(tmp_path, Parcel(27_000, 110, 30, 30))
    assert found.amount("oversize") == 1200
    assert found.amount("overweight") == 1800
