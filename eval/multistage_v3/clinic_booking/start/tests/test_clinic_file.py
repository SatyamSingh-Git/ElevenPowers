import copy
import json

import pytest

from clinicbook.errors import ConfigError
from clinicbook.storage.clinic_file import add_closure, load_clinic, parse_clinic
from conftest import CLINIC, MONDAY


def test_loads_rooms_practitioners_and_settings(clinic_file):
    clinic = load_clinic(clinic_file)
    assert [room.id for room in clinic.rooms] == ["R1", "R2", "R3"]
    assert clinic.practitioner("ben").days == ("mon", "wed", "fri")
    assert clinic.settings.slot_minutes == 20


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="no clinic file"):
        load_clinic(tmp_path / "nowhere.json")


def test_practitioner_in_unknown_room():
    raw = copy.deepcopy(CLINIC)
    raw["practitioners"][0]["room"] = "R9"
    with pytest.raises(ConfigError, match="amy works in unknown room R9"):
        parse_clinic(raw)


def test_two_practitioners_cannot_share_a_room_on_the_same_day():
    raw = copy.deepcopy(CLINIC)
    raw["practitioners"][2]["room"] = "R1"
    with pytest.raises(ConfigError, match="amy and cara both use room R1 on tue"):
        parse_clinic(raw)


def test_add_closure_keeps_the_file_loadable(clinic_file):
    assert add_closure(clinic_file, MONDAY) is True
    assert add_closure(clinic_file, MONDAY) is False
    assert load_clinic(clinic_file).hours.window(MONDAY) is None
    assert json.loads(clinic_file.read_text(encoding="utf-8"))["closures"] == ["2026-03-02", "2026-03-20"]
