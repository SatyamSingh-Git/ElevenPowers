"""Exceptions raised across the package."""


class GreenhouseError(Exception):
    """Base class for errors the command line reports without a traceback."""


class ConfigError(GreenhouseError):
    """A settings, layout, thresholds or calibration file is missing or malformed."""


class ValidationError(GreenhouseError):
    """A reading, offset or argument fails a check."""
