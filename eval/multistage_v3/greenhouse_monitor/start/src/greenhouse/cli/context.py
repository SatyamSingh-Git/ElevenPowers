"""What every command handler is given besides its parsed arguments."""
from dataclasses import dataclass
from typing import TextIO

from ..config.layout import load_layout
from ..config.settings import load_settings
from ..core.clock import Clock, parse_day
from ..storage.paths import DataDir


@dataclass
class Context:
    data: DataDir
    clock: Clock
    out: TextIO

    def settings(self):
        return load_settings(self.data.settings)

    def layout(self):
        return load_layout(self.data.layout)

    def day(self, text):
        """The ``--date`` given, or today."""
        return parse_day(text) if text else self.clock.now().date()

    def say(self, text):
        print(text, file=self.out)
