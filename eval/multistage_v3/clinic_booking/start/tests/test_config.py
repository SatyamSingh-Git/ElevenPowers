from decimal import Decimal

import pytest

from clinicbook.config import Settings, settings_from_dict, settings_to_dict
from clinicbook.errors import ConfigError


def test_defaults_fill_in_what_the_file_leaves_out():
    settings = settings_from_dict({"slot_minutes": 30})
    assert settings.slot_minutes == 30
    assert settings.no_show_fee == Decimal("25.00")
    assert settings.currency == "GBP"


def test_amounts_are_kept_to_the_penny():
    assert settings_from_dict({"no_show_fee": 12.5}).no_show_fee == Decimal("12.50")
    assert settings_from_dict({"no_show_fee": "30"}).no_show_fee == Decimal("30.00")


@pytest.mark.parametrize("raw, message", [
    ({"slot_length": 20}, "unknown setting: slot_length"),
    ({"slot_minutes": "20"}, "setting slot_minutes must be a whole number"),
    ({"slot_minutes": True}, "setting slot_minutes must be a whole number"),
    ({"slot_minutes": 2}, "setting slot_minutes must be at least 5"),
    ({"no_show_fee": "lots"}, "setting no_show_fee must be an amount like 25.00"),
    ({"currency": "JPY"}, "unsupported currency: JPY"),
])
def test_bad_settings_are_refused(raw, message):
    with pytest.raises(ConfigError) as caught:
        settings_from_dict(raw)
    assert str(caught.value) == message


def test_money_uses_the_currency_symbol():
    assert Settings(currency="EUR").money(Decimal("7.5")) == "€7.50"


def test_settings_round_trip_through_the_file_spelling():
    settings = Settings(slot_minutes=15)
    assert settings_from_dict(settings_to_dict(settings)) == settings
