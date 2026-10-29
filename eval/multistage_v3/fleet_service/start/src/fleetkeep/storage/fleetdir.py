"""A fleet directory: fleet.ini plus one file per kind of record."""
from pathlib import Path

from ..config import Settings, load_settings, write_settings
from ..errors import FleetError
from ..services.fleet import Fleet
from . import csvfiles, jsonfiles

SETTINGS_FILE = "fleet.ini"
VEHICLES_FILE = "vehicles.json"
ORDERS_FILE = "workorders.json"
READINGS_FILE = "odometer.csv"
FUEL_FILE = "fuel.csv"
HISTORY_FILE = "history.csv"
PARTS_FILE = "parts.json"
CARDS_FILE = "cards.csv"
DEFECTS_FILE = "defects.json"
TREADS_FILE = "tread.csv"


class FleetDirectory:
    def __init__(self, path):
        self.path = Path(path)

    def _file(self, name):
        return self.path / name

    def exists(self):
        return self._file(SETTINGS_FILE).is_file()

    def create(self, name):
        if self.exists():
            raise FleetError("E154", path=str(self.path))
        self.path.mkdir(parents=True, exist_ok=True)
        write_settings(self._file(SETTINGS_FILE), Settings(name=name))
        self.save(Fleet(Settings(name=name)))

    def load(self):
        if not self.exists():
            raise FleetError("E153", path=str(self.path))
        return Fleet.restore(
            load_settings(self._file(SETTINGS_FILE)),
            vehicles=[jsonfiles.vehicle_from_dict(d)
                      for d in jsonfiles.read_documents(self._file(VEHICLES_FILE))],
            readings=csvfiles.read_readings(self._file(READINGS_FILE)),
            fuel=csvfiles.read_fuel(self._file(FUEL_FILE)),
            orders=[jsonfiles.order_from_dict(d)
                    for d in jsonfiles.read_documents(self._file(ORDERS_FILE))],
            history=csvfiles.read_history(self._file(HISTORY_FILE)),
            stock=[jsonfiles.stock_from_dict(d)
                   for d in jsonfiles.read_documents(self._file(PARTS_FILE))],
            cards=csvfiles.read_cards(self._file(CARDS_FILE)),
            defects=[jsonfiles.defect_from_dict(d)
                     for d in jsonfiles.read_documents(self._file(DEFECTS_FILE))],
            treads=csvfiles.read_treads(self._file(TREADS_FILE)),
        )

    def save(self, fleet):
        jsonfiles.write_documents(self._file(VEHICLES_FILE),
                                  [jsonfiles.vehicle_to_dict(v) for v in fleet.vehicles()])
        jsonfiles.write_documents(self._file(ORDERS_FILE),
                                  [jsonfiles.order_to_dict(o) for o in fleet.orders()])
        csvfiles.write_readings(self._file(READINGS_FILE), fleet.readings())
        csvfiles.write_fuel(self._file(FUEL_FILE), fleet.fuel())
        csvfiles.write_history(self._file(HISTORY_FILE), fleet.history())
        jsonfiles.write_documents(self._file(PARTS_FILE),
                                  [jsonfiles.stock_to_dict(i) for i in fleet.stock()])
        csvfiles.write_cards(self._file(CARDS_FILE), fleet.cards())
        jsonfiles.write_documents(self._file(DEFECTS_FILE),
                                  [jsonfiles.defect_to_dict(d) for d in fleet.defects()])
        csvfiles.write_treads(self._file(TREADS_FILE), fleet.treads())
