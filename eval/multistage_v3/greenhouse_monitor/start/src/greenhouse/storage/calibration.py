"""Per-sensor calibration offsets, kept in ``calibration.json``.

    {"GH1-T01": 0.5, "GH2-S01": -1.2}

An offset is added after a reading is converted to its kind's canonical unit,
so it is always in canonical units. Sensors without an entry read as-is.
"""
import json
from pathlib import Path

from ..config.jsonfile import number, read_json
from ..core.errors import ValidationError


class CalibrationStore:
    def __init__(self, path, offsets=None):
        self.path = Path(path)
        self._offsets = dict(offsets or {})

    def offset_for(self, sensor):
        return self._offsets.get(sensor, 0.0)

    def set_offset(self, sensor, offset, limit):
        """Set a sensor's offset; ``limit`` is the largest offset a site accepts."""
        if offset > limit:
            raise ValidationError(f"offset too large: {offset}")
        self._offsets[sensor] = offset

    def clear(self, sensor):
        """Forget a sensor's offset; False if it had none."""
        return self._offsets.pop(sensor, None) is not None

    def items(self):
        return sorted(self._offsets.items())

    def save(self):
        text = json.dumps(dict(self.items()), indent=2)
        self.path.write_text(text + "\n", encoding="utf-8")


def load_calibration(path):
    path = Path(path)
    if not path.exists():
        return CalibrationStore(path)
    offsets = {
        sensor: number(offset, f"offset for {sensor}")
        for sensor, offset in read_json(path).items()
    }
    return CalibrationStore(path, offsets)
