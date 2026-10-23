class UnitError(ValueError):
    """Base class for every error unitconv reports to the user."""


class UnknownUnitError(UnitError):
    def __init__(self, symbol):
        super().__init__(f"unknown unit: '{symbol}'")
        self.symbol = symbol


class IncompatibleUnitsError(UnitError):
    pass


class ParseError(UnitError):
    pass


class SettingsError(UnitError):
    pass
