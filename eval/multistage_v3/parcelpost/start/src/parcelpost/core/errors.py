"""Errors the command line reports as a one-line message rather than a traceback."""


class ParcelpostError(Exception):
    pass


class ValidationError(ParcelpostError):
    """An order, parcel or address the carrier would not accept."""


class RatingError(ParcelpostError):
    """No price exists for the service or destination asked for."""


class ConfigError(ParcelpostError):
    pass


class StoreError(ParcelpostError):
    pass


class ManifestError(ParcelpostError):
    pass


class ScanError(ParcelpostError):
    """A scan file that cannot be recorded. Nothing from the file is recorded."""


class UnknownShipment(ParcelpostError):
    def __init__(self, number):
        super().__init__(f"no shipment {number}")
        self.number = number
