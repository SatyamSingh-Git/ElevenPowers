import csv
import json

from clinicbook.cli.main import main

CLINIC = {
    "name": "Riverside Physio",
    "rooms": [{"id": "R1", "name": "Room 1"}],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00",
              "fri": "09:00-17:00", "sat": None, "sun": None},
}


def cli(folder, *argv, now="2026-02-27T08:00"):
    return main(["--clinic", str(folder / "clinic.json"), "--bookings", str(folder / "bookings.csv"),
                 "--now", now, *argv])


def test_fees_command_writes_pence(tmp_path):
    (tmp_path / "clinic.json").write_text(json.dumps(dict(CLINIC, settings={"no_show_fee": 30})), encoding="utf-8")
    for day in ("2026-03-02", "2026-03-03", "2026-03-04"):
        assert cli(tmp_path, "book", "amy", day, "10:40", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    for reference in ("B0001", "B0002", "B0003"):
        assert cli(tmp_path, "no-show", reference, now="2026-03-04T18:00") == 0
    target = tmp_path / "out.csv"
    assert cli(tmp_path, "fees", "--out", str(target)) == 0
    with open(target, newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["amount_pence"] != "0"]
    assert len(rows) >= 2
    assert {row["amount_pence"] for row in rows} == {"3000"}
    assert {row["phone"] for row in rows} == {"07700900001"}
