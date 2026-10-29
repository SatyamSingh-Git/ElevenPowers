"""Errors the desk reports to the person at the counter.

Every message is written to be shown as it is; the CLI prints it after `error: `.
"""


class HotelError(Exception):
    pass


class NotFound(HotelError):
    pass


class ValidationError(HotelError):
    pass


class Unavailable(HotelError):
    pass


class RoomNotReady(HotelError):
    pass


class InvalidState(HotelError):
    pass


class BalanceDue(HotelError):
    pass
