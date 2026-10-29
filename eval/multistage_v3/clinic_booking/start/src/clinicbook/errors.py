"""Errors a user can act on. The command line prints any of them as `error: <message>`."""


class ClinicError(Exception):
    """Base class for every error clinicbook raises on purpose."""


class ConfigError(ClinicError):
    """The clinic file is missing, malformed or inconsistent."""


class StorageError(ClinicError):
    """A bookings, charges or outbox file cannot be read."""


class NotFound(ClinicError):
    """A practitioner, room or booking that does not exist."""


class BookingError(ClinicError):
    """A booking request that breaks a rule: opening hours, clashes, limits."""


class ValidationError(BookingError):
    """Patient details that cannot be accepted."""
