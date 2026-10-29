"""A member's request for the next available copy of a title."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

WAITING = 'waiting'
READY = 'ready'


@dataclass
class Hold:
    title_id: str
    card: str
    placed: date
    status: str = WAITING
    barcode: Optional[str] = None
    ready_on: Optional[date] = None
