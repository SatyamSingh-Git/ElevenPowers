"""Clinic settings: the `settings` block of the clinic file.

Every setting has a default, so a clinic file only lists what it changes.
"""
from dataclasses import asdict, dataclass, fields, replace
from decimal import Decimal, InvalidOperation

from .errors import ConfigError

CURRENCY_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}
PENNY = Decimal("0.01")
SHORTEST_SLOT = 5


@dataclass(frozen=True)
class Settings:
    slot_minutes: int = 20
    no_show_fee: Decimal = Decimal("25.00")
    reminder_lead_hours: int = 24
    booking_horizon_days: int = 60
    currency: str = "GBP"

    @property
    def currency_symbol(self):
        return CURRENCY_SYMBOLS[self.currency]

    def money(self, amount):
        return f"{self.currency_symbol}{amount:.2f}"


def _convert(name, value, default):
    if isinstance(default, int):
        # JSON true and false are ints to Python; a count of minutes is never one.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"setting {name} must be a whole number")
        if value < 0:
            raise ConfigError(f"setting {name} cannot be negative")
        return value
    if isinstance(default, Decimal):
        if isinstance(value, bool):
            raise ConfigError(f"setting {name} must be an amount like 25.00")
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ConfigError(f"setting {name} must be an amount like 25.00") from None
        if amount < 0:
            raise ConfigError(f"setting {name} cannot be negative")
        return amount.quantize(PENNY)
    if not isinstance(value, str):
        raise ConfigError(f"setting {name} must be text")
    return value


def settings_from_dict(raw):
    """Settings from the clinic file's `settings` block, checked and filled in with defaults."""
    if not isinstance(raw, dict):
        raise ConfigError("settings must be an object")
    defaults = Settings()
    known = {field.name for field in fields(Settings)}
    values = {}
    for name, value in raw.items():
        if name not in known:
            raise ConfigError(f"unknown setting: {name}")
        values[name] = _convert(name, value, getattr(defaults, name))
    settings = replace(defaults, **values)
    if settings.slot_minutes < SHORTEST_SLOT:
        raise ConfigError(f"setting slot_minutes must be at least {SHORTEST_SLOT}")
    if settings.currency not in CURRENCY_SYMBOLS:
        raise ConfigError(f"unsupported currency: {settings.currency}")
    return settings


def settings_to_dict(settings):
    """The settings as the clinic file would spell them, amounts as text."""
    return {name: str(value) if isinstance(value, Decimal) else value
            for name, value in asdict(settings).items()}
