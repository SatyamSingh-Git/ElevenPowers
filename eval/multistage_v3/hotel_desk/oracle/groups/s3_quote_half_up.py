"""Stage 3: a quote's tax is the tax the stay will post, so it rounds half up too."""
from datetime import date
import json

from hoteldesk.cli import main
from hoteldesk.config import Settings
from hoteldesk.services import pricing
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "KG", "name": "King", "max_adults": 2, "base_rate": "150.00"}],
    "rooms": [{"number": "201", "type": "KG"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_quote_tax_rounds_each_night_half_up():
    offer = pricing.quote(build_hotel(SETUP, MONDAY), Settings(), "KG", "BAR", MONDAY, date(2026, 3, 9))
    assert offer.rates == [15000] * 4 + [16500] * 2 + [15000]
    assert offer.tax == 5 * 1763 + 2 * 1939
    assert offer.total == 5 * 15000 + 2 * 16500 + offer.tax


def test_cli_quote_total(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")
    main(["--state", state, "init", str(setup_file), "--business-date", "2026-03-02"])
    capsys.readouterr()
    assert main(["--state", state, "--settings", str(tmp_path / "hotel.json"), "quote", "--type", "KG",
                 "--arrival", "2026-03-02", "--departure", "2026-03-04"]) == 0
    assert "tax 35.26" in capsys.readouterr().out
