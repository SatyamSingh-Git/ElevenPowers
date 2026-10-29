"""Stage 8: late_checkout_fee defaults to 40.00 and the settings file can still change it."""
import json

from hoteldesk.cli import main
from hoteldesk.config import Settings, load_settings


def test_default(tmp_path):
    assert Settings().late_checkout_fee == 4000
    assert load_settings(tmp_path / "no-such-file.json").late_checkout_fee == 4000


def test_settings_file_overrides(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(json.dumps({"late_checkout_fee": "35.00"}))
    assert load_settings(path).late_checkout_fee == 3500
    path.write_text(json.dumps({"currency": "USD"}))
    assert load_settings(path).late_checkout_fee == 4000


def test_settings_command(tmp_path, capsys):
    assert main(["--settings", str(tmp_path / "hotel.json"), "settings"]) == 0
    assert "late_checkout_fee: 40.00" in capsys.readouterr().out
