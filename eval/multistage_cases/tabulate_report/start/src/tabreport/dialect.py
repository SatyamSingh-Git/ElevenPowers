"""How a CSV file is laid out: separators, quoting and encoding."""
from dataclasses import dataclass

from .errors import ReportError


@dataclass(frozen=True)
class Dialect:
    delimiter: str = ","
    quotechar: str = '"'
    encoding: str = "utf-8"
    skip_blank: bool = True

    def __post_init__(self):
        for name in ("delimiter", "quotechar"):
            value = getattr(self, name)
            if len(value) != 1:
                raise ReportError(f"{name} must be one character, got {value!r}")
        if self.delimiter == self.quotechar:
            raise ReportError("delimiter and quotechar must differ")


NAMED = {
    "comma": Dialect(),
    "semicolon": Dialect(delimiter=";"),
    "tab": Dialect(delimiter="\t"),
    "pipe": Dialect(delimiter="|"),
}


def named(name):
    try:
        return NAMED[name.lower()]
    except KeyError:
        raise ReportError(f"unknown dialect: {name}") from None


def unescape(text):
    """A delimiter typed on a command line: shells make a literal tab awkward, so accept \\t."""
    return "\t" if text in ("\\t", "tab") else text
