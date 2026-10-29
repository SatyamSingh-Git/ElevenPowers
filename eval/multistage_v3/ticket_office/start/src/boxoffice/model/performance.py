"""A performance: one showing of a production, with a price for each tier."""
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..clock import format_time, parse_time
from ..errors import BoxOfficeError

CODE = re.compile(r"[A-Z0-9][A-Z0-9-]{1,19}")


@dataclass
class Performance:
    code: str
    title: str
    starts: datetime
    prices: dict = field(default_factory=dict)
    cancelled: bool = False

    def has_started(self, now):
        return now >= self.starts

    def to_dict(self):
        return {"code": self.code, "title": self.title, "starts": format_time(self.starts),
                "prices": dict(sorted(self.prices.items())), "cancelled": self.cancelled}

    @classmethod
    def from_dict(cls, data):
        return cls(data["code"], data["title"], parse_time(data["starts"]), dict(data["prices"]),
                   data["cancelled"])


def check_code(code):
    if not CODE.fullmatch(code):
        raise BoxOfficeError("bad-performance-code", code=code)
    return code
