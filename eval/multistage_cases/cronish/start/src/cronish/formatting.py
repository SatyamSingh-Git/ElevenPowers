"""Text helpers shared by the describer and the command line."""
from ._generated import DAY_NAMES


def join_words(words):
    """``["a", "b", "c"]`` -> ``"a, b and c"``."""
    words = list(words)
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " and " + words[-1]


def clock(hour, minute):
    return f"{hour:02d}:{minute:02d}"


def format_run(moment):
    # Weekday names come from the generated table so output does not depend on the locale.
    weekday = DAY_NAMES[moment.isoweekday() % 7].title()
    return f"{moment:%Y-%m-%d} {clock(moment.hour, moment.minute)} {weekday}"
