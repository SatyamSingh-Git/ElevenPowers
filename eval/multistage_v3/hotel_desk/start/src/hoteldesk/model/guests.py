"""Guest profiles, kept by name so repeat guests are recognised at booking."""
from dataclasses import dataclass


@dataclass
class Guest:
    name: str
    email: str = ""
    phone: str = ""
    vip: bool = False
    notes: str = ""
